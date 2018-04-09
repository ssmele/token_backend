from flask import Blueprint
from routes import load_with_schema
from models.claim import ClaimRequest
from utils.utils import success_response
from utils.doc_utils import BlueprintDocumentation

claim_bp = Blueprint('claim', __name__)
claim_docs = BlueprintDocumentation(claim_bp, 'Claim')
url_prefix = '/claim'


@claim_bp.route(url_prefix, methods=['POST'])
@load_with_schema(ClaimRequest)
def claims(data):
    return success_response(data)