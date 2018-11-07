from enum import Enum

from flask import request
from marshmallow import Schema, fields, post_dump, post_load
from sqlalchemy.exc import SQLAlchemyError

from utils.db_utils import DataQuery
from utils.utils import log_kv, LOG_ERROR
from models.constraints import Constraints, InsertLocationConstraint, \
    InsertTimeConstraint, InsertUniqueCodeConstraint, CONSTRAINT_DATETIME_FORMAT


class ContractRequest(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    num_created = fields.Int(required=True)
    tradable = fields.Boolean(required=True)
    qr_code_claimable = fields.Boolean(required=True)

    constraints = fields.Nested(Constraints, required=False)

    doc_load_info = {
        'name': {'type': 'string', 'desc': 'Name for the new token contract.'},
        'description': {'type': 'string', 'desc': 'Description of the new token contract being deployed'},
        'num_created': {'type': 'int', 'desc': 'desired password for collector creation.'},
        'tradable': {'type': 'boolean', 'desc': 'boolean to determine if token is tradable.'},
        'qr_code_claimable': {'boolean that says if qrcode should be generated for this contract.'},
        'constraints': Constraints.doc_load_info,
        'INFO (NOT APART OF REQUEST)' : {'time_format': CONSTRAINT_DATETIME_FORMAT, 'radius metric': 'meters',
                                         'constraints': 'The constraints are optional'}
    }


class GetContractResponse(Schema):
    con_id = fields.Int(required=True)
    i_id = fields.Int(required=True)
    con_hash = fields.Str(required=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    num_created = fields.Int(required=True)
    pic_location = fields.Str(required=True)
    qr_code_location = fields.Str(required=True)
    tradable = fields.Boolean(required=True)
    status = fields.Str(required=True)

    issuer_username = fields.Str(dump_only=True)

    @post_dump
    def add_picture_path(self, data):
        data['pic_location'] = request.url_root + 'contract/image=' + data['pic_location']

        if data['qr_code_location']:
            data['qr_code_location'] = request.url_root + 'contract/qr_code=' + data['qr_code_location']

    doc_dump_info = {
        'con_id': '1', 'i_id': '2', 'con_hash': "", 'name': '', 'description': '', 'num_created': 20,
        'pic_location': 'url to pic', 'status': 'status of contract',
        'constraints': Constraints.doc_load_info
    }


class InsertNewContract(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO contracts(i_id, con_tx, con_abi, name, description, tradable, num_created, pic_location) 
        VALUES(:i_id, :con_tx, :con_abi,  :name, :description, :tradable, :num_created, :pic_location);
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

    def __init__(self, keyword=None):
        if keyword is not None:
            self.sql_text = """
            SELECT contracts.con_id, issuers.i_id, issuers.username as issuer_username, contracts.con_tx as con_hash,
            contracts.name, contracts.description, contracts.num_created, contracts.pic_location, contracts.tradable,
            contracts.status
            FROM contracts, issuers
            WHERE contracts.i_id = issuers.i_id
            AND (contracts.name like '%{keyword}%'
            OR contracts.description like '%{keyword}%');
            """.format(keyword=keyword)
        else:
            self.sql_text = """
            SELECT contracts.con_id, issuers.i_id, issuers.username as issuer_username, contracts.con_tx as con_hash,
            contracts.name, contracts.description, contracts.num_created, contracts.pic_location, contracts.tradable,
            contracts.status
            FROM contracts, issuers
            WHERE contracts.i_id = issuers.i_id;
            """

        self.schema_out = GetContractResponse()

        super().__init__()


class GetProximityContracts(Schema):
    # Stuff off contracts.
    con_id = fields.Int(required=True)
    con_hash = fields.Str(required=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    num_created = fields.Int(required=True)
    pic_location = fields.Str(required=True)
    tradable = fields.Boolean(required=True)
    status = fields.Str(required=True)

    # Issuer info.
    i_id = fields.Int(required=True)
    issuer_username = fields.Str(required=True)

    # Info from location constraints.
    distance = fields.Float(required=True)
    radius = fields.Float(required=True)
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)

    @post_dump
    @post_load
    def add_picture_path(self, data):
        data['pic_location'] = request.url_root + 'contract/image=' + data['pic_location']

    doc_dump_info = {
        'con_id': '1', 'i_id': '2', 'con_hash': "", 'name': '', 'description': '', 'num_created': 20,
        'pic_location': 'url to pic', 'status': 'status of contract',
        'constraints': Constraints.doc_load_info
    }


class GetAllContractsByProximity(DataQuery):
    def __init__(self, keyword=None):
        if keyword:
            self.sql_text = """
            SELECT min((((latitude-:latitude)*(latitude-:latitude)) 
            + ((longitude - :longitude)*(longitude - :longitude))) * 1000)
            as distance, radius, latitude, longitude,
            contracts.con_id, contracts.name, contracts.description, contracts.num_created, contracts.pic_location, 
            contracts.tradable, contracts.status, contracts.con_tx as con_hash,
            issuers.username as issuer_username, issuers.i_id
            FROM location_claim, contracts, issuers
            WHERE location_claim.con_id = contracts.con_id
            AND issuers.i_id = contracts.i_id
            AND (contracts.name like '%{keyword}%'
            OR contracts.description like '%{keyword}%')
            GROUP BY location_claim.con_id
            ORDER BY distance ASC;
            """.format(keyword=keyword)
        else:
            self.sql_text = """
            SELECT min((((latitude-:latitude)*(latitude-:latitude)) 
            + ((longitude - :longitude)*(longitude - :longitude))) * 1000)
            as distance, radius, latitude, longitude,
            contracts.con_id, contracts.name, contracts.description, contracts.num_created, contracts.pic_location, 
            contracts.tradable, contracts.status, contracts.con_tx as con_hash,
            issuers.username as issuer_username, issuers.i_id
            FROM location_claim, contracts, issuers
            WHERE location_claim.con_id = contracts.con_id
            AND issuers.i_id = contracts.i_id
            GROUP BY location_claim.con_id
            ORDER BY distance ASC;
            """

        self.schema_out = GetProximityContracts()

        super().__init__()


class TradableTokenResponse(Schema):
    # Contract stuff.
    con_id = fields.Int(required=True)
    con_hash = fields.Str(required=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    num_created = fields.Int(required=True)
    pic_location = fields.Str(required=True)
    tradable = fields.Boolean(required=True)
    status = fields.Str(required=True)

    # Issuer stuff.
    issuer_username = fields.Str(required=True)
    i_id = fields.Int(required=True)

    # Collector Stuff
    collector_username = fields.Str(required=True)
    c_id = fields.Int(required=True)

    # Token Stuff
    t_id = fields.Int(required=True)

    @post_dump
    @post_load
    def add_picture_path(self, data):
        data['pic_location'] = request.url_root + 'contract/image=' + data['pic_location']

    doc_dump_info = {
        'con_id': '1', 'i_id': '2', 'con_hash': "", 'name': '', 'description': '', 'num_created': 20,
        'pic_location': 'url to pic', 'status': 'status of contract',
        'constraints': Constraints.doc_load_info
    }


class GetAllTradableContracts(DataQuery):

    def __init__(self, keyword=None):
        if keyword is not None:
            self.sql_text = """
            SELECT issuers.i_id, issuers.username as issuer_username,
            contracts.con_tx as con_hash, contracts.name, contracts.description, contracts.num_created,
            contracts.pic_location, contracts.tradable, contracts.status, issuers.username, contracts.con_id,
            tokens.t_id,
            collectors.username as 'collector_username', collectors.c_id
            FROM contracts, issuers, tokens, collectors
            WHERE contracts.i_id = issuers.i_id
            AND contracts.tradable = 1
            AND contracts.status = 'S'
            AND tokens.con_id = contracts.con_id
            AND tokens.status = 'S'
            AND tokens.owner_c_id notnull
            and tokens.owner_c_id = collectors.c_id
            AND (contracts.name like '%{keyword}%'
            OR contracts.description like '%{keyword}%');
            """.format(keyword=keyword)
        else:
            self.sql_text = """
            SELECT issuers.i_id, issuers.username as issuer_username,
            contracts.con_tx as con_hash, contracts.name, contracts.description, contracts.num_created,
            contracts.pic_location, contracts.tradable, contracts.status, issuers.username, contracts.con_id,
            tokens.t_id,
            collectors.username as 'collector_username', collectors.c_id
            FROM contracts, issuers, tokens, collectors
            WHERE contracts.i_id = issuers.i_id
            AND contracts.tradable = 1
            AND contracts.status = 'S'
            AND tokens.con_id = contracts.con_id
            AND tokens.status = 'S'
            AND tokens.owner_c_id notnull
            and tokens.owner_c_id = collectors.c_id;
            """
        self.schema_out = TradableTokenResponse()
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


class UpdateQRCODE(DataQuery):

    def __init__(self):
        self.sql_text = """
        UPDATE contracts
        SET qr_code_location = :qr_code_location
        WHERE con_id = :con_id;
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
