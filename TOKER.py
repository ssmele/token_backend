from flask import Flask
from models import db
from utils.setup_utils import load_config

# Setting up flask application.
app = Flask(__name__)
app.config.update(load_config())

# Set up the database after configuration application.
db.init_app(app)
db.app = app

# Have to import these after as they require the database to be set up with the application configured.
from routes.collector import collector
from routes.issuer import issuer
from routes.ping import ping

# Registering blueprints.
app.register_blueprint(collector)
app.register_blueprint(issuer)
app.register_blueprint(ping)


if __name__ == '__main__':
    app.run(host = 'localhost', debug=True, port = 8088)
