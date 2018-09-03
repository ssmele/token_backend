from functools import wraps
from sqlite3 import Connection as SQLite3Connection

from flask import g
from marshmallow.exceptions import ValidationError
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.sql import text

from models import Sesh


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

class DataQuery:

    def __init__(self):
        self.sql_txt = text(self.sql_text)
        self.schema_out = self.schema_out

    def execute(self, binds, sesh=None, close_connection=False):
        """
        Calls query and fetch's the first row will return None if no values are present.
        :param binds: Binds to add to the query.
        :param schema_out: If row should be dumped to schemas before returning.
        :param sesh: If we are being provided a connection use it.
        :param close_connection: If true close connection before returning
        :return: First value of None.
        """
        try:
            sesh = sesh if sesh is not None else g.sesh
            res = sesh.execute(self.sql_text, binds)

            # close connection if needed.
            if close_connection:
                sesh.close()

            return res.rowcount
        except DBAPIError as e:
            raise e

    def execute_n_fetchone(self, binds, sesh=None, schema_out=True, close_connection=False):
        """
        Calls query and fetch's the first row will return None if no values are present.
        :param binds: Binds to add to the query.
        :param schema_out: If row should be dumped to schemas before returning.
        :param close_connection: If true close connection before returning
        :return: First value of None.
        """
        try:
            # Perform the selected query and try and get object off of it.
            sesh = sesh if sesh is not None else g.sesh
            rv = sesh.execute(self.sql_text, binds).fetchone()
            if rv is None:
                # Nothing from the query.
                return None

            # close connection if needed.
            if close_connection:
                sesh.close()

            if schema_out:
                # If we got an object then we need to try and parse it into an python dict.
                return self.schema_out.dump(rv)
            else:
                # Else get original Datatype returned by SqlAlchemy.
                return rv

        # If we encounter an error return None
        except DBAPIError:
            return None
        except ValidationError as e:
            return None

    def execute_n_fetchall(self, binds, sesh=None, schema_out=True, close_connection=False):
        """
        Querys and fetch's all rows from the query results.
        :param binds: Binds to use for query.
        :param schema_out: If row should be dumped to schemas before returning.
        :param close_connection: If true close connection before returning
        :return:
        """
        try:
            # Perform the selected query and try and get object off of it.
            sesh = sesh if sesh is not None else g.sesh
            rv = sesh.execute(self.sql_text, binds).fetchall()
            if rv is None:
                # Nothing from the query.
                return None

            # close connection if needed.
            if close_connection:
                sesh.close()

            if schema_out:
                # If we got an object then we need to try and parse it into an python dict.
                return self.schema_out.dump(rv, many=True)
            else:
                # Else get original DataType returned by SqlAlchemy.
                return rv

        # If we encounter an error return None
        except DBAPIError:
            return None
        except ValidationError:
            return None

