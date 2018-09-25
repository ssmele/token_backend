from flask import Blueprint, g, request
from flask_restful import Api, Resource

from ether.geth_keeper import GethException
from models.contract import ContractRequest, ClaimTypes, GetContractByConID, \
    GetContractByName, insert_bulk_tokens, GetContractsByIssuerID
from models.issuer import GetIssuerInfo
from routes import requires_geth
from utils.db_utils import requires_db
from utils.doc_utils import BlueprintDocumentation
from utils.image_utils import save_file, serve_file, ImageFolders
from utils.utils import success_response, error_response, log_kv, LOG_WARNING, LOG_INFO, LOG_ERROR, LOG_DEBUG
from utils.verify_utils import verify_issuer_jwt

contract_bp = Blueprint('contract', __name__)
contract_docs = BlueprintDocumentation(contract_bp, 'Contract')
url_prefix = '/contract'

MAX_TOKEN_LIMIT = 1000


class Contract(Resource):

    @verify_issuer_jwt
    @requires_db
    @requires_geth
    @contract_docs.document(url_prefix+" ", 'POST',
                            'Method to start a request to issue a new token on the eth network.'
                            ' This will also create all new tokens associated with the method.', ContractRequest)
    def post(self):
        """ Method to use for post requests to the /contract method.

        :return: HTTP response
        """
        data = ContractRequest().load(request.form)
        if data['num_created'] > MAX_TOKEN_LIMIT:
            log_kv(LOG_WARNING, {'warning': 'issuer tried to create contract over limit',
                                 'issuer_id': g.issuer_info['i_id'], 'num_tokens': data['num_created']})
            return error_response("Could not create a token contract with that many individual token. Max is {}"
                                  .format(MAX_TOKEN_LIMIT))

        # Update the original data given after validation for contract creation binds.
        data.update({'claim_type': ClaimTypes.SIMPLE.value,
                     'i_id': g.issuer_info['i_id']})

        # If we have an image save it.
        file_location = None
        if 'token_image' in request.files:
            file = request.files['token_image']
            file_location = save_file(file,  'CONTRACTS', g.issuer_info['i_id'])

        if file_location is None:
            file_location = 'default.png'
        data.update({'pic_location': file_location})

        try:
            # Issue the contract on the ETH network
            issuer = GetIssuerInfo().execute_n_fetchone(binds={'i_id': g.issuer_info['i_id']})
            data['con_tx'], data['con_abi'] = g.geth.issue_contract(issuer['i_hash'],
                                                                    issuer_name=issuer['username'],
                                                                    name=data['name'],
                                                                    desc=data['description'],
                                                                    img_url=data['pic_location'],
                                                                    num_tokes=data['num_created'])
            # Insert into the database
            insert_bulk_tokens(data['num_created'], data, g.sesh)

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

    @contract_docs.document(url_prefix, 'GET',
                            'Method to get all contracts deployed by the issuer verified in the jwt.')
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
            return success_response({'contracts': contracts})
        else:
            log_kv(LOG_WARNING, {'warning': 'could not get contract for issuer', 'issuer_id': g.issuer_info['i_id']})
            return error_response(status="Couldn't retrieve contract with that con_id", status_code=-1, http_code=200)


contract_api = Api(contract_bp)
contract_api.add_resource(Contract, url_prefix)


@contract_bp.route(url_prefix + '/image=<string:image>')
def server_image(image):
    return serve_file(image, ImageFolders.CONTRACTS.value)


@contract_bp.route(url_prefix + '/con_id=<int:con_id>', methods=['GET'])
@verify_issuer_jwt
@requires_db
@contract_docs.document(url_prefix + '/con_id=<int:con_id>', 'GET',
                        "Method to retrieve contract information by con_id. Requires issuer verification.")
def get_contract_by_con_id(con_id):
    contract = GetContractByConID().execute_n_fetchone({'con_id': con_id}, close_connection=True)
    if contract:
        log_kv(LOG_DEBUG, {'debug': 'successfully retrieved contract', 'contract_id': con_id})
        return success_response(contract)
    else:
        log_kv(LOG_WARNING, {'warning': 'could not find contract', 'contract_id': con_id})
        return error_response(status="Couldn't retrieve contract with that con_id", status_code=-1, http_code=200)


@contract_bp.route(url_prefix + '/name=<string:name>', methods=['GET'])
@verify_issuer_jwt
@requires_db
@contract_docs.document(url_prefix + '/name=<string:name>', 'GET',
                        "Method to retrieve contract information by names like it.")
def get_contract_by_name(name):
    contracts_by_name = GetContractByName().execute_n_fetchall({'name': '%'+name+'%'}, close_connection=True)
    if contracts_by_name is not None:
        log_kv(LOG_DEBUG, {'debug': 'found contract by name', 'contract_name': name})
        return success_response({'contracts': contracts_by_name})
    else:
        log_kv(LOG_WARNING, {'warning': 'could not find contract by name', 'contract_name': name})
        return error_response(status="Couldn't retrieve contract with that con_id", status_code=-1, http_code=200)
