from marshmallow import Schema, fields

from utils.db_utils import DataQuery


class CreateIssuerRequest(Schema):
    """
    Schema for creating issuer.
    """
    i_id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

    doc_load_info = {
        'username': {'type': 'string', 'desc': 'desired username for issuer creation.'},
        'password': {'type': 'string', 'desc': 'desired password for issuer creation.'}
    }


class IssuerInternalInfo(Schema):
    """
    Schema for creating issuer.
    """
    i_id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)
    i_hash = fields.Str(dump_only=True)
    i_priv_key = fields.Str(dump_only=True)


def create_issuer(user_deets):
    # Insert the contract.
    InsertNewIssuer().execute(user_deets)
    issuer = GetIssuerByUsername().execute_n_fetchone({'username': user_deets['username']})
    return issuer


class LoginIssuerRequest(Schema):
    """
    Schema for gathering login request.
    """
    i_id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True)

    doc_load_info = {
        'username': {'type': 'string', 'desc': 'issuer username to use with login.'},
        'password': {'type': 'string', 'desc': 'issuer password to use with login.'}
    }


class GetIssuerInfo(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT *
        FROM issuers
        WHERE i_id = :i_id
        """

        self.schema_out = IssuerInternalInfo()

        super().__init__()


class InsertNewIssuer(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO issuers(username, password, i_hash, i_priv_key) 
        values(:username, :password, :i_hash, :i_priv_key)
        """
        self.schema_out = None
        super().__init__()


class GetIssuerByUsername(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT i_id, username
        FROM issuers
        WHERE username = :username
        """

        self.schema_out = CreateIssuerRequest()

        super().__init__()


class GetIssuerByIID(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT *
        FROM issuers
        WHERE i_id = :i_id
        """

        self.schema_out = IssuerInfoRequest()

        super().__init__()


class IssuerInfoRequest(Schema):
    i_id = fields.Int(required=True)
    username = fields.Str(required=True)
    i_hash = fields.Str(required=True)
    i_priv_key = fields.Str(required=True)

class GetIssuerLoginDetails(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT *
        FROM issuers
        WHERE username = :username
        """

        self.schema_out = LoginIssuerRequest()

        super().__init__()
