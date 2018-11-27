from flask import Blueprint, g
from flask_restful import Resource, Api

from models.collector import GetCollectorByCID
from utils.doc_utils import BlueprintDocumentation
from utils.verify_utils import verify_collector_jwt
from utils.db_utils import requires_db
from utils.utils import success_response, error_response, log_kv, LOG_ERROR
from routes import load_with_schema, requires_geth

from models.contract import GetContractByConID, UpdateTokenStatus, TokenStatus
from models.issuer import GetIssuerByIID

from models.transfer import ExternalTransfer

transfer_bp = Blueprint('transfer', __name__)
transfer_docs = BlueprintDocumentation(transfer_bp, 'Transfer')
url_prefix = '/transfer'


class Transfer(Resource):
    @requires_db
    @requires_geth
    @transfer_bp.route(url_prefix)
    @transfer_docs.document(url_prefix, 'POST',
                            """
                            This method performs a transfer to an external account outside of the token environment.
                            """, req_c_jwt=True,
                            error_codes={423: "Couldn't perform external token transfer."})
    @verify_collector_jwt
    @load_with_schema(ExternalTransfer)
    def post(self, data):
        # Get needed issuer, and contract data.
        collector = GetCollectorByCID().execute_n_fetchone({'c_id': g.collector_info['c_id']})
        contract = GetContractByConID().execute_n_fetchone({'con_id': data['con_id']}, schema_out=False)

        try:
            g.geth.perform_transfer(contract['con_addr'], contract['con_abi'], data['t_id'],
                                    src_acct=collector['c_hash'],
                                    dest_acct=data['destination_wallet_hash'])
            UpdateTokenStatus().execute({'new_status': TokenStatus.EXTERNAL.value, 'this_id': data['t_id']})
            g.sesh.commit()
        except Exception as e:
            g.sesh.rollback()
            log_kv(LOG_ERROR, {'error': str(e), 'message': "Could not perform external token transfer!"}, exception=True)
            return error_response('Couldnt not perform external token transfer', status_code=423)

        return success_response("Went through.")


transfer_api = Api(transfer_bp)
transfer_api.add_resource(Transfer, url_prefix)
