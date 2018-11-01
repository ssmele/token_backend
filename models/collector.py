from marshmallow import Schema, fields

from models.contract import GetContractResponse
from utils.db_utils import DataQuery


class TokenResponse(GetContractResponse):
    t_id = fields.Int(required=True)
    con_id = fields.Int(required=True)
    t_hash = fields.Str(required=True)


class CreateCollectorRequest(Schema):
    c_id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

    doc_load_info = {
        'username': {'type': 'string', 'desc': 'desired username for collector creation.'},
        'password': {'type': 'string', 'desc': 'desired password for collector creation.'}
    }


class CollectorInfoRequest(Schema):
    c_id = fields.Int(required=True)
    username = fields.Str(required=True)
    c_hash = fields.Str(required=True)
    c_priv_key = fields.Str(required=True)


class LoginCollectorRequest(Schema):
    c_id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True)

    doc_load_info = {
        'username': {'type': 'string', 'desc': 'collector username to use with login.'},
        'password': {'type': 'string', 'desc': 'collector password to use with login.'}
    }


def create_collector(user_deets):
    # Insert the contract.
    InsertNewCollector().execute(user_deets)
    collector = GetCollectorByUsername().execute_n_fetchone({'username': user_deets['username']})
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
        SELECT *
        FROM collectors
        WHERE c_id = :c_id
        """

        self.schema_out = CollectorInfoRequest()

        super().__init__()


class GetCollection(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT  contracts.con_id, issuers.i_id, issuers.username as issuer_username, contracts.con_tx as con_hash,
                contracts.name, contracts.description, contracts.num_created, contracts.pic_location, contracts.tradable,
                contracts.status, tokens.t_id, tokens.t_hash
        FROM tokens, contracts, issuers
        WHERE owner_c_id = :c_id
        AND contracts.con_id = tokens.con_id
        AND contracts.i_id = issuers.i_id;
        """

        self.schema_out = TokenResponse()
        super().__init__()


class InsertNewCollector(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO collectors(username, password, c_hash, c_priv_key) 
        values(:username, :password, :c_hash, :c_priv_key)
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
