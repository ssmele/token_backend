from marshmallow import Schema, fields

from models.contract import GetContractResponse
from utils.db_utils import DataQuery


TOKEN_RESPONSE_DOC = {
    't_id': 't_id of token',
    'con_id': 'con_id of the token.',
    't_hash': 'hash on ethereum network tied to the token.',
    'owner_c_id': 'c_id of current owner of token.',
    'owner_c_id': 'c_id of current owner of token.'
}


class TokenResponse(GetContractResponse):
    t_id = fields.Int(required=True)
    con_id = fields.Int(required=True)
    t_hash = fields.Str(required=True)
    owner_c_id = fields.Str(required=True)

    doc_dump_info = TOKEN_RESPONSE_DOC


COLLECTOR_DOC_INFO = {
        'username': 'username for collector.',
        'password': 'password for collector.'
}


class CreateCollectorRequest(Schema):
    c_id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

    doc_load_info = COLLECTOR_DOC_INFO


COLLECTOR_INFO_REQUEST_DOC = {
    'c_id': 'c_id of the collector',
    'username': 'username of collector',
    'c_hash': 'collectors wallet hash.',
    'c_priv_key': 'collector private key.'
}


class CollectorInfoRequest(Schema):
    c_id = fields.Int(required=True)
    username = fields.Str(required=True)
    c_hash = fields.Str(required=True)
    c_priv_key = fields.Str(required=True)

    doc_dump_info = COLLECTOR_INFO_REQUEST_DOC


class LoginCollectorRequest(Schema):
    c_id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True)

    doc_load_info = COLLECTOR_DOC_INFO


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
                contracts.status, contracts.metadata_location, tokens.t_id, tokens.t_hash, tokens.owner_c_id
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
