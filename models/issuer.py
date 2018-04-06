from marshmallow import Schema, fields
from utils.db_utils import DataQuery


class CreateIssuerRequest(Schema):
    """
    Schema for creating issuer.
    """
    i_id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class LoginIssuerRequest(Schema):
    """
    Schema for gathering login request.
    """
    username = fields.Str(required=True)
    password = fields.Str(required=True)


class InsertNewIssuer(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO issuers(username, password) 
        values(:username, :password)
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
        SELECT i_id, username
        FROM issuers
        WHERE i_id = :i_id
        """

        self.schema_out = CreateIssuerRequest()

        super().__init__()


class GetIssuerLoginDetails(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT username, password
        FROM issuers
        WHERE username = :username
        """

        self.schema_out = LoginIssuerRequest()

        super().__init__()