from flask import Blueprint

from models.contract import GetAllContracts
from utils.db_utils import requires_db
from utils.doc_utils import BlueprintDocumentation
from utils.utils import success_response, error_response, log_kv, LOG_DEBUG, LOG_ERROR
from models.claim import Location
from models.contract import GetAllContractsByProximity, GetAllTradableContracts, GetProximityContracts, \
    TradableTokenResponse, GET_CONTRACT_DOC_EXPLORE
from routes import load_with_schema


explore_bp = Blueprint('explore', __name__)
explore_docs = BlueprintDocumentation(explore_bp, 'Explore')
url_prefix = '/explore'


@explore_bp.route(url_prefix + '/contracts', defaults={'keyword': None, 'include_nearby': 1}, methods=['GET'])
@explore_bp.route(url_prefix + '/contracts/keyword=<string:keyword>', defaults={'include_nearby': 1},
                  methods=['GET'])
@explore_bp.route(url_prefix + '/contracts/include_nearby=<int:include_nearby>', defaults={'keyword': None},
                  methods=['GET'])
@explore_bp.route(url_prefix + '/contracts/keyword=<string:keyword>&include_nearby=<int:include_nearby>',
                  methods=['GET'])
@requires_db
@explore_docs.document(url_prefix + '/contracts', 'GET',
                       """
                       Get's all contracts for the explore page.
                       """, output_schema=GET_CONTRACT_DOC_EXPLORE)
@explore_docs.document(url_prefix + '/contracts/keyword=<string:keyword>', 'GET',
                       """
                       Get's all contracts for the explore page that have keyword in name or description.
                       """, output_schema=GET_CONTRACT_DOC_EXPLORE)
def get_all_contracts(keyword, include_nearby):
    contracts = GetAllContracts(keyword, include_nearby).execute_n_fetchall({}, close_connection=True)
    if contracts is not None:
        log_kv(LOG_DEBUG, {'debug': 'succesfully got all contracts'})
        return success_response({'contracts': contracts})
    else:
        log_kv(LOG_ERROR, {'warning': 'could not pull all contracts!!!'})
        return error_response(status="Couldn't retrieve contracts")


@explore_bp.route(url_prefix + '/proximity', methods=['POST'])
@explore_bp.route(url_prefix + '/proximity/keyword=<string:keyword>', methods=['POST'])
@load_with_schema(Location)
@requires_db
@explore_docs.document(url_prefix + '/proximity', 'POST',
                       """
                       Returns all contracts that have some sort of location constraint on it. Also returns distance 
                       given location is from the constraint. Distance in meters.
                       """, input_schema=Location, output_schema=GetProximityContracts)
@explore_docs.document(url_prefix + '/proximity/keyword=<string:keyword>', 'POST',
                       """
                       Same as proximmity with keyword.
                       """,
                       input_schema=Location, output_schema=GetProximityContracts)
def get_all_contracts_by_proximity(data, keyword=None):
    contracts = GetAllContractsByProximity(keyword).execute_n_fetchall(data, close_connection=True, load_out=True)
    if contracts is not None:
        log_kv(LOG_DEBUG, {'debug': 'succesfully got all contracts'})
        return success_response({'contracts': contracts})
    else:
        log_kv(LOG_ERROR, {'warning': 'could not pull all contracts!!!'})
        return error_response(status="Couldn't retrieve contracts")


@explore_bp.route(url_prefix + '/tradable', methods=['GET'])
@explore_bp.route(url_prefix + '/tradable/keyword=<string:keyword>', methods=['GET'])
@requires_db
@explore_docs.document(url_prefix + "/tradable", 'GET',
                       """
                       Returns all tokens currently in a tradable state.
                       """, output_schema=TradableTokenResponse)
@explore_docs.document(url_prefix + '/tradable/keyword=<string:keyword>', 'GET',
                       """
                       Same as base tradable method but with keyword search.
                       """, output_schema=TradableTokenResponse)
def get_all_tradable(keyword=None):
    contracts = GetAllTradableContracts(keyword).execute_n_fetchall({}, close_connection=True, load_out=True)
    if contracts is not None:
        log_kv(LOG_DEBUG, {'debug': 'succesfully got all contracts'})
        return success_response({'contracts': contracts})
    else:
        log_kv(LOG_ERROR, {'warning': 'could not pull all contracts!!!'})
        return error_response(status="Couldn't retrieve contracts")