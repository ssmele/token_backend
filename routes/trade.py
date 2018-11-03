from flask import Blueprint, g
from flask_restful import Resource, Api

from utils.doc_utils import BlueprintDocumentation
from utils.utils import success_response, error_response, log_kv, LOG_INFO, LOG_ERROR
from utils.db_utils import requires_db
from utils.verify_utils import verify_collector_jwt
from ether.geth_keeper import GethException
from routes import load_with_schema
from models.trade import TradeRequest, DeleteTradeRequest, TradeResponseRequest, GetTradeByTRID, UpdateTradeStatus, \
    TradeStatus, GetTradeItems, InvalidateTradeRequests, GetActiveTradeRequests, UpdateOwnership, GetUntradables, \
    create_trade_request, check_trade_item_ownership, check_active_trade_item, is_valid_trade_items, \
    validate_offer_and_trade, GetTokenInfo, TradeResponse
from models.collector import GetCollectorByCID

trade_bp = Blueprint('trade', __name__)
trade_docs = BlueprintDocumentation(trade_bp, 'Trade')
url_prefix = '/trade'


class Trade(Resource):

    @load_with_schema(TradeRequest, dump=True)
    @requires_db
    @verify_collector_jwt
    @trade_docs.document(url_prefix + ' ', 'POST', 'Method to issue trade request.', input_schema=TradeRequest,
                         req_c_jwt=True)
    def post(self, data):
        try:
            # Ensure the trader is the one making the request.
            if data['trader']['c_id'] != g.collector_info['c_id']:
                return error_response('Not allowed to issue this trade request.')

            # Ensure all the items put up for trade are tradable tokens.
            con_ids = set([t_i['con_id'] for t_i in data['trader']['offers']] +
                          [t_i['con_id'] for t_i in data['tradee']['offers']])
            untradable_con_ids = GetUntradables().execute_n_fetchall({'con_ids': ','.join(map(str, set(con_ids)))},
                                                                     schema_out=False)
            if len(untradable_con_ids) != 0:
                return error_response('Attempting to issue trade request with untrabable tokens.',
                                      untradable_cons=untradable_con_ids)

            # Ensure trader owns all tokens put up by trader.
            for t_i in data['trader']['offers']:
                if not check_trade_item_ownership(data['trader']['c_id'], t_i['con_id'], t_i['t_id']):
                    log_kv(LOG_INFO, {'info': 'collector made trade request containing token they did not own.',
                                      'trader_c_id': data['trader']['c_id'], 'con_id': t_i['con_id'],
                                      't_id': t_i['t_id']})
                    return error_response("Collector making request doesn't have ownership of tokens within trade")

            # Ensure trader doesn't have any active trades containing put up tokens.
            for t_i in data['trader']['offers']:
                if check_active_trade_item(data['trader']['c_id'], t_i['con_id'], t_i['t_id']):
                    log_kv(LOG_INFO, {'info': 'collector attempting to make trade on active token.',
                                      'trader_c_id': data['trader']['c_id'], 'con_id': t_i['con_id'],
                                      't_id': t_i['t_id']})
                    return error_response("Collector making request already has token in an active trade.")

            # Ensure tradee owns all tokens request
            for t_i in data['tradee']['offers']:
                if not check_trade_item_ownership(data['tradee']['c_id'], t_i['con_id'], t_i['t_id']):
                    log_kv(LOG_INFO, {'info': 'collector made trade request containing token tradee did not own.',
                                      'tradee_c_id': data['tradee']['c_id'], 'con_id': t_i['con_id'],
                                      't_id': t_i['t_id']})
                    return error_response("Collector making request for token the tradee doesn't have ownership of.")

            # TODO: Need to add validation for the eth_offer here. - Once tokens are put up for trade

            # If we are dealing with a valid trade request persist it within the database.
            new_tr_id = create_trade_request(data)

            # TODO: transfer trader items to intermittent account - Once tokens are put up for trade

            data.update({'tr_id': new_tr_id})
            g.sesh.commit()
            return success_response(resp_data={'trade_info': data},
                                    status='Trade request sent.',
                                    http_code=201)
        except Exception as e:
            g.sesh.rollback()
            return error_response("Couldn't create trade request.".format(str(e)))

    @requires_db
    @verify_collector_jwt
    @load_with_schema(DeleteTradeRequest)
    @trade_docs.document(url_prefix + '  ', 'DELETE', 'Method to cancel trade request.',
                         input_schema=DeleteTradeRequest, req_c_jwt=True)
    def delete(self, data):

        # Get trade specified by requester.
        trade = GetTradeByTRID().execute_n_fetchone(data, schema_out=False)

        # Make sure got a trade.
        if trade is None:
            return error_response('No trade request specified for that tr_id.')

        # Make sure trade is in correct state to delete.
        if trade['status'] != TradeStatus.REQUESTED.value:
            return error_response('Trade is not in a valid state to delete.')

        # Ensure requester has access to cancel this trade.
        if trade['trader_c_id'] != g.collector_info['c_id']:
            log_kv(LOG_INFO, {'info': "Attempted deletion of trade request not owned by authorized collector",
                              'c_id': g.collector_info['c_id']})
            return error_response('Authorized collector does not have ownership over this trade.')

        # TODO: transfer items back from intermittent account - Once tokens are put up for trade

        # If identity has be verified update the status.
        data.update({'new_status': TradeStatus.CANCELED.value})
        if UpdateTradeStatus().execute(data):
            g.sesh.commit()
            return success_response(status='Trade request canceled.')
        else:
            g.sesh.rollback()
            return error_response(status='Unable to cancel trade request.')

    @requires_db
    @verify_collector_jwt
    @load_with_schema(TradeResponseRequest)
    @trade_docs.document(url_prefix + '    ', 'PUT', 'Method to respond to trade request.',
                         input_schema=TradeResponseRequest, req_c_jwt=True)
    def put(self, data):
        # Get trade specified by requester.
        trade = GetTradeByTRID().execute_n_fetchone(data, schema_out=False)

        # Make sure got a trade.
        if trade is None:
            return error_response('No trade request specified for given tr_id.')

        # Make sure trade is in correct state.
        if trade['status'] != TradeStatus.REQUESTED.value:
            return error_response('Trade is not in a valid state to accept.')

        # Ensure requester has access to respond to this request.
        if trade['tradee_c_id'] != g.collector_info['c_id']:
            log_kv(LOG_INFO, {'info': "Attempted manipulation of trade request not directed to authorized collector.",
                              'c_id': g.gollector_info['c_id']})
            return error_response('Authorized collector is not the collector trade was intended for.')

        # logic for accepting the request
        if data['accept']:
            # Get trade items specified by requester.
            trade_items = GetTradeItems().execute_n_fetchall({'tr_id': trade['tr_id']}, schema_out=False)

            # Check to make sure the trade_items are still valid.
            if is_valid_trade_items(trade_items):

                # If trade items are valid we can go through with the trade. Start by invalidating all trades
                # containing items used within this trade.
                for trade_item in trade_items:
                    try:
                        InvalidateTradeRequests().execute({'con_id': trade_item['con_id'], 't_id': trade_item['t_id']})
                    except Exception as e:
                        log_kv(LOG_ERROR, {'error': 'error invalidating trades containing trade items',
                                           'con_id': trade_item['con_id'], 't_id': trade_item['t_id'],
                                           'exception': str(e)}, exception=True)
                        g.sesh.rollback()
                        return error_response('Error accepting request.', http_code=400)

                # Go through and transfer ownership over
                trader_c_id, tradee_c_id = trade['trader_c_id'], trade['tradee_c_id']
                for trade_item in trade_items:
                    try:
                        # Figure out new ownership.
                        if trade_item['owner'] == trader_c_id:
                            prev_owner, new_owner = trader_c_id, tradee_c_id
                        else:
                            prev_owner, new_owner = tradee_c_id, trader_c_id

                        # Update the ownership.
                        upt_cnt = UpdateOwnership().execute({'con_id': trade_item['con_id'], 't_id': trade_item['t_id'],
                                                             'new_owner': new_owner, 'prev_owner': prev_owner})
                        # Ensure that the ownership was actually updated.
                        if upt_cnt != 1:
                            log_kv(LOG_ERROR, {'error': 'error transferring token ownership',
                                               'con_id': trade_item['con_id'], 't_id': trade_item['t_id']})
                            return error_response("Error Accepting request.")

                    except Exception as e:
                        log_kv(LOG_ERROR, {'error': 'error transferring ownership of token.',
                                           'con_id': trade_item['con_id'], 't_id': trade_item['t_id'],
                                           'owner_c_id': trade_item['owner'], 'exception': str(e)}, exception=True)
                        g.sesh.rollback()
                        return error_response('Error Accepting request', http_code=400)

                # Update trade request logic.
                data.update({'new_status': TradeStatus.ACCEPTED.value})
                if not UpdateTradeStatus().execute(data):
                    g.sesh.rollback()
                    return error_response(status='Error accepting request.')

                # Perform the logic on the block chain now.
                try:
                    validate_offer_and_trade(trade_items, tradee_c_id, trader_c_id, trade['trader_eth_offer'])
                except GethException as e:
                    log_kv(LOG_ERROR, {'error': 'exception while performing trades', 'exception': str(e.exception),
                                       'message': e.message}, exception=True)
                    g.sesh.rollback()
                    return error_response('Error accepting request. [G]')
                except Exception as e:
                    log_kv(LOG_ERROR, {'error': 'exception while performing trades', 'exception': str(e)},
                           exception=True)
                    g.sesh.rollback()
                    return error_response('Error accepting request. [G]')

                # If all the ethereum logic went through then commit database changes.
                g.sesh.commit()
                return success_response(status='Trade request accepted.')

            else:
                # Perform logic to decline the trade.
                data.update({'new_status': TradeStatus.INVALID.value})
                if UpdateTradeStatus().execute(data):
                    g.sesh.commit()
                    return success_response(status='Trade request declined.')
                else:
                    g.sesh.rollback()
                    return error_response(status='Unable to decline trade request.')
        # Logic for declining the request.
        else:

            # TODO: transfer items back from intermittent account - once tokens are put up for trade

            # Perform logic to decline the trade.
            data.update({'new_status': TradeStatus.DECLINED.value})
            if UpdateTradeStatus().execute(data):
                g.sesh.commit()
                return success_response(status='Trade request declined.')
            else:
                g.sesh.rollback()
                return error_response(status='Unable to decline trade request.')


