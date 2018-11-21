from flask import Blueprint, g

from utils.doc_utils import BlueprintDocumentation
from utils.verify_utils import verify_issuer_jwt
from utils.db_utils import requires_db
from utils.utils import success_response, error_response, log_kv, LOG_INFO, LOG_ERROR
from routes import load_with_schema, requires_geth

from models.contract import GetContractByConID, UpdateTokenStatus, TokenStatus
from models.issuer import GetIssuerByIID

from models.transfer import ExternalTransfer

transfer_bp = Blueprint('transfer', __name__)
transfer_docs = BlueprintDocumentation(transfer_bp, 'Transfer')
url_prefix = '/transfer'


@requires_db
@requires_geth
@transfer_bp.route(url_prefix)
@transfer_docs.document(url_prefix, 'GET',
                        """
                        This method performs a transfer to an external account outside of the token environment.
                        """, req_i_jwt=True,
                        error_codes={423: "Couldn't perform external token transfer."})
@verify_issuer_jwt
@load_with_schema(ExternalTransfer)
def do_external_transfer(data):
    # Get needed issuer, and contract data.
    issuer = GetIssuerByIID().execute_n_fetchone({'i_id': g.issuer_info['i_id']})
    contract = GetContractByConID().execute_n_fetchone({'con_id': data['con_id']}, schema_out=False)

    try:
        g.geth.perform_transfer(contract['con_addr'], contract['con_abi'], data['t_id'],
                                src_acct=issuer['i_hash'],
                                dest_acct=data['destination_wallet_hash'],
                                src_priv_key=issuer['i_priv_key'])
        UpdateTokenStatus().execute({'new_status': TokenStatus.EXTERNAL.value}, close_connection=True)
    except Exception as e:
        log_kv(LOG_ERROR, {'error': str(e), 'message': "Could not perform external token transfer!"}, exception=True)
        return error_response('Couldnt not perform external token transfer', status_code=423)

    return success_response("Went through.")
