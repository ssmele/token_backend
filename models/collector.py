from marshmallow import Schema, fields
from utils.db_utils import DataQuery


class CreateCollectorRequest(Schema):
    c_id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

    doc_load_info = {
        'username': {'type': 'string', 'desc': 'desired username for collector creation.'},
        'password': {'type': 'string', 'desc': 'desired password for collector creation.'}
    }


class LoginCollectorRequest(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)

    doc_load_info = {
        'username': {'type': 'string', 'desc': 'collector username to use with login.'},
        'password': {'type': 'string', 'desc': 'collector password to use with login.'}
    }


class GetCollectorByUsername(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT c_id, username
        FROM collectors
        WHERE username = :username
        """

        self.schema_out = CreateCollectorRequest()

        super().__init__()


class GetCollectorByCID(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT c_id, username
        FROM collectors
        WHERE c_id = :c_id
        """

        self.schema_out = CreateCollectorRequest()

        super().__init__()


class InsertNewCollector(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO collectors(username, password) 
        values(:username, :password)
        """
        self.schema_out = None
        super().__init__()


class GetCollectorLoginDetails(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT username, password
        FROM collectors
        WHERE username = :username
        """

        self.schema_out = LoginCollectorRequest()

        super().__init__()