@trade_bp.route(url_prefix, methods=['GET'], defaults={'version': None})
@trade_bp.route('/tradee', methods=['GET'], defaults={'version': 'tradee'})
@trade_bp.route('/trader', methods=['GET'], defaults={'version': 'trader'})
@requires_db
@verify_collector_jwt
@trade_docs.document(url_prefix + '     ', 'GET', 'Method to get all active trade requests.', req_c_jwt=True)
@trade_docs.document('/tradee', 'GET', 'Method to get all active trade requests where authorized user is tradee.',
                     req_c_jwt=True)
@trade_docs.document('/trader', 'GET', 'Method to get all active trade requests where authorized user is trader.',
                     req_c_jwt=True)
def get(version=None):
    # Get all tr_ids of active trade_requests containing the authorized collector..
    tr_ids = GetActiveTradeRequests(version).execute_n_fetchall({'c_id': g.collector_info['c_id']}, schema_out=False)

    trades = []
    for tr_id in map(lambda x: x['tr_id'], tr_ids):
        # Get base trade info and all trade items associated.
        trade = GetTradeByTRID().execute_n_fetchone({'tr_id': tr_id}, schema_out=False)
        trade_items = GetTradeItems().execute_n_fetchall({'tr_id': tr_id}, schema_out=False)

        # Getting collector info..
        trader_collector = GetCollectorByCID().execute_n_fetchone({'c_id': trade['trader_c_id']})
        tradee_collector = GetCollectorByCID().execute_n_fetchone({'c_id': trade['tradee_c_id']})

        # Getting trade offer, tradee offer info.
        trader_offers = [
            GetTokenInfo().execute_n_fetchone({'con_id': t_i['con_id'], 't_id': t_i['t_id']}) for t_i in trade_items
            if t_i['owner'] == trade['trader_c_id']
        ]
        tradee_offers = [
            GetTokenInfo().execute_n_fetchone({'con_id': t_i['con_id'], 't_id': t_i['t_id']}) for t_i in trade_items
            if t_i['owner'] == trade['tradee_c_id']
        ]

        # Setting them up in an object.
        cur_trade = TradeResponse().load({
            'trader': {'collector': trader_collector, 'eth_offer': trade['trader_eth_offer'], 'offers': trader_offers},
            'tradee': {'collector': tradee_collector, 'eth_offer': trade['tradee_eth_offer'], 'offers': tradee_offers},
            'status': trade['status'], 'tr_id': tr_id
        })
        trades.append(cur_trade)

    return success_response({'trades': trades})


trade_api = Api(trade_bp)
trade_api.add_resource(Trade, url_prefix)
