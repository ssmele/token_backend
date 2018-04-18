from flask import Blueprint, g

from ether.geth_keeper import GethException
from routes import load_with_schema, requires_geth
from models.claim import ClaimRequest, DoesCollectorOwnToken, GetTokenInfo, GetAvailableToken, SetToken
from utils.utils import success_response, error_response
from utils.doc_utils import BlueprintDocumentation
from utils.verify_utils import verify_collector_jwt
from models import requires_db

claim_bp = Blueprint('claim', __name__)
claim_docs = BlueprintDocumentation(claim_bp, 'Claim')
url_prefix = '/claim'


@claim_bp.route(url_prefix, methods=['POST'])
@claim_docs.document(url_prefix, 'POST', 'Method to claim a token of of a contract.', input_schema=ClaimRequest)
@verify_collector_jwt
@requires_geth
@load_with_schema(ClaimRequest)
@requires_db
def claims(data):
    results, msg = claim_token_for_user(data['con_id'], g.collector_info['c_id'], g.sesh)
    if results:
        g.sesh.commit()
        return success_response(msg)
    else:
        g.sesh.rollback()
        return error_response(msg)


def claim_token_for_user(con_id, c_id, sesh):
    """ Attempts to claim a token for the given user

    :param con_id: The contract_id of the token
    :param c_id: The collector_id of the collecting user
    :param sesh: The database session to use
    :return: True if the claim request was successful, False if otherwise
    """
    have_token_already = DoesCollectorOwnToken().execute_n_fetchone({'con_id': con_id, 'c_id': c_id},
                                                                    sesh=sesh, schema_out=False)
    if have_token_already:
        return False, 'User already has token'

    try:
        # Make sure a token is available and that it has info
        avail_token = GetAvailableToken().execute_n_fetchone({'con_id': con_id}, sesh=sesh)
        token_info = GetTokenInfo().execute_n_fetchone({'con_id': con_id, 'c_id': c_id}, sesh=sesh)
        if not avail_token and token_info:
            return False

        # Claim the token and update the database
        tx_hash = g.geth.claim_token(token_info['con_addr'], token_info['con_abi'], token_info['c_hash'],
                                     avail_token['t_id'])
        rows_updated = SetToken().execute(
            {'con_id': con_id, 't_hash': tx_hash, 't_id': avail_token['t_id'], 'c_id': c_id}, sesh=sesh)

        # Make sure a row was updated
        if rows_updated == 1:
            return True, 'Token has been claimed!'
    except GethException as e:
        return False, e.exception
    except Exception as e:
        return False, str(e)
