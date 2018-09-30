from flask import Blueprint, g
from flask_restful import Resource, Api

from utils.doc_utils import BlueprintDocumentation
from utils.utils import success_response, error_response
from utils.db_utils import requires_db
from utils.verify_utils import verify_collector_jwt
from routes import load_with_schema
from models.trade import TradeRequest, get_trades, create_trade_request

trade_bp = Blueprint('trade', __name__)
trade_docs = BlueprintDocumentation(trade_bp, 'Trade')
url_prefix = '/trade'


class Trade(Resource):

    @requires_db
    @verify_collector_jwt
    @load_with_schema(TradeRequest)
    def post(self, data):
        try:
            # TODO: Verify they own all tokens, Same with tradee.
            # Ensure the trader is the one making the request.
            if data['trader']['c_id'] != g.collector_info['c_id']:
               return error_response('Not allowed to issue this trade request.')

            create_trade_request(data)
            g.sesh.commit()
            return success_response(resp_data={'trade_info': data},
                                    status='Trade request sent.',
                                    http_code=201)
        except Exception as e:
            g.sesh.rollback()
            return error_response("Couldn't create trade request.".format(str(e)))

    @requires_db
    @verify_collector_jwt
    def get(self):
        return success_response(resp_data={'trades': get_trades(g.collector_info['c_id'])})


trade_api = Api(trade_bp)
trade_api.add_resource(Trade, url_prefix)