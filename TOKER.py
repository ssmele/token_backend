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
from routes.collector import collector
from routes.issuer import issuer
from routes.ping import ping
from routes.claim import claim
from routes.token import token
from routes.login import login

# Registering blueprints.
app.register_blueprint(collector)
app.register_blueprint(issuer)
app.register_blueprint(ping)
app.register_blueprint(claim)
app.register_blueprint(token)
app.register_blueprint(login)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port = 8088)
