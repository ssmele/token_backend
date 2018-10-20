from flask import Blueprint, g
from flask_restful import Resource, Api

from ether.geth_keeper import GethException
from models.collector import CreateCollectorRequest, GetCollectorByUsername, GetCollectorByCID, GetCollection
from models.collector import create_collector
from routes import load_with_schema, requires_geth
from utils.db_utils import requires_db
from utils.doc_utils import BlueprintDocumentation
from utils.utils import success_response, error_response, log_kv, LOG_INFO, LOG_ERROR, LOG_WARNING
from utils.verify_utils import generate_jwt, verify_collector_jwt

collector_bp = Blueprint('collector', __name__)
collector_docs = BlueprintDocumentation(collector_bp, 'Collector')
url_prefix = '/collector'


@collector_bp.route(url_prefix + '/username=<string:username>', methods=['GET'])
@requires_db
@collector_docs.document(url_prefix + '/username=<string:username>', 'GET',
                         "Method to retrieve collector information by username",
                         url_params={'username': 'username of collector to search for.'})
def get_collector_by_username(username):
    collector = GetCollectorByUsername().execute_n_fetchone({'username': username}, close_connection=True)
    if collector:
        log_kv(LOG_INFO, {'message': 'successfully created collector', 'username': username})
        return success_response(collector)
    else:
        log_kv(LOG_WARNING, {'warning': 'could not create collector', 'username': username})
        return error_response(status="Couldn't retrieve collector with that username", status_code=-1, http_code=200)


@collector_bp.route(url_prefix + '/collection', methods=['GET'])
@collector_docs.document(url_prefix + '/collection', 'GET',
                         'This method returns a list of tokens in the collectors collection.',
                         req_c_jwt=True)
@requires_db
@verify_collector_jwt
def get_collection():
    # Get collection for user.
    collection = GetCollection().execute_n_fetchall({'c_id': g.collector_info['c_id']}, close_connection=True)
    if collection is not None:
        return success_response({'collection': collection})
    else:
        log_kv(LOG_ERROR, {'error': 'could not get a user\'s collection', 'collector_id': g.collector_info['c_id']})
        return error_response("Couldn't retrieve collectors collection.")


class Collector(Resource):

    @load_with_schema(CreateCollectorRequest)
    @requires_db
    @requires_geth
    @collector_docs.document(url_prefix+" ", 'POST', "Method to create collector. Returns jwt for other methods.",
                             input_schema=CreateCollectorRequest)
    def post(self, data):
        try:
            # Create the collector account and bind the hash and private key
            data['c_hash'], data['c_priv_key'] = g.geth.create_account()

            # TODO: EXTEND THIS TO TAKE MORE VALUES FROM THE USER. ONLY HAVE TO CHANGE MARSHMALLOW OBEJCT. (HOPEFULLY)
            collector = create_collector(data)
            g.sesh.commit()
            log_kv(LOG_INFO, {'message': 'successfully created collector'})
            return success_response({'jwt': generate_jwt(collector)}, http_code=201)
        except GethException as ge:
            log_kv(LOG_ERROR, {'error': 'a geth_exception occurred while creating collector account',
                               'exception': ge.exception, 'exc_message': ge.message})
            return error_response(ge.message)
        except Exception as e:
            log_kv(LOG_ERROR, {'error': 'an exception occurred while creating collector account',
                               'exception': str(e)})
            return error_response(str(e), http_code=200)

    @verify_collector_jwt
    @requires_db
    @requires_geth
    @collector_docs.document(url_prefix, 'GET',
                             "Method to retrieve collector information. Requires jwt from login/creation account.",
                             url_params={'c_id': 'c_id of collector to search for.'},
                             req_c_jwt=True)
    def get(self):
        collector = GetCollectorByCID().execute_n_fetchone({'c_id': g.collector_info['c_id']}, close_connection=True)

        if collector:
            # Try and get out the eth balance.
            try:
                balance = g.geth.get_eth_balance(collector['c_hash'])
            except GethException as e:
                log_kv(LOG_ERROR, {'error': "Couldn't retrieve eth balance", 'c_id': g.collector_info['c_id'],
                                   'exception': str(e)}, exception=True)
                balance = 'Not available at this time.'

            collector.update({'eth_balance': balance})
            return success_response(collector)
        else:
            log_kv(LOG_WARNING, {'warning': 'could not get collector account',
                                 'collector_id': g.collector_info['c_id']})
            return error_response(status="Couldn't retrieve collector info.", status_code=-1, http_code=200)


collector_api = Api(collector_bp)
collector_api.add_resource(Collector, url_prefix)
