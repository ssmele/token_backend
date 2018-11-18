from datetime import datetime
from json import dumps

import qrcode
from flask import Blueprint, g, request
from flask_restful import Api, Resource
from marshmallow import ValidationError

from ether.geth_keeper import GethException
from models.constraints import get_all_constraints
from models.contract import ContractRequest, GetContractByConID, GetContractByName, \
    GetContractsByIssuerID, process_constraints, insert_bulk_tokens, GetContractResponse, UpdateQRCODE, GetAllQRCodes
from models.issuer import GetIssuerInfo
from routes import requires_geth
from utils.db_utils import requires_db
from utils.doc_utils import BlueprintDocumentation
from utils.image_utils import save_file, serve_file, save_qrcode, Folders
from utils.utils import success_response, error_response, log_kv, LOG_WARNING, LOG_INFO, LOG_ERROR, LOG_DEBUG
from utils.verify_utils import verify_issuer_jwt, generate_jwt

contract_bp = Blueprint('contract', __name__)
contract_docs = BlueprintDocumentation(contract_bp, 'Contract')
url_prefix = '/contract'

MAX_TOKEN_LIMIT = 1000


class Contract(Resource):

    @verify_issuer_jwt
    @requires_db
    @requires_geth
    @contract_docs.document(url_prefix + " ", 'POST',
                            """
                            Method to start a request to issue a new token on the eth network. This will also create all 
                            new tokens associated with the method. This method requires a multipart form. The two 
                            possible form values are token_image which should be an image, and json_data. The json_data 
                            form should contain a json object matching the method request json fields below.
                            """,
                            error_codes={'89': 'Number of tokens requested to create exceeds limit.',
                                         '45': "Couldn't retrieve issuer specified."},
                            input_schema=ContractRequest, req_i_jwt=True)
    def post(self):
        """ Method to use for post requests to the /contract method.

        :return: HTTP response
        """
        try:
            # Parse out the data from the contract request.
            data = ContractRequest().loads(request.form['json_data'])
        except ValidationError as er:
            return error_response('Validation Failed', errors=er.messages)

        # Check to ensure we are not over the max token limit.
        if data['num_created'] > MAX_TOKEN_LIMIT:
            log_kv(LOG_WARNING, {'warning': 'issuer tried to create contract over limit',
                                 'issuer_id': g.issuer_info['i_id'], 'num_tokens': data['num_created']})
            return error_response("Could not create a token contract with that many individual token. Max is {}"
                                  .format(MAX_TOKEN_LIMIT), status_code=89)

        # Update the original data given after validation for contract creation binds.
        data.update({'i_id': g.issuer_info['i_id']})

        # If we have an image save it.
        file_location = None
        if 'token_image' in request.files:
            file_location = save_file(request.files['token_image'], Folders.CONTRACTS.value,
                                      g.issuer_info['i_id'])

        if file_location is None:
            file_location = 'default.png'
        data.update({'pic_location': file_location})

        metadata_location = 'tmp'  # TODO: save and get the location of the metadata JSON file
        data['metadata_location'] = metadata_location

        try:
            # Get the received constraints in array format for the smart contract
            code_constraints, date_constraints, loc_constraints = self.get_constraints(data)

            # Issue the contract on the ETH network
            issuer = GetIssuerInfo().execute_n_fetchone(binds={'i_id': g.issuer_info['i_id']})
            # Ensure we retrieved an issuer.
            if issuer is None:
                error_response('Failed to retrieve issuer specified.', status_code=45)

            data['con_tx'], data['con_abi'], data['gas_price'] = g.geth.issue_contract(issuer['i_hash'],
                                                                                       issuer_name=issuer['username'],
                                                                                       name=data['name'],
                                                                                       desc=data['description'],
                                                                                       img_url=data['pic_location'],
                                                                                       num_tokes=data['num_created'],
                                                                                       code_reqs=code_constraints,
                                                                                       date_reqs=date_constraints,
                                                                                       loc_reqs=loc_constraints,
                                                                                       tradable=data['tradable'],
                                                                                       metadata_uri=metadata_location)

            # Insert into the database
            con_id, t_ids = insert_bulk_tokens(data['num_created'], data, g.sesh)

            # It is either qr_codes or other contstraints it cannot be both.
            if data['qr_code_claimable']:
                # Get all tokens to associate qr code with.
                for t_id in t_ids:
                    # Generate the data to place in qr code.
                    json_data_dict = dumps({'con_id': con_id, 't_id': t_id,
                                            'jwt': generate_jwt({'con_id': con_id, 't_id': 't_id'})})

                    # Make qr_code and save it.
                    qrc = qrcode.make(json_data_dict)
                    saved_location = save_qrcode(qrc, con_id, t_id)

                    # If we successfully saved the image persist it into database.
                    if saved_location is None:
                        log_kv(LOG_ERROR, {'error': 'failed to make qrcode.'})
                    else:
                        UpdateQRCODE().execute({'qr_code_location': saved_location, 'con_id': con_id, 't_id': t_id})
            elif 'constraints' in data:
                # If constraints were passed in we need to process them.
                process_constraints(data['constraints'], con_id)

            g.sesh.commit()
            log_kv(LOG_INFO, {'message': 'succesfully issued contract!', 'issuer_id': g.issuer_info['i_id']})
            return success_response('Success in issuing token!', http_code=201)
        except GethException as e:
            g.sesh.rollback()
            log_kv(LOG_ERROR, {'error': 'a geth_exception occurred while issuing contract',
                               'issuer_id': g.issuer_info['i_id'], 'exception': e.exception,
                               'exc_message': e.message})
            return error_response(e.message)
        except Exception as e:
            g.sesh.rollback()
            log_kv(LOG_ERROR, {'error': 'an exception occurred while issuing contract',
                               'issuer_id': g.issuer_info['i_id'], 'exception': str(e)})
            return error_response("Couldn't create new contract. Exception {}".format(str(e)))

    @staticmethod
    def get_constraints(data):
        """ Gets the constraints for the contract creation

        :param data: The data received in the contract POST method
        :return: Tuple of (code_constraints, time_constraints, and location_constraints) - all arrays
        """
        code_constraints = []
        date_constraints = []
        loc_constraints = []

        if 'constraints' in data:
            constraints = data['constraints']

            # Check code constraints
            if 'code_constraints' in constraints:
                for cc in constraints['code_constraints']:
                    code_constraints.append(cc['code'])

            # Check date constraints
            if 'time_constraints' in constraints:
                for tc in constraints['time_constraints']:
                    start = int((tc['start'] - datetime(1970, 1, 1)).total_seconds())
                    end = int((tc['end'] - datetime(1970, 1, 1)).total_seconds())
                    date_constraints.append(start)
                    date_constraints.append(end)

            # Check locations constraints
            if 'location_constraints' in constraints:
                for lc in constraints['location_constraints']:
                    loc_constraints.append(int(lc['latitude']))
                    loc_constraints.append(int(lc['longitude']))
                    loc_constraints.append(int(lc['radius']))

        return code_constraints, date_constraints, loc_constraints

    @contract_docs.document(url_prefix, 'GET',
                            """
                            Method to get all contracts deployed by the issuer verified in the jwt.
                            """, req_i_jwt=True)
    @requires_db
    @verify_issuer_jwt
    def get(self):
        """
        Method to use for get requests to the /contract method.
        :return:
        """
        contracts = GetContractsByIssuerID().execute_n_fetchall({'i_id': g.issuer_info['i_id']}, close_connection=True)
        if contracts is not None:
            log_kv(LOG_INFO, {'message': 'succesfully retrieved issuer\'s contracts',
                              'issuer_id': g.issuer_info['i_id']})

            # Add the constraints to the contract object.
            for contract in contracts:
                contract.update({'constraints': get_all_constraints(contract['con_id'])})

            return success_response({'contracts': contracts})
        else:
            log_kv(LOG_WARNING, {'warning': 'could not get contract for issuer', 'issuer_id': g.issuer_info['i_id']})
            return error_response(status="Couldn't retrieve contract with that con_id", status_code=-1, http_code=200)


