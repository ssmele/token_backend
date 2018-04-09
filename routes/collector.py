from flask import Blueprint, g
from flask_restful import Resource, Api
from models.collector import CreateCollectorRequest, GetCollectorByUsername, GetCollectorByCID
from models.collector import create_collector
from routes import load_with_schema
from utils.verify_utils import generate_jwt, verify_collector_jwt
from utils.utils import success_response, error_response
from utils.doc_utils import BlueprintDocumentation

collector_bp = Blueprint('collector', __name__)
collector_docs = BlueprintDocumentation(collector_bp, 'Collector')
url_prefix = '/collector'


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


class Collector(Resource):

    @load_with_schema(CreateCollectorRequest)
    @collector_docs.document(url_prefix, 'POST', "Method to create collector. Returns jwt for other methods.",
                             input_schema=CreateCollectorRequest)
    def post(self, data):
        try:
            collector = create_collector(data)
            return success_response({'jwt': generate_jwt(collector)}, http_code=201)
        except Exception as e:
            return error_response("Couldn't create account", http_code=200)

    @verify_collector_jwt
    @collector_docs.document(url_prefix, 'GET',
                             "Method to retrieve collector information. Requires jwt from login/creation account.",
                             url_params={'c_id': 'c_id of collector to search for.'})
    def get(self):
        collector = GetCollectorByCID().execute_n_fetchone({'c_id': g.collector_info['c_id']})
        if collector:
            return success_response(collector)
        else:
            return error_response(status="Couldn't retrieve collector info.", status_code=-1, http_code=200)


collector_api_bp = Blueprint('collector_api', __name__)
collector_api = Api(collector_api_bp)
collector_api.add_resource(Collector, url_prefix)


# TODO: GET COLLECTION.
# TODO: CLAIM.