from marshmallow import Schema, fields
from utils.db_utils import DataQuery
from models import db
from models.token import TokenResponse


class CreateCollectorRequest(Schema):
    c_id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

    doc_load_info = {
        'username': {'type': 'string', 'desc': 'desired username for collector creation.'},
        'password': {'type': 'string', 'desc': 'desired password for collector creation.'}
    }


class LoginCollectorRequest(Schema):
    c_id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True)

    doc_load_info = {
        'username': {'type': 'string', 'desc': 'collector username to use with login.'},
        'password': {'type': 'string', 'desc': 'collector password to use with login.'}
    }


def create_collector(user_deets):
    with db.engine.begin() as connection:
        # Insert the contract.
        InsertNewCollector().execute(user_deets, con=connection)
        collector = GetCollectorByUsername().execute_n_fetchone({'username': user_deets['username']}, con=connection)
        return collector


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


class GetCollection(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT * 
        FROM tokens, contracts 
        WHERE owner_c_id = :c_id
        AND contracts.con_id = tokens.con_id;
        """

        self.schema_out = TokenResponse()
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
        SELECT username, password, c_id
        FROM collectors
        WHERE username = :username
        """

        self.schema_out = LoginCollectorRequest()

        super().__init__()