@contract_bp.route(url_prefix + '/image=<string:image>')
def server_image(image):
    return serve_file(image, Folders.CONTRACTS.value)


@contract_bp.route(url_prefix + '/qr_code=<string:qr_code>')
def serve_qr_code(qr_code):
    return serve_file(qr_code, Folders.QR_CODES.value)


@contract_bp.route(url_prefix + '/metadata=<string:metadata>')
def serve_metadata(metadata):
    return serve_file(metadata, Folders.METADATA.value)


@contract_bp.route(url_prefix + '/qr_code/con_id=<int:con_id>')
@requires_db
@verify_issuer_jwt
@contract_docs.document(url_prefix + 'qr_code/con_id=<int:con_id>', 'GET',
                        """
                        Method to retrieve all the qr_codes associated with a given con_id.
                        """, req_i_jwt=True)
def qr_codes_by_con_id(con_id):
    qr_codes = GetAllQRCodes().execute_n_fetchall({'con_id': con_id})
    return success_response({'qr_codes': [q['qr_code_location'] for q in qr_codes]})


@contract_bp.route(url_prefix + '/con_id=<int:con_id>', methods=['GET'])
@verify_issuer_jwt
@requires_db
@contract_docs.document(url_prefix + '/con_id=<int:con_id>', 'GET',
                        """
                        Method to retrieve contract information by con_id. Constraint info included.
                        """,
                        output_schema=GetContractResponse, req_i_jwt=True)
def get_contract_by_con_id(con_id):
    contract = GetContractByConID().execute_n_fetchone({'con_id': con_id})
    constraints = get_all_constraints(con_id)
    g.sesh.close()
    if contract:
        log_kv(LOG_DEBUG, {'debug': 'successfully retrieved contract', 'contract_id': con_id})
        contract.update({'constraints': constraints})
        return success_response({'contract': contract})
    else:
        log_kv(LOG_WARNING, {'warning': 'could not find contract', 'contract_id': con_id})
        return error_response(status="Couldn't retrieve contract with that con_id", status_code=-1, http_code=200)


@contract_bp.route(url_prefix + '/name=<string:name>', methods=['GET'])
@verify_issuer_jwt
@requires_db
@contract_docs.document(url_prefix + '/name=<string:name>', 'GET',
                        """
                        Method to retrieve contract information by names like it.
                        """, req_i_jwt=True)
def get_contract_by_name(name):
    contracts_by_name = GetContractByName().execute_n_fetchall({'name': '%' + name + '%'}, close_connection=True)
    if contracts_by_name is not None:
        log_kv(LOG_DEBUG, {'debug': 'found contract by name', 'contract_name': name})
        return success_response({'contracts': contracts_by_name})
    else:
        log_kv(LOG_WARNING, {'warning': 'could not find contract by name', 'contract_name': name})
        return error_response(status="Couldn't retrieve contract with that con_id", status_code=-1, http_code=200)


contract_api = Api(contract_bp)
contract_api.add_resource(Contract, url_prefix)
