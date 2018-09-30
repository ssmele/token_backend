from enum import Enum

from flask import request
from marshmallow import Schema, fields, post_dump
from sqlalchemy.exc import SQLAlchemyError

from utils.db_utils import DataQuery
from utils.utils import log_kv, LOG_ERROR
from models.constraints import Constraints, InsertLocationConstraint, \
    InsertTimeConstraint, InsertUniqueCodeConstraint, CONSTRAINT_DATETIME_FORMAT


class ClaimTypes(Enum):
    SIMPLE = 'S'
    LOCATION = 'L'
    CODE = 'C'


class ContractRequest(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    num_created = fields.Int(required=True)

    constraints = fields.Nested(Constraints, required=False)

    doc_load_info = {
        'i_id': {'type': 'int', 'desc': 'i_id of the issuer that this contract should be deployed under.'},
        'name': {'type': 'string', 'desc': 'Name for the new token contract.'},
        'description': {'type': 'string', 'desc': 'Description of the new token contract being deployed'},
        'num_created': {'type': 'int', 'desc': 'desired password for collector creation.'},
        'constraints': Constraints.doc_load_info,
        'INFO (NOT APART OF REQUEST)' : {'time_format': CONSTRAINT_DATETIME_FORMAT, 'radius metric': 'meters'}
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
    status = fields.Str(required=True)

    username = fields.Str(dump_only=True)

    @post_dump
    def add_picture_path(self, data):
        data['pic_location'] = request.url_root + 'contract/image=' + data['pic_location']

    doc_dump_info = {
        'con_id': '1', 'i_id': '2', 'con_hash': "", 'name': '', 'description': '', 'num_created': 20,
        'pic_location': 'url to pic', 'status': 'status of contract',
        'constraints': Constraints.doc_load_info
    }


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
        INSERT INTO tokens(con_id, t_hash, status) values(:con_id, :tok_hash, 'N');
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


class GetAllContractsForEth(DataQuery):
    def __init__(self):
        self.sql_text = """
            SELECT c.con_id, c.i_id, c.con_tx, c.con_addr, c.con_abi, i.username
            FROM contracts c, issuers i 
            WHERE c.i_id = i.i_id;
        """

        self.schema_out = None
        super().__init__()


def insert_bulk_tokens(num_to_create, contract_deets, sesh):
    """
    This method inserts the original token contract given the deets and creates the tokens related to it.
    :param num_to_create: Number of tokens to create off this contract.
    :param contract_deets: Details for contract creation.
    :param sesh: The database session
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


def process_constraints(constraints, con_id):
    """
    This method handles all the processing of the constraints passed in by issuers.
    :param constraints: Constraints to process.
    :param con_id: con_id of contract to associated constraints with.
    :return: None
    """
    if 'code_constraints' in constraints:
        process_unique_code_constraints(constraints['code_constraints'], con_id)
    if 'time_constraints' in constraints:
        process_time_constraints(constraints['time_constraints'], con_id)
    if 'location_constraints' in constraints:
        process_location_constraints(constraints['location_constraints'], con_id)


def process_unique_code_constraints(uc_constraints, con_id):
    """
    This method inserts all of the code constraints into the database associated to given con_id.
    :param uc_constraints: codes to add
    :param con_id: con_id of contract to associate constraints to.
    :return: None
    """
    for uc in uc_constraints:
        try:
            InsertUniqueCodeConstraint().execute({'con_id': con_id, 'code': uc['code']})
        except SQLAlchemyError as e:
            log_kv(LOG_ERROR, {'message': 'Exception trying to add code constraint.',
                               'contract_con_id': con_id, 'exception': str(e), 'constraints': uc_constraints})
            continue


def process_time_constraints(time_constraints, con_id):
    """
    This method inserts all of the time constraints into the database associated to given con_id.
    :param time_constraints: time constraints to add.
    :param con_id: con_id of contract to associate constraints to.
    :return:
    """
    for tc in time_constraints:
        try:
            InsertTimeConstraint().execute({'con_id': con_id, 'start': tc['start'].strftime(CONSTRAINT_DATETIME_FORMAT),
                                            'end': tc['end'].strftime(CONSTRAINT_DATETIME_FORMAT)})
        except SQLAlchemyError as e:
            log_kv(LOG_ERROR, {'message': 'Exception trying to add time constraint.', 'contract_con_id': con_id,
                               'exception': str(e), 'constraints': time_constraints})
            continue


def process_location_constraints(location_constraints, con_id):
    """
    This method inserts all of the location constraints into the database associated to given con_id.
    :param location_constraints: location constraints to add.
    :param con_id: con_id of contract to associate constraints to.
    :return:
    """
    for lc in location_constraints:
        try:
            InsertLocationConstraint().execute({'con_id': con_id, 'latitude': lc['latitude'],
                                                'longitude': lc['longitude'], 'radius': lc['radius']})
        except SQLAlchemyError as e:
            log_kv(LOG_ERROR, {'message': 'Exception trying to add location constraint.', 'contract_con_id': con_id,
                               'exception': str(e), 'constraints': location_constraints})
            continue
