from flask import Blueprint
from routes import load_with_schema
from models.collector import LoginCollectorRequest
from utils.utils import success_response, error_response
from models import db

login = Blueprint('login', __name__)
url_prefix = '/login'

login_parser = LoginCollectorRequest()


@login.route(url_prefix, methods=['POST'])
@load_with_schema(LoginCollectorRequest)
def logins(data):
    rv = db.engine.connect().execute("select * from collectors where username = '{}'".format(data['username']))
    for r in rv:
        if data['password'] == login_parser.dump(r)['password']:
            return 'SWAG'
        else:
            return 'BAD'
    else:
        return error_response(status="Username not recongnized in system.", status_code=-1, http_code=200)