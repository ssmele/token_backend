import traceback

from flask import Blueprint, g

from ether.geth_keeper import GethException
from models.claim import ClaimRequest, DoesCollectorOwnToken, GetTokenInfo, GetAvailableToken, SetToken
from routes import load_with_schema, requires_geth
from utils.db_utils import requires_db
from utils.doc_utils import BlueprintDocumentation
from utils.utils import success_response, error_response, log_kv, LOG_WARNING, LOG_INFO, LOG_ERROR
from utils.verify_utils import verify_collector_jwt

claim_bp = Blueprint('claim', __name__)
claim_docs = BlueprintDocumentation(claim_bp, 'Claim')
url_prefix = '/claim'


@claim_bp.route(url_prefix, methods=['POST'])
@verify_collector_jwt
@requires_geth
@requires_db
@load_with_schema(ClaimRequest)
@claim_docs.document(url_prefix, 'POST', 'Method to claim a token of of a contract.', input_schema=ClaimRequest)
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
        log_kv(LOG_WARNING, {'warning': 'user already has token', 'contract_id': con_id, 'collector_id': c_id})
        return False, 'User already has token'

    try:
        # Make sure a token is available and that it has info
        avail_token = GetAvailableToken().execute_n_fetchone({'con_id': con_id}, sesh=sesh)
        token_info = GetTokenInfo().execute_n_fetchone({'con_id': con_id, 'c_id': c_id}, sesh=sesh)
        if not avail_token and not token_info:
            log_kv(LOG_INFO, {'message': 'no tokens are available', 'contract_id': con_id, 'collector_id': c_id})
            return False, 'No available tokens'

        # Claim the token and update the database
        log_kv(LOG_INFO, {'message': 'claiming ethereum token', 'token_id': avail_token['t_id'],
                          'collector_id': c_id})
        tx_hash = g.geth.claim_token(token_info['con_addr'], token_info['con_abi'], token_info['c_hash'],
                                     avail_token['t_id'])
        rows_updated = SetToken().execute(
            {'con_id': con_id, 't_hash': tx_hash, 't_id': avail_token['t_id'], 'c_id': c_id}, sesh=sesh)

        # Make sure a row was updated
        if rows_updated == 1:
            log_kv(LOG_INFO, {'message': 'successfully claimed token', 'contract_id': con_id, 'collector_id': c_id})
            return True, 'Token has been claimed!'
    except GethException as e:
        log_kv(LOG_ERROR, {'error': 'a geth_exception occurred while claiming token', 'exception': e.exception,
                           'exc_message': e.message, 'contract_id': con_id, 'collector_id': c_id})
        return False, 'GETH !!!' + e.exception
    except Exception as e:
        log_kv(LOG_ERROR, {'error': 'an exception occurred while claiming token', 'exception': str(e),
                           'contract_id': con_id, 'collector_id': c_id})
        return False, str(e) + traceback.format_exc()
