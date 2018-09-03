from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker

# Create the database here.
db = SQLAlchemy()
Sesh = sessionmaker()
