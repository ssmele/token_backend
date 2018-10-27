from flask import Blueprint, g, render_template
from utils.doc_utils import BlueprintDocumentation
from utils.verify_utils import verify_issuer_jwt
from utils.utils import error_response, success_response
from utils.db_utils import requires_db

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
    data = g.sesh.execute("""select num_created from contracts where contracts.con_id = :contract_id;""",
                          {"contract_id": con_id}).fetchall()

    # Check that the data is there
    if len(data) == 0:
        return error_response("Con id doesn't exist")

    num_created = data[0]['num_created']

    # Figure out how many have been claimed.
    d_num_claimed = g.sesh.execute("""select count(*) as count1 from tokens where tokens.con_id=:contract_id 
    and status='S';""", {'contract_id': con_id}).fetchall()

    num_claimed = d_num_claimed[0]['count1']

    return success_response({
        'num_claimed': num_claimed,
        'num_unclaimed': num_created-num_claimed,
        'num_created': num_created,
        'coordinates': claimed_coordinates(con_id),
        'loc_constraints': loc_constraints(con_id),
        'time_windows': token_time_windows(con_id),
        'price_and_time': price_and_timestamps(con_id),
        'traded':  num_traded(con_id)
    })


@verify_issuer_jwt
@requires_db
def claimed_coordinates(con_id):
    d_coordinates = g.sesh.execute("""select latitude, longitude from tokens where tokens.con_id=:contract_id
       and status = 'S' ;""", {'contract_id': con_id}).fetchall()

    coordinates = []
    for i in range(len(d_coordinates)):
        coordinates.append([d_coordinates[i].latitude, d_coordinates[i].longitude])
    return coordinates


@verify_issuer_jwt
@requires_db
def loc_constraints(con_id):
    d_coordinates = g.sesh.execute("""select latitude, longitude, radius from location_claim where location_claim.con_id=:contract_id
    ;""", {'contract_id': con_id}).fetchall()

    point = [d_coordinates[0].latitude, d_coordinates[0].longitude, d_coordinates[0].radius]
    return point


@verify_issuer_jwt
@requires_db
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


@verify_issuer_jwt
@requires_db
def price_and_timestamps(con_id):
    d_timestamps = g.sesh.execute("""select claim_ts, gas_price from tokens where tokens.con_id=:contract_id and status = 'S';
       """, {'contract_id': con_id}).fetchall()

    timestamps = []
    for i in range(len(d_timestamps)):
        timestamps.append([d_timestamps[i].claim_ts, d_timestamps[i].gas_price])
    return timestamps


@verify_issuer_jwt
@requires_db
def num_traded(con_id):
    d_tradable = g.sesh.execute("""select tradable from contracts where contracts.con_id=:contract_id;
       """, {'contract_id': con_id}).fetchall()

    if d_tradable[0].tradable == 0:
        return -1

    d_num_trades = g.sesh.execute("""select count(*) as count1 from trade, trade_item where status = 'A' and trade.tr_id = trade_item.tr_id 
    and trade_item.con_id=:contract_id ;""", {'contract_id': con_id}).fetchall()

    num_trades = d_num_trades[0]['count1']
    return num_trades



