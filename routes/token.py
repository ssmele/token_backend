from flask import Blueprint
from routes import load_with_schema
from models.token import TokenRequest
from utils.utils import success_response

token = Blueprint('token', __name__)
url_prefix = '/token'


@token.route(url_prefix, methods=['POST'])
@load_with_schema(TokenRequest)
def tokens(data):
    return success_response()