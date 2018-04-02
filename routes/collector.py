from flask import Blueprint
from models.collector import CreateCollectorRequest
from routes import load_with_schema
from utils.utils import success_response
from models import db

collector = Blueprint('collector', __name__)


@collector.route('/collector/<string:username>')
def get_collector(username):
    rv = db.engine.connect().execute('select * from collectors')
    for r in rv:
        print(r)
    return success_response(username)


@collector.route('/collector', methods=['POST'])
@load_with_schema(CreateCollectorRequest)
def collectors(data):
    return success_response(data)