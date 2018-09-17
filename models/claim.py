from marshmallow import Schema, fields
from models.constraints import validate_code, CONSTRAINT_DATETIME_FORMAT, LocationConstraint

from utils.db_utils import DataQuery


class ClaimConstraintRequest(Schema):
    code = fields.Str(required=False, validate=validate_code)
    time = fields.DateTime(CONSTRAINT_DATETIME_FORMAT, required=False)
    location = fields.Nested(LocationConstraint, only=['latitude', 'longitude'], required=False)


class ClaimRequest(Schema):
    con_id = fields.Int(required=True)

    constraints = fields.Nested(ClaimConstraintRequest, required=False)

    doc_load_info = {
        'con_id': {'type': 'int', 'desc': 'con_id of contract in which you want to claim a token from.'},
    }


class GetTokenInfoInternal(Schema):
    """ Schema for Token info for the ETH network """
    t_id = fields.Int(dump_only=True)
    con_addr = fields.Str(dump_only=True)
    con_abi = fields.Str(dump_only=True)
    i_hash = fields.Str(dump_only=True)
    i_priv_key = fields.Str(dump_only=True)
    c_hash = fields.Str(dump_only=True)


class GetAvailableTokenIDInternal(Schema):
    """ Schema that gets an available token_id """
    t_id = fields.Int(dump_only=True)


# ------------------------------QUERIES--------------------------------
class DoesCollectorOwnToken(DataQuery):

    def __init__(self):
        self.sql_text = """
        select * 
        from tokens 
        where owner_c_id = :c_id
        and con_id = :con_id;
        """
        self.schema_out = None
        super().__init__()


class SetToken(DataQuery):

    def __init__(self):
        self.sql_text = """
        UPDATE tokens
        SET owner_c_id = :c_id,
          status = 'P',
          t_hash = :t_hash
        WHERE con_id = :con_id
          AND t_id = :t_id;
        """

        self.schema_out = None
        super().__init__()


class GetAvailableToken(DataQuery):
    """ Gets an available token in the collection """

    def __init__(self):
        self.sql_text = """
            SELECT t_id
            FROM tokens
            WHERE owner_c_id IS NULL 
              AND con_id = :con_id
            LIMIT 1;
        """

        self.schema_out = GetAvailableTokenIDInternal()
        super().__init__()


class GetTokenInfo(DataQuery):
    """ Gets a token's related contract and its issuer information for the ETH network """

    def __init__(self):
        self.sql_text = """
            SELECT t.t_id AS t_id, c.con_addr AS con_addr, c.con_abi AS con_abi, i.i_hash AS i_hash, 
              i_priv_key AS i_priv_key, col.c_hash
            FROM tokens t, contracts c, issuers i, collectors col
            WHERE  t.con_id = :con_id
              AND t.con_id = c.con_id
              AND c.i_id = i.i_id
              AND c.con_addr IS NOT NULL
              AND c.status == 'S'
              AND t.owner_c_id IS NULL
              AND col.c_id = :c_id;
        """

        self.schema_out = GetTokenInfoInternal()
        super().__init__()
