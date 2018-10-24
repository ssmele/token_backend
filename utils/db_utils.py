from functools import wraps
from sqlite3 import Connection as SQLite3Connection

from flask import g
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text

from models import Sesh


# Need this here as sqlite is a little lame and wont keep this across connections.
from utils.utils import log_kv, LOG_ERROR, LOG_DEBUG


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


def requires_db(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            g.sesh = Sesh()
            return f(*args, **kwargs)
        except Exception as e:
            log_kv(LOG_ERROR, {'error': 'exception while establishing connection', 'exception': str(e)}, exception=True)
            raise e
    return decorated_function


class DataQuery:

    sql_text = None
    schema_out = None

    def __init__(self):
        if self.sql_text is None:
            raise NotImplementedError("Must provide sql_text")
        self.sql_txt = text(self.sql_text)

    def execute(self, binds, sesh=None, close_connection=False):
        """
        Calls query and fetch's the first row will return None if no values are present.
        :param binds: Binds to add to the query.
        :param sesh: If we are being provided a connection use it.
        :param close_connection: If true close connection before returning
        :return: First value of None.
        """
        log_kv(LOG_DEBUG, {'message': 'executing query', 'sql_text': self.sql_text, 'binds': binds})
        try:
            sesh = sesh if sesh is not None else g.sesh
            res = sesh.execute(self.sql_text, binds)

            # close connection if needed.
            if close_connection:
                sesh.close()

            return res.rowcount
        except Exception as e:
            log_kv(LOG_ERROR, {'error': 'could not execute statement', 'exception': str(e)}, exception=True)
            raise e

    def execute_n_fetchone(self, binds, sesh=None, schema_out=True, close_connection=False):
        """
        Calls query and fetch's the first row will return None if no values are present.
        :param binds: Binds to add to the query.
        :param sesh: The database session
        :param schema_out: If row should be dumped to schemas before returning.
        :param sesh: session to use if provided.
        :param close_connection: If true close connection before returning
        :return: First value of None.
        """
        log_kv(LOG_DEBUG, {'message': 'executing query', 'sql_text': self.sql_text, 'binds': binds})
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
                if self.schema_out is None:
                    raise ValueError('No schema to parse with.')
                # If we got an object then we need to try and parse it into an python dict.
                return self.schema_out.dump(dict(rv))
            else:
                return dict(rv)

        # If we encounter an error return None
        except Exception as e:
            log_kv(LOG_ERROR, {'error': 'error executing query', 'exception': str(e)}, exception=True)
            return None

    def execute_n_fetchall(self, binds, sesh=None, schema_out=True, close_connection=False, load_out=False):
        """
        Querys and fetch's all rows from the query results.
        :param binds: Binds to use for query.
        :param sesh: The database session to use
        :param schema_out: If row should be dumped to schemas before returning.
        :param close_connection: If true close connection before returning
        :param sesh: session to use if provided.
        :return:
        """
        log_kv(LOG_DEBUG, {'message': 'executing query', 'sql_text': self.sql_text, 'binds': binds})
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

            # If we got an object then we need to try and parse it into an python dict.
            if schema_out:
                if self.schema_out is None:
                    raise ValueError('No schema to parse with.')

                if load_out:
                    return self.schema_out.load(list(map(dict, rv)), many=True)
                else:
                    return self.schema_out.dump(list(map(dict, rv)), many=True)
            else:
                return list(map(dict, rv))

        # If we encounter an error return None
        except Exception as e:
            log_kv(LOG_ERROR, {'error': 'error executing query', 'exception': str(e)}, exception=True)
            return None
