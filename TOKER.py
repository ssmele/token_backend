from flask import Flask
from models import db
from utils.setup_utils import load_config

# Setting up flask application.
app = Flask(__name__)
app.config.update(load_config(app.root_path))

# Set up the database after configuration application.
db.init_app(app)
db.app = app

# Have to import these after as they require the database to be set up with the application configured.
from routes.collector import collector_bp
from routes.issuer import issuer_bp
from routes.ping import ping
from routes.claim import claim
from routes.token import token
from routes.login import login_bp

# Registering blueprints.
app.register_blueprint(collector_bp)
app.register_blueprint(issuer_bp)
app.register_blueprint(ping)
app.register_blueprint(claim)
app.register_blueprint(token)
app.register_blueprint(login_bp)

# Need to move this to another file.
from flask import request, jsonify
TEMP_JWT = 'SECRET_AND_SEUCRE_420'

#TODO: Make transition to auth on always.
#@app.before_request
def check_jwt():
    # Get the key out of the authroization header
    key = request.headers.get('Authorization')
    if key is None:
        return jsonify("Access Denied"), 401
    key = key.split('Bearer ')[1]
    if key != TEMP_JWT:
        return jsonify("Access Denied"), 401




if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port = 8088)
