from flask import Blueprint
from models.collector import CreateCollectorRequest, GetCollectorByUsername, GetCollectorByCID, InsertNewCollector
from models.collector import create_collector
from routes import load_with_schema
from utils.verify_utils import generate_jwt
from utils.utils import success_response, error_response
from utils.doc_utils import BlueprintDocumentation

collector_bp = Blueprint('collector', __name__)
collector_docs = BlueprintDocumentation(collector_bp, 'Collector')
url_prefix = '/collector'


# TODO: Return collector.
@collector_bp.route(url_prefix + '/username=<string:username>', methods=['GET'])
@collector_docs.document(url_prefix + '/username=<string:username>', 'GET',
                         "Method to retrieve collector information by username",
                         url_params={'username': 'username of collector to search for.'})
def get_collector_by_username(username):
    collector = GetCollectorByUsername().execute_n_fetchone({'username': username})
    if collector:
        return success_response(collector)
    else:
        return error_response(status="Couldn't retrieve collector with that username", status_code=-1, http_code=200)


@collector_bp.route(url_prefix + '/c_id=<int:c_id>', methods=['GET'])
@collector_docs.document(url_prefix + '/c_id=<int:c_id>', 'GET',
                         "Method to retrieve collector information by c_id",
                         url_params={'c_id': 'c_id of collector to search for.'})
def get_collector_by_c_id(c_id):
    collector = GetCollectorByCID().execute_n_fetchone({'c_id': c_id})
    if collector:
        return success_response(collector)
    else:
        return error_response(status="Couldn't retrieve collector with that c_id", status_code=-1, http_code=200)


@collector_bp.route(url_prefix, methods=['POST'])
@load_with_schema(CreateCollectorRequest)
@collector_docs.document(url_prefix, 'POST', "Method to create collector.", input_schema=CreateCollectorRequest)
def collectors(data):
    try:
        collector = create_collector(data)
        return success_response({'jwt': generate_jwt(collector)}, http_code=201)
    except Exception as e:
        return error_response("Couldn't create account", http_code=200)


# TODO: GET COLLECTION.
# TODO: GET COLLECTOR.
# TODO: CLAIM.