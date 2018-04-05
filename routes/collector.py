from flask import Blueprint
from models.collector import CreateCollectorRequest
from routes import load_with_schema
from utils.utils import success_response, error_response
from models import db

collector = Blueprint('collector', __name__)
url_prefix = '/collector'

collector_parser = CreateCollectorRequest()


@collector.route(url_prefix + '/<string:username>', methods=['GET'])
def get_collector_by_username(username):
    rv = db.engine.connect().execute("select * from collectors where username = '{}'".format(username))
    for r in rv:
        return success_response(collector_parser.dump(r))
    else:
        return error_response(status="Couldn't get collector with that username", status_code=-1, http_code=200)


@collector.route(url_prefix + '/<int:c_id>', methods=['GET'])
def get_collector_by_c_id(c_id):
    rv = db.engine.connect().execute("select * from collectors where c_id = '{}'".format(c_id))
    for r in rv:
        return success_response(collector_parser.dump(r))
    else:
        return error_response(status="Couldn't get collector with that c_id", status_code=-1, http_code=200)


@collector.route(url_prefix, methods=['POST'])
@load_with_schema(CreateCollectorRequest)
def collectors(data):
    try:
        db.engine.connect().execute("insert into collectors (userna, password) values('{}','{}')"
                                    .format(data['username'], data['password']))
    except Exception as e:
        return error_response("Couldn't create account", http_code=200)
    return success_response('Created users!', http_code=201)
