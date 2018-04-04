from flask import Blueprint
from routes import load_with_schema
from models.claim import ClaimRequest
from utils.utils import success_response

claim = Blueprint('claim', __name__)
url_prefix = '/claim'


@claim.route(url_prefix, methods=['POST'])
@load_with_schema(ClaimRequest)
def claims(data):
    return success_response(data)