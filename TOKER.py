from flask import Flask, render_template
from flask_cors import CORS
from models import db
from utils.setup_utils import load_config
from utils.doc_utils import to_pretty_json
from utils.utils import success_response_dict, error_response

# Setting up flask application.
app = Flask(__name__)
CORS(app)
app.config.update(load_config(app.root_path))

# Set up the database after configuration application.
db.init_app(app)
db.app = app

# Have to import these after as they require the database to be set up with the application configured.
from routes.collector import collector_bp, collector_docs
from routes.issuer import issuer_bp, issuer_docs
from routes.ping import ping, ping_docs
from routes.claim import claim_bp, claim_docs
from routes.token import token
from routes.contract import contract_bp, contract_docs
from routes.login import login_bp, login_docs

# Registering blueprints.
app.register_blueprint(collector_bp)
app.register_blueprint(issuer_bp)
app.register_blueprint(ping)
app.register_blueprint(claim_bp)
app.register_blueprint(token)
app.register_blueprint(contract_bp)
app.register_blueprint(login_bp)


@app.errorhandler(Exception)
def handle_bad_request(e):
    print(e)
    return error_response('Unknown Error!', http_code=500)


# Setting up the documentation.
@app.route('/docs')
def docs():
    """
    This endpoint simple servers the documenation to the user. The universe is gonna end from heat death anyway f the
    rules and smoke dope for life.
    :return:
    """
    app.jinja_env.filters['tojson_pretty'] = to_pretty_json
    blueprint_doc_list = [collector_docs, issuer_docs, contract_docs, login_docs, ping_docs, claim_docs]
    return render_template('documentation.html', bp_docs=blueprint_doc_list, base_resp=success_response_dict({}))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port = 8088)
