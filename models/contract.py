from marshmallow import Schema, fields
from utils.db_utils import DataQuery
from enum import Enum


class ContractRequest(Schema):
    i_id = fields.Int(required=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    num_created = fields.Int(required=True)


class InsertNewContract(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO contracts(i_id, hash, name, description, num_created, claim_type) 
        VALUES(:i_id, :hash, :name, :description, :num_created, :claim_type)
        """
        self.schema_out = None
        super().__init__()


class ClaimTypes(Enum):
    SIMPLE = 'S'
    LOCATION = 'L'
    CODE = 'C'
