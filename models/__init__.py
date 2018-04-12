from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from flask import g
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlite3 import Connection as SQLite3Connection

# Create the database here.
db = SQLAlchemy()
Sesh = sessionmaker()

# Need this here as sqlite is a little lame and wont keep this across connections.
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


def requires_db(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.sesh = Sesh()
        return f(*args, **kwargs)
    return decorated_function
