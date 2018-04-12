from flask import Blueprint
from models.contract import GetAllContracts
from utils.utils import success_response, error_response
from utils.doc_utils import BlueprintDocumentation

explore_bp = Blueprint('explore', __name__)
explore_docs = BlueprintDocumentation(explore_bp, 'Explore')
url_prefix = '/explore'


@explore_bp.route(url_prefix + '/contracts', methods=['GET'])
@explore_docs.document(url_prefix + '/contracts', 'GET', "Get's all contracts for the explore page.")
def get_all_contracts():
    contracts = GetAllContracts().execute_n_fetchall({})
    if contracts:
        return success_response({'contracts': contracts})
    else:
        return error_response(status="Couldn't retrieve contracts")