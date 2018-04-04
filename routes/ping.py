from flask import Blueprint
from utils.utils import success_response

ping = Blueprint('ping', __name__)
url_prefix = '/ping'


@ping.route(url_prefix, methods=['GET'])
def pings():
    return success_response("pong")