from flask import Blueprint
from routes import load_with_schema
from models.issuer import CreateIssuerRequest
from utils.utils import success_response

issuer = Blueprint('issuer', __name__)
url_prefix = '/issuer'


@issuer.route(url_prefix, methods=['POST'])
@load_with_schema(CreateIssuerRequest)
def issuers(data):
    return success_response(data)