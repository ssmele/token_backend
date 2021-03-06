from flask import Blueprint, g
from flask_restful import Resource, Api

from ether.geth_keeper import GethException
from models.issuer import CreateIssuerRequest, GetIssuerByIID, GetIssuerByUsername, create_issuer
from routes import load_with_schema, requires_geth
from utils.db_utils import requires_db
from utils.doc_utils import BlueprintDocumentation
from utils.utils import success_response, error_response, log_kv, LOG_INFO, LOG_ERROR, LOG_WARNING
from utils.verify_utils import verify_issuer_jwt, generate_jwt

issuer_bp = Blueprint('issuer', __name__)
issuer_docs = BlueprintDocumentation(issuer_bp, 'Issuer')
url_prefix = '/issuer'


@issuer_bp.route(url_prefix + '/username=<string:username>', methods=['GET'])
@requires_db
@issuer_docs.document(url_prefix + '/username=<string:username>', 'GET',
                      """
                      Gets issuer information by username
                      """)
def get_issuer_by_username(username):
    """
    This method retrieves issuer data for the given username.
    :param username: username of issuer to retrieve.
    :return:
    """
    issuer = GetIssuerByUsername().execute_n_fetchone({'username': username}, close_connection=True)
    if issuer:
        log_kv(LOG_INFO, {'message': 'Successfully found issuer', 'issuer_username': username})
        return success_response(issuer)
    else:
        log_kv(LOG_WARNING, {'warning': 'Could not find account', 'issuer_username': username})
        return error_response(status="Couldn't retrieve issuer with that username", status_code=-1, http_code=200)


class Issuer(Resource):

    @load_with_schema(CreateIssuerRequest)
    @requires_db
    @requires_geth
    @issuer_docs.document(url_prefix, 'POST',
                          """
                          Method to create issuer. Returns jwt.
                          """, CreateIssuerRequest)
    def post(self, data):
        try:
            data['i_hash'], data['i_priv_key'] = g.geth.create_account()
            
            issuer = create_issuer(data)
            g.sesh.commit()
            log_kv(LOG_INFO, {'message': 'successfully created issuer account'})
            return success_response({'jwt': generate_jwt(issuer)}, http_code=201)
        except GethException as ge:
            g.sesh.rollback()
            log_kv(LOG_ERROR, {'error': 'raised exception from geth_keeper while creating issuer account',
                               'exception': ge.exception, 'exc_message': ge.message})
            return error_response(ge.message)
        except Exception as err:
            g.sesh.rollback()
            log_kv(LOG_ERROR, {'error': 'an exception occurred while creating issuer account',
                               'exception': str(err)})
            return error_response("Couldn't create issuer", http_code=200)

    @verify_issuer_jwt
    @requires_db
    @requires_geth
    @issuer_docs.document(url_prefix, 'GET',
                          """
                          Method to retrieve issuer information. Requires jwt from login/creation account.
                          """, req_i_jwt=True)
    def get(self):
        issuer = GetIssuerByIID().execute_n_fetchone({'i_id': g.issuer_info['i_id']}, close_connection=True)

        if issuer:
            # Try and get out the eth balance.
            try:
                balance = g.geth.get_eth_balance(issuer['i_hash'])
            except GethException as e:
                log_kv(LOG_ERROR, {'error': "Couldnt retrieve eth balance", 'i_id': g.issuer_info['i_id'],
                                   'exception': e.exception, 'geth_message': e.message}, exception=True)
                balance = 'Not available at this time.'

            issuer.update({'eth_balance': balance})
            return success_response(issuer)
        else:
            log_kv(LOG_WARNING, {'warning': 'could not find issuer account', 'issuer_id': g.issuer_info['i_id']})
            return error_response(status="Couldn't retrieve issuer info.", status_code=-1, http_code=200)


issuer_api = Api(issuer_bp)
issuer_api.add_resource(Issuer, url_prefix)
