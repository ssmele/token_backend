from flask import Blueprint
from routes import load_with_schema
from models.contract import ContractRequest
from utils.utils import success_response

contract = Blueprint('contract', __name__)
url_prefix = '/contract'


@contract.route(url_prefix, methods=['POST'])
@load_with_schema(ContractRequest)
def contracts(data):
    return success_response(data)