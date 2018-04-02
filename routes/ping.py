from flask import Blueprint
from utils.utils import success_response

ping = Blueprint('ping', __name__)


@ping.route('/ping', methods=['GET'])
def pings():
    return success_response("pong")