from flask import Blueprint, g
from flask_restful import Resource, Api
from routes import load_with_schema
from models.issuer import CreateIssuerRequest, GetIssuerByIID, GetIssuerByUsername, create_issuer
from utils.utils import success_response, error_response
from utils.doc_utils import BlueprintDocumentation
from utils.verify_utils import verify_issuer_jwt, generate_jwt

issuer_bp = Blueprint('issuer', __name__)
issuer_docs = BlueprintDocumentation(issuer_bp, 'Issuer')
url_prefix = '/issuer'


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


class Issuer(Resource):

    @load_with_schema(CreateIssuerRequest)
    @issuer_docs.document(url_prefix+" ", 'POST', 'Method to create issuer. Returns jwt.', CreateIssuerRequest)
    def post(self, data):
        try:
            # TODO: Need to create Ethereum account here.
            issuer = create_issuer(data)
            return success_response({'jwt': generate_jwt(issuer)}, http_code=201)
        except Exception:
            return error_response("Couldn't create issuer", http_code=200)

    @verify_issuer_jwt
    @issuer_docs.document(url_prefix, 'GET',
                          "Method to retrieve issuer information. Requires jwt from login/creation account.")
    def get(self):
        issuer = GetIssuerByIID().execute_n_fetchone({'i_id': g.issuer_info['i_id']})
        if issuer:
            return success_response(issuer)
        else:
            return error_response(status="Couldn't retrieve issuer info.", status_code=-1, http_code=200)


issuer_api = Api(issuer_bp)
issuer_api.add_resource(Issuer, url_prefix)