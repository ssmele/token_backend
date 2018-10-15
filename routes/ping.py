from flask import Blueprint, g

from utils.doc_utils import BlueprintDocumentation
from utils.utils import success_response, log_kv, LOG_INFO
from utils.verify_utils import verify_issuer_jwt, verify_collector_jwt

ping = Blueprint('ping', __name__)
ping_docs = BlueprintDocumentation(ping, 'Ping')
url_prefix = '/ping'


@ping.route(url_prefix, methods=['GET'])
@ping_docs.document(url_prefix, 'GET', 'Method to test connectivity to server.')
def pings():
    log_kv(LOG_INFO, {'message': 'ping called pong respond'})
    return success_response("pong")


@ping.route(url_prefix+'_issuer_a', methods=['GET'])
@verify_issuer_jwt
@ping_docs.document(url_prefix+'_issuer_a', 'GET', description='Ping that requires collector verification.',
                    req_i_jwt=True)
def issuer_a_ping():
    log_kv(LOG_INFO, {'message': 'authorized issuer ping called', 'issuer_id': g.issuer_info['i_id']})
    return success_response("pong for i_id:{}".format(g.issuer_info['i_id']))


@ping.route(url_prefix+'_collector_a', methods=['GET'])
@verify_collector_jwt
@ping_docs.document('collector_a_'+url_prefix, 'GET', description='Ping that requires collector verification.',
                    req_c_jwt=True)
def collector_a_ping():
    log_kv(LOG_INFO, {'message': 'authorized collector ping called', 'collector_id': g.collector_info['c_id']})
    return success_response("pong for c_id:{}".format(g.collector_info['c_id']))
