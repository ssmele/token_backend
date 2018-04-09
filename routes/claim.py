from flask import Blueprint, g
from routes import load_with_schema
from models.claim import ClaimRequest, claim_token_for_user
from utils.utils import success_response, error_response
from utils.doc_utils import BlueprintDocumentation
from utils.verify_utils import verify_collector_jwt

claim_bp = Blueprint('claim', __name__)
claim_docs = BlueprintDocumentation(claim_bp, 'Claim')
url_prefix = '/claim'


@claim_bp.route(url_prefix, methods=['POST'])
@claim_docs.document(url_prefix, 'POST', 'Method to claim a rand', input_schema=ClaimRequest)
@verify_collector_jwt
@load_with_schema(ClaimRequest)
def claims(data):
    results = claim_token_for_user(data['con_id'], g.collector_info['c_id'])
    if results is None:
        return error_response("Couldn't claim token")
    else:
        return success_response("Token has been claimed!")