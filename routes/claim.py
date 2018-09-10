import traceback

from flask import Blueprint, g

from ether.geth_keeper import GethException
from models.claim import ClaimRequest, DoesCollectorOwnToken, GetTokenInfo, GetAvailableToken, SetToken
from models.constraints import validate_uni_code_constraints, validate_time_constraints, validate_location_constraints
from routes import load_with_schema, requires_geth
from utils.db_utils import requires_db
from utils.doc_utils import BlueprintDocumentation
from utils.utils import success_response, error_response
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
    results, msg = claim_token_for_user(data['con_id'], g.collector_info['c_id'], data.get('constraints', {}), g.sesh)
    if results:
        g.sesh.commit()
        return success_response(msg)
    else:
        g.sesh.rollback()
        return error_response(msg)


def claim_token_for_user(con_id, c_id, constraints, sesh):
    """ Attempts to claim a token for the given user

    :return:
    :param con_id: The contract_id of the token
    :param c_id: The collector_id of the collecting user
    :param sesh: The database session to use
    :param constraints: Contraint information given by user.
    :return: True if the claim request was successful, False if otherwise
    """
    try:
        # Check to see if this collector already has this token.
        if DoesCollectorOwnToken().execute_n_fetchone({'con_id': con_id, 'c_id': c_id}, schema_out=False):
            return False, 'User already has token'

        # Enforcing claim constraints..
        # Unique Code Constraints.
        if not validate_uni_code_constraints(con_id, constraints.get('code', None)):
            return False, "Constraint Failed: Code provided does not match any codes required to claim this token."

        # Time Constraints # TODO: Figure out how to compare the times.
        # if not validate_time_constraints():
        #    return False, 'Invalid Time'

        # Location Claims # TODO: Figure out how to compare the distances.
        # if not validate_location_constraints():
        #    return False, 'Invalid Location'

        # Make sure a token is available and that it has info
        avail_token = GetAvailableToken().execute_n_fetchone({'con_id': con_id}, sesh=sesh)
        token_info = GetTokenInfo().execute_n_fetchone({'con_id': con_id, 'c_id': c_id}, sesh=sesh)
        if not avail_token and not token_info:
            return False, 'No available tokens'

        # Claim the token and update the database
        tx_hash = g.geth.claim_token(token_info['con_addr'], token_info['con_abi'], token_info['c_hash'],
                                     avail_token['t_id'])
        rows_updated = SetToken().execute(
            {'con_id': con_id, 't_hash': tx_hash, 't_id': avail_token['t_id'], 'c_id': c_id}, sesh=sesh)

        # Make sure a row was updated
        if rows_updated == 1:
            return True, 'Token has been claimed!'
    except GethException as e:
        return False, 'Error with Ethereum Network please try again soon.' + e.exception
    except Exception as e:
        return False, str(e) + traceback.format_exc()
