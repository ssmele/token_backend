from marshmallow import Schema, fields, post_dump
from utils.db_utils import DataQuery
from flask import request
from enum import Enum


class ClaimTypes(Enum):
    SIMPLE = 'S'
    LOCATION = 'L'
    CODE = 'C'


class ContractRequest(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    num_created = fields.Int(required=True)

    doc_load_info = {
        'i_id': {'type': 'int', 'desc': 'i_id of the issuer that this contract should be deployed under.'},
        'name': {'type': 'string', 'desc': 'Name for the new token contract.'},
        'description': {'type': 'string', 'desc': 'Description of the new token contract being deployed'},
        'num_created': {'type': 'int', 'desc': 'desired password for collector creation.'}
    }


class GetContractResponse(Schema):
    con_id = fields.Int(required=True)
    i_id = fields.Int(required=True)
    con_hash = fields.Str(required=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    num_created = fields.Int(required=True)
    claim_type = fields.Str(required=True)
    pic_location = fields.Str(required=True)

    username = fields.Str(dump_only=True)

    @post_dump
    def add_picture_path(self, data):
        data['pic_location'] = request.url_root + 'contract/image=' + data['pic_location']


class InsertNewContract(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO contracts(i_id, con_tx, con_abi, name, description, num_created, claim_type, pic_location) 
        VALUES(:i_id, :con_tx, :con_abi,  :name, :description, :num_created, :claim_type, :pic_location);
        """
        self.schema_out = None
        super().__init__()


class InsertToken(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO tokens(con_id, t_hash) values(:con_id, :tok_hash);
        """

        self.schema_out = None
        super().__init__()


class GetContractByConID(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT *
        FROM contracts
        WHERE con_id = :con_id
        """

        self.schema_out = GetContractResponse()

        super().__init__()


class GetContractsByIssuerID(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT *
        FROM contracts
        WHERE i_id = :i_id
        """

        self.schema_out = GetContractResponse()

        super().__init__()


class GetContractByName(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT *
        FROM contracts
        WHERE name like :name
        """

        self.schema_out = GetContractResponse()

        super().__init__()


class GetAllContracts(DataQuery):
    def __init__(self):
        self.sql_text = """
        SELECT * 
        FROM contracts, issuers
        WHERE contracts.i_id = issuers.i_id;
        """

        self.schema_out = GetContractResponse()

        super().__init__()


def insert_bulk_tokens(num_to_create, contract_deets, sesh):
    """
    This method inserts the original token contract given the deets and creates the tokens related to it.
    :param num_to_create: Number of tokens to create off this contract.
    :param contract_deets: Details for contract creation.
    :return:
    """
    # Insert the contract.
    InsertNewContract().execute(contract_deets, sesh=sesh)
    # TODO: look into if this will always return the insert from above.

    con_id = sesh.execute("select last_insert_rowid() as 'con_id'").fetchone()['con_id']

    # Insert all token records associated with it.
    token_binds = {'con_id': con_id, 'tok_hash': 'temp_hash'}
    for tok_num in range(1, num_to_create+1):
        InsertToken().execute(token_binds, sesh=sesh)
    return con_id

