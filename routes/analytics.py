from flask import Blueprint, g, render_template
from utils.doc_utils import BlueprintDocumentation
from utils.verify_utils import verify_issuer_jwt
from utils.utils import error_response, success_response
from utils.db_utils import requires_db
from models.constraints import get_all_constraints

analytics_bp = Blueprint('analytics', __name__)
analytics_docs = BlueprintDocumentation(analytics_bp, 'Analytics')
url_prefix = '/analytics'


@analytics_bp.route(url_prefix + "/tok_sum", methods=['GET'])
@verify_issuer_jwt
@requires_db
def summary():
    data = g.sesh.execute("""
    select contracts.*, (select count(*) from tokens where tokens.con_id = contracts.con_id and  status = 'S') as 
    num_claimed from contracts where contracts.i_id = :desired_id;""", {'desired_id': g.issuer_info['i_id']}).fetchall()

    bar_values = []
    bar_labels = []
    for r in data:
        bar_values.append(100 * r['num_claimed'] / r['num_created'])
        bar_labels.append(r['name'])

    return render_template('bar_chart.html', title='Tokens Claimed', max=100, labels=bar_labels, values=bar_values)


@analytics_bp.route(url_prefix + '/<con_id>', methods=['GET'])
@verify_issuer_jwt
@requires_db
def analytics(con_id):

    # Get contract.
    data = g.sesh.execute("""
                          select num_created, qr_code_claimable 
                          from contracts 
                          where contracts.con_id = :contract_id;""",
                          {"contract_id": con_id}).fetchall()

    # Check that the data is there
    if len(data) == 0:
        return error_response("Con id doesn't exist")

    num_created = data[0]['num_created']
    qr_code_claimable = data[0]['qr_code_claimable']

    # Figure out how many have been claimed.
    d_num_claimed = g.sesh.execute("""select count(*) as count1 from tokens where tokens.con_id=:contract_id 
    and status='S';""", {'contract_id': con_id}).fetchall()

    num_claimed = d_num_claimed[0]['count1']

    if qr_code_claimable:
        constraints = None
    else:
        constraints = get_all_constraints(con_id)

    return success_response({
        'num_claimed': num_claimed,
        'num_unclaimed': num_created-num_claimed,
        'num_created': num_created,
        'coordinates': claimed_coordinates(con_id),
        'loc_constraints': loc_constraints(con_id),
        'time_windows': token_time_windows(con_id),
        'qr_code_claimable': qr_code_claimable,
        'constraints': constraints,
        'price_and_time': price_and_timestamps(con_id),
        'traded':  num_trades(con_id),
        'num_traded_tokens': num_traded_tokens(con_id)
    })


def claimed_coordinates(con_id):
    d_coordinates = g.sesh.execute("""select latitude, longitude from tokens where tokens.con_id=:contract_id
       and status = 'S' ;""", {'contract_id': con_id}).fetchall()

    coordinates = []
    for i in range(len(d_coordinates)):
        coordinates.append([d_coordinates[i].latitude, d_coordinates[i].longitude])
    return coordinates


def loc_constraints(con_id):
    d_coordinates = g.sesh.execute("""select latitude, longitude, radius from location_claim where location_claim.con_id=:contract_id
    ;""", {'contract_id': con_id}).fetchall()

    if d_coordinates:
        point = [d_coordinates[0].latitude, d_coordinates[0].longitude, d_coordinates[0].radius]
        return point
    else:
        return []


def token_time_windows(con_id):
    d_times = g.sesh.execute("""select start, end from time_claim where time_claim.con_id=:contract_id;
       """, {'contract_id': con_id}).fetchall()

    time_windows = []
    for i in range(len(d_times)):
        time_windows.append([d_times[i].start, d_times[i].end])

    if len(time_windows) == 0:
        d_creation_ts = g.sesh.execute("""select creation_ts from contracts where contracts.con_id=:contract_id;
       """, {'contract_id': con_id}).fetchall()

        time_windows.append([d_creation_ts[0].creation_ts, -1])

    return time_windows


def price_and_timestamps(con_id):
    prices_by_actions = {}

    # Gas cost/price data for trades
    d_trades = g.sesh.execute("""select trade.tr_id, gas_price, gas_cost, creation_ts from trade_item, trade where 
    trade_item.con_id=:contract_id AND trade_item.tr_id=trade.tr_id AND trade.status='A'; """, {'contract_id': con_id}).fetchall()
    trade_transaction_cost = []
    trade_gas_price = []
    trade_gas_cost = []
    trade_timestamps = []
    for i in range(len(d_trades)):
        trade_transaction_cost.append(d_trades[i].gas_price * d_trades[i].gas_cost)
        trade_gas_cost.append(d_trades[i].gas_cost)
        trade_gas_price.append(d_trades[i].gas_price)
        trade_timestamps.append(d_trades[i].creation_ts)

    prices_by_actions["trade_timestamps"] = trade_timestamps
    prices_by_actions["trade_transaction_cost"] = trade_transaction_cost
    prices_by_actions["trade_gas_cost"] = trade_gas_cost
    prices_by_actions["trade_gas_price"] = trade_gas_price

    # Gas cost/price data for claims
    d_claims = g.sesh.execute("""select claim_ts, gas_price, gas_cost from tokens where
     con_id=:contract_id and status = 'S'; """, {'contract_id': con_id}).fetchall()
    claim_transaction_cost = []
    claim_gas_price = []
    claim_gas_cost = []
    claim_timestamps = []

    for i in range(len(d_claims)):
        claim_transaction_cost.append(d_claims[i].gas_price * d_claims[i].gas_cost)
        claim_gas_cost.append(d_claims[i].gas_cost)
        claim_gas_price.append(d_claims[i].gas_price)
        claim_timestamps.append(d_claims[i].claim_ts)

    prices_by_actions["claim_timestamps"] = claim_timestamps
    prices_by_actions["claim_transaction_cost"] = claim_transaction_cost
    prices_by_actions["claim_gas_cost"] = claim_gas_cost
    prices_by_actions["claim_gas_price"] = claim_gas_price
    return prices_by_actions

#Total number of times this token has been traded
def num_trades(con_id):
    d_tradable = g.sesh.execute("""select tradable from contracts where contracts.con_id=:contract_id;
       """, {'contract_id': con_id}).fetchall()

    if d_tradable[0].tradable == 0:
        return -1

    d_num_trades = g.sesh.execute("""select count(*) as count1 from trade, trade_item where status = 'A' and trade.tr_id = trade_item.tr_id 
    and trade_item.con_id=:contract_id ;""", {'contract_id': con_id}).fetchall()

    num_trades = d_num_trades[0]['count1']
    return num_trades


def num_traded_tokens(con_id):
    d_traded_tokens = g.sesh.execute("""select distinct t_id from trade, trade_item where 
                                        trade.tr_id = trade_item.tr_id and status = 'A' and con_id=:contract_id ;""",
                                        {'contract_id': con_id}).fetchall()
    if len(d_traded_tokens) > 0:
        return len(d_traded_tokens[0])
    else:
        return 0

