from flask import Blueprint, g, render_template, request
from utils.doc_utils import BlueprintDocumentation
from utils.verify_utils import verify_issuer_jwt
from models import requires_db
from utils.utils import error_response

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
def percent_claimed(con_id):

    data = g.sesh.execute("""select * from contracts where contracts.con_id = :contract_id;""",
                           {"contract_id": con_id}).fetchall()
    if len(data) == 0:
        return error_response("Con id doesn't exist")

    d_num_claimed = g.sesh.execute("""select count(*) as count1 from tokens where tokens.con_id=:contract_id 
    and status='S';""", {'contract_id': con_id}).fetchall()

    num_claimed = d_num_claimed[0]['count1']

    d_num_created = g.sesh.execute("""select contracts.num_created as count2 from contracts where 
    contracts.con_id = :contract_id;""", {"contract_id": con_id}).fetchall()
    num_created = d_num_created[0]['count2']

    values = [num_claimed, num_created - num_claimed]  # = num claimed, num unclaimed
    return render_template('pie_chart.html', values=values)
