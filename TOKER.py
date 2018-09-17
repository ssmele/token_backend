from uuid import uuid1

from flask import current_app, Flask, g, render_template, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from models import Sesh
from models import db
from utils.doc_utils import to_pretty_json
from utils.setup_utils import load_config
from utils.utils import success_response_dict, error_response, log_kv, LOG_DEBUG, LOG_ERROR

# Setting up flask application.
app = Flask(__name__)
CORS(app)
app.config.update(load_config(app.root_path))

with app.app_context():
    current_app.config = app.config

# Set up the database after configuration application.
db.init_app(app)
db.app = app
Sesh.configure(bind=db.engine)

# Have to import these after as they require the database to be set up with the application configured.
from routes.collector import collector_bp, collector_docs
from routes.issuer import issuer_bp, issuer_docs
from routes.ping import ping, ping_docs
from routes.claim import claim_bp, claim_docs
from routes.contract import contract_bp, contract_docs
from routes.login import login_bp, login_docs
from routes.explore import explore_bp, explore_docs
from routes.analytics import analytics_bp
from routes.frontend import frontend_bp

# Registering blueprints.
app.register_blueprint(collector_bp)
app.register_blueprint(issuer_bp)
app.register_blueprint(ping)
app.register_blueprint(claim_bp)
app.register_blueprint(contract_bp)
app.register_blueprint(login_bp)
app.register_blueprint(explore_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(frontend_bp)


@app.before_request
def log_request():
    g.log_id = str(uuid1())[:8]
    log_kv(LOG_DEBUG, {'message': 'received request', 'method': request.method, 'headers': request.headers,
                       'url': request.url, 'data': request.get_data()})


@app.errorhandler(Exception)
def handle_bad_request(e):
    log_kv(LOG_ERROR, {'error': 'exception while processing request', 'exception': str(e)}, exception=True)
    if isinstance(e, HTTPException):
        return error_response(str(e), http_code=e.code)
    else:
        return error_response('Unknown Error!', http_code=500)


# Setting up the documentation.
@app.route('/docs')
def docs():
    """
    This endpoint simple servers the documentation to the user. The universe is gonna end from heat death anyway f the
    rules and smoke dope for life.
    :return:
    """
    app.jinja_env.filters['tojson_pretty'] = to_pretty_json
    blueprint_doc_list = [collector_docs, issuer_docs, contract_docs, login_docs, ping_docs, claim_docs, explore_docs]
    return render_template('documentation.html', bp_docs=blueprint_doc_list, base_resp=success_response_dict({}))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8088)
