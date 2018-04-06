from flask import Blueprint
from routes import load_with_schema
from models.collector import LoginCollectorRequest, GetCollectorLoginDetails
from models.issuer import LoginIssuerRequest, GetIssuerLoginDetails
from utils.utils import success_response, error_response

login_bp = Blueprint('login', __name__)
url_prefix = '/login'

TEMP_JWT = 'SECRET_AND_SEUCRE_420'


@login_bp.route(url_prefix + '/collector', methods=['POST'])
@load_with_schema(LoginCollectorRequest)
def get_collector_jwt(data):
    # Gather up login details.
    login_deets = GetCollectorLoginDetails().execute_n_fetchone(binds=data)
    if login_deets is None:
        return error_response("Authorization Failed for Collector Login.")

    # If we got some deets back then check if passwords match.
    if data['password'] == login_deets['password']:
        return success_response({'jwt': TEMP_JWT})
    else:
        return error_response("Authorization Failed for Collector Login.")


@login_bp.route(url_prefix + '/issuer', methods=['POST'])
@load_with_schema(LoginIssuerRequest)
def get_issuer_jwt(data):
    # Gather up login details.
    login_deets = GetIssuerLoginDetails().execute_n_fetchone(binds=data)
    if login_deets is None:
        return error_response("Authorization Failed for Issuer Login.")

    # If we got some deets back then check if passwords match.
    if data['password'] == login_deets['password']:
        return success_response({'jwt': TEMP_JWT})
    else:
        return error_response("Authorization Failed for Issuer Login.")
