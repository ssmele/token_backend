from flask import Blueprint
from utils.utils import success_response
from utils.doc_utils import BlueprintDocumentation

ping = Blueprint('ping', __name__)
ping_docs = BlueprintDocumentation(ping, 'Ping')
url_prefix = '/ping'


@ping.route(url_prefix, methods=['GET'])
@ping_docs.document(url_prefix, 'GET', 'Method to test connectivity to server.')
def pings():
    return success_response("pong")