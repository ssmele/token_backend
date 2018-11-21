from flask import Blueprint

from models.collector import LoginCollectorRequest, GetCollectorLoginDetails
from models.issuer import LoginIssuerRequest, GetIssuerLoginDetails
from routes import load_with_schema
from utils.db_utils import requires_db
from utils.doc_utils import BlueprintDocumentation
from utils.utils import success_response, error_response, log_kv, LOG_WARNING, LOG_DEBUG, LOG_INFO
from utils.verify_utils import generate_jwt

login_bp = Blueprint('login', __name__)
login_docs = BlueprintDocumentation(login_bp, 'Login')
url_prefix = '/login'


@login_bp.route(url_prefix + '/collector', methods=['POST'])
@load_with_schema(LoginCollectorRequest)
@requires_db
@login_docs.document(url_prefix + '/collector', 'POST',
                     """
                     This method verifies collector creds and generates a JWT if successful verification takes place.
                     """, input_schema=LoginCollectorRequest, error_codes={'420': 'Failed authorization.'})
def get_collector_jwt(data):
    # Gather up login details.
    login_deets = GetCollectorLoginDetails().execute_n_fetchone(binds=data, close_connection=True)
    if login_deets is None:
        log_kv(LOG_WARNING, {'warning': 'could not find login details for user', 'username': data['username']})
        return error_response("Authorization Failed for Collector Login.", status_code=420)

    # If we got some deets back then check if passwords match.
    if data['password'] == login_deets['password']:
        del login_deets['password']
        log_kv(LOG_DEBUG, {'debug': 'successfully logged in user', 'username': data['username']})
        return success_response({'jwt': generate_jwt(login_deets)})
    else:
        log_kv(LOG_INFO, {'message': 'authorization failed for collecter', 'username': data['username']})
        return error_response("Authorization Failed for Collector Login.")


@login_bp.route(url_prefix + '/issuer', methods=['POST'])
@load_with_schema(LoginIssuerRequest)
@requires_db
@login_docs.document(url_prefix + '/issuer', 'POST',
                     """
                     This method verifies issuer creds and generates a JWT if successful verification takes place.
                     """, input_schema=LoginIssuerRequest, error_codes={'420': 'Failed authorization.'})
def get_issuer_jwt(data):
    # Gather up login details.
    login_deets = GetIssuerLoginDetails().execute_n_fetchone(binds=data, close_connection=True)
    if login_deets is None:
        log_kv(LOG_WARNING, {'warning': 'could not find login details for issuer', 'username': data['username']})
        return error_response("Authorization Failed for Issuer Login.")

    # If we got some deets back then check if passwords match.
    if data['password'] == login_deets['password']:
        del login_deets['password']
        log_kv(LOG_DEBUG, {'debug': 'successfully logged in issuer', 'username': data['username']})
        return success_response({'jwt': generate_jwt(login_deets)})
    else:
        log_kv(LOG_INFO, {'message': 'authorization failed for issuer', 'username': data['username']})
        return error_response("Authorization Failed for Issuer Login.")
