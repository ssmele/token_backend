from flask import Blueprint, g
from flask_restful import Resource, Api
from models import requires_db
from models.collector import CreateCollectorRequest, GetCollectorByUsername, GetCollectorByCID, GetCollection
from models.collector import create_collector
from routes import load_with_schema, requires_geth
from utils.verify_utils import generate_jwt, verify_collector_jwt
from utils.utils import success_response, error_response
from utils.doc_utils import BlueprintDocumentation

collector_bp = Blueprint('collector', __name__)
collector_docs = BlueprintDocumentation(collector_bp, 'Collector')
url_prefix = '/collector'


@collector_bp.route(url_prefix + '/username=<string:username>', methods=['GET'])
@requires_db
@collector_docs.document(url_prefix + '/username=<string:username>', 'GET',
                         "Method to retrieve collector information by username",
                         url_params={'username': 'username of collector to search for.'})
def get_collector_by_username(username):
    collector = GetCollectorByUsername().execute_n_fetchone({'username': username})
    if collector:
        return success_response(collector)
    else:
        return error_response(status="Couldn't retrieve collector with that username", status_code=-1, http_code=200)


@collector_bp.route(url_prefix + '/collection', methods=['GET'])
@collector_docs.document(url_prefix + '/collection', 'GET',
                         'This method returns a list of tokens in the collectors collection. Needs JWT.')
@requires_db
@verify_collector_jwt
def get_collection():
    # Get collection for user.
    collection = GetCollection().execute_n_fetchall({'c_id': g.collector_info['c_id']})
    if collection is not None:
        return success_response({'collection': collection})
    else:
        return error_response("Couldn't retrieve collectors collection.")


class Collector(Resource):

    @load_with_schema(CreateCollectorRequest)
    @requires_db
    @requires_geth
    @collector_docs.document(url_prefix+" ", 'POST', "Method to create collector. Returns jwt for other methods.",
                             input_schema=CreateCollectorRequest)
    def post(self, data):
        try:
            hash, priv_key = g.geth.create_account()
            collector = create_collector(data, g.sesh)
            g.sesh.commit()
            return success_response({'jwt': generate_jwt(collector)}, http_code=201)
        except Exception as e:
            return error_response("Couldn't create account", http_code=200)

    @verify_collector_jwt
    @requires_db
    @collector_docs.document(url_prefix, 'GET',
                             "Method to retrieve collector information. Requires jwt from login/creation account.",
                             url_params={'c_id': 'c_id of collector to search for.'})
    def get(self):
        collector = GetCollectorByCID().execute_n_fetchone({'c_id': g.collector_info['c_id']})
        if collector:
            return success_response(collector)
        else:
            return error_response(status="Couldn't retrieve collector info.", status_code=-1, http_code=200)


collector_api = Api(collector_bp)
collector_api.add_resource(Collector, url_prefix)
