from flask import Flask, render_template
from models import db
from utils.setup_utils import load_config
from utils.doc_utils import to_pretty_json
from utils.utils import success_response_dict

# Setting up flask application.
app = Flask(__name__)
app.config.update(load_config(app.root_path))

# Set up the database after configuration application.
db.init_app(app)
db.app = app

# Have to import these after as they require the database to be set up with the application configured.
from routes.collector import collector_bp, collector_docs
from routes.issuer import issuer_bp, issuer_docs
from routes.ping import ping, ping_docs
from routes.claim import claim
from routes.token import token
from routes.login import login_bp, login_docs

# Registering blueprints.
app.register_blueprint(collector_bp)
app.register_blueprint(issuer_bp)
app.register_blueprint(ping)
app.register_blueprint(claim)
app.register_blueprint(token)
app.register_blueprint(login_bp)


# Setting up the documentation.
@app.route('/docs')
def docs():
    """
    This endpoint simple servers the documenation to the user. The universe is gonna end from heat death anyway f the
    rules and smoke dope for life.
    :return:
    """
    app.jinja_env.filters['tojson_pretty'] = to_pretty_json
    blueprint_doc_list = [collector_docs, issuer_docs, login_docs, ping_docs]
    return render_template('documentation.html', bp_docs=blueprint_doc_list, base_resp=success_response_dict({}))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port = 8088)
