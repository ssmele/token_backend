from flask import Blueprint
from routes import load_with_schema
from models.issuer import CreateIssuerRequest, InsertNewIssuer, GetIssuerByIID, GetIssuerByUsername
from utils.utils import success_response, error_response
from utils.doc_utils import BlueprintDocumentation

issuer_bp = Blueprint('issuer', __name__)
issuer_docs = BlueprintDocumentation(issuer_bp, 'Issuer')
url_prefix = '/issuer'


@issuer_bp.route(url_prefix, methods=['POST'])
@load_with_schema(CreateIssuerRequest)
@issuer_docs.document(url_prefix, 'POST', 'Method to create issuer.', CreateIssuerRequest)
def issuers(data):
    try:
        # TODO: Need to create Ethereum account here.
        # TODO: Need to encrypt password and thangs.
        InsertNewIssuer().execute(data)
        return success_response('Created issuer!', http_code=201)
    except Exception:
        return error_response("Couldn't create issuer", http_code=200)


@issuer_bp.route(url_prefix + '/username=<string:username>', methods=['GET'])
@issuer_docs.document(url_prefix + '/username=<string:username>', 'GET', 'Gets issuer information by username')
def get_issuer_by_username(username):
    """
    This method retrieves issuer data for the given username.
    :param username: username of issuer to retrieve.
    :return:
    """
    issuer = GetIssuerByUsername().execute_n_fetchone({'username': username})
    if issuer:
        return success_response(issuer)
    else:
        return error_response(status="Couldn't retrieve issuer with that username", status_code=-1, http_code=200)


@issuer_bp.route(url_prefix + '/i_id=<int:i_id>', methods=['GET'])
@issuer_docs.document(url_prefix + '/i_id=<int:i_id>', 'GET', 'Gets issuer information by i_id')
def get_issuer_by_i_id(i_id):
    """
    This method retrieves issuer data for the given i_id.
    :param i_id: i_id of issuer to retrieve.
    :return:
    """
    issuer = GetIssuerByIID().execute_n_fetchone({'i_id': i_id})
    if issuer:
        return success_response(issuer)
    else:
        return error_response(status="Couldn't retrieve issuer with that i_id", status_code=-1, http_code=200)