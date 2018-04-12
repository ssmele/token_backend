from flask import Blueprint, g, request
from flask_restful import Api, Resource
from models.contract import ContractRequest, ClaimTypes, GetContractByConID, \
    GetContractByName, insert_bulk_tokens, GetContractsByIssuerID
from utils.utils import success_response, error_response
from utils.doc_utils import BlueprintDocumentation
from utils.verify_utils import verify_issuer_jwt
from utils.image_utils import save_file, serve_file, ImageFolders
from json import loads

contract_bp = Blueprint('contract', __name__)
contract_docs = BlueprintDocumentation(contract_bp, 'Contract')
url_prefix = '/contract'

MAX_TOKEN_LIMIT = 1000


class Contract(Resource):

    @verify_issuer_jwt
    @contract_docs.document(url_prefix+" ", 'POST',
                            'Method to start a request to issue a new token on the eth network.'
                            ' This will also create all new tokens associated with the method.', ContractRequest)
    def post(self):
        """
        Method to use for post requests to the /contract method.
        :param data:
        :return:
        """
        json_data = loads(request.form.get('json_data'))
        data = ContractRequest().load(json_data)
        if data['num_created'] > MAX_TOKEN_LIMIT:
            return error_response("Could not create a token contract with that many individual token. Max is {}"
                                  .format(MAX_TOKEN_LIMIT))

        # TODO: ISSUE THE ACTUAL CONTRACT HERE.

        # Update the original data given after validation for contract creation binds.
        data.update({'hash': 'TEMP_CONTRACT_HASH',
                     'claim_type': ClaimTypes.SIMPLE.value,
                     'i_id': g.issuer_info['i_id']})

        # If we have an image save it.
        file_location = None
        if 'token_image' in request.files:
            file = request.files['token_image']
            file_location = save_file(file,  'CONTRACTS', g.issuer_info['i_id'])

        if file_location is None:
            file_location = 'default.png'

        data.update({'pic_location': file_location})

        # Try and insert into database.
        try:
            insert_bulk_tokens(data['num_created'], data)
        except Exception as e:
            print(str(e))
            return error_response("Couldn't create new contract.")

        return success_response('Success in issuing token!', http_code=201)

    @contract_docs.document(url_prefix, 'GET',
                            'Method to get all contracts deployed by the issuer verified in the jwt.')
    @verify_issuer_jwt
    def get(self):
        """
        Method to use for get requests to the /contract method.
        :return:
        """
        contracts = GetContractsByIssuerID().execute_n_fetchall({'i_id': g.issuer_info['i_id']})
        if contracts:
            return success_response({'contracts': contracts})
        else:
            return error_response(status="Couldn't retrieve contract with that con_id", status_code=-1, http_code=200)


contract_api = Api(contract_bp)
contract_api.add_resource(Contract, url_prefix)


@contract_bp.route(url_prefix + '/image=<string:image>')
def server_image(image):
    return serve_file(image, ImageFolders.CONTRACTS.value)


@contract_bp.route(url_prefix + '/con_id=<int:con_id>', methods=['GET'])
@verify_issuer_jwt
@contract_docs.document(url_prefix + '/con_id=<int:con_id>', 'GET',
                        "Method to retrieve contract information by con_id. Requires issuer verification.")
def get_contract_by_con_id(con_id):
    contract = GetContractByConID().execute_n_fetchone({'con_id': con_id})
    if contract:
        return success_response(contract)
    else:
        return error_response(status="Couldn't retrieve contract with that con_id", status_code=-1, http_code=200)


@contract_bp.route(url_prefix + '/name=<string:name>', methods=['GET'])
@verify_issuer_jwt
@contract_docs.document(url_prefix + '/name=<string:name>', 'GET',
                        "Method to retrieve contract information by names like it.")
def get_contract_by_name(name):
    contracts_by_name = GetContractByName().execute_n_fetchall({'name': '%'+name+'%'})
    if contracts_by_name is not None:
        return success_response({'contracts': contracts_by_name})
    else:
        return error_response(status="Couldn't retrieve contract with that con_id", status_code=-1, http_code=200)
