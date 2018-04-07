from flask import Blueprint
from routes import load_with_schema
from models.contract import ContractRequest, ClaimTypes, insert_bulk_tokens
from utils.utils import success_response, error_response
from utils.doc_utils import BlueprintDocumentation

contract_bp = Blueprint('contract', __name__)
contract_docs = BlueprintDocumentation(contract_bp, 'Contract')
url_prefix = '/contract'

MAX_TOKEN_LIMIT = 1000


@contract_bp.route(url_prefix, methods=['POST'])
@load_with_schema(ContractRequest)
@contract_docs.document(url_prefix, 'POST',
                        'Method to start a request to issue a new token on the eth network. This will also create all'
                        'new tokens associated with the method.', ContractRequest)
def contracts(data):
    # TODO: Actually issue a deployment for the contract here
    # I don't know how the api for the ether network works just gonna assume if we get None something went wrong.
    contract = 'NOT NULL'
    if contract is None:
        return error_response('Something went wrong creating issuing token contract.')

    # TODO: Move this to marshmallow possibly.
    if data['num_created'] > MAX_TOKEN_LIMIT:
        return error_response("Could not create a token contract with that many individual token. Max is {}"
                              .format(MAX_TOKEN_LIMIT))

    # Update the original data given after validation for contract creation binds.
    data.update({'hash': 'TEMP_CONTRACT_HASH'})
    data.update({'claim_type':  ClaimTypes.SIMPLE.value})

    # Try and insert into database.
    try:
        insert_bulk_tokens(data['num_created'], data)
    except Exception as e:
        print(str(e))
        return error_response("Couldn't create new contract.")

    return success_response('Success in issuing token!', http_code=201)
