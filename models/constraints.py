from datetime import datetime

import mpu
from marshmallow import Schema, fields, pre_dump
from marshmallow.validate import ValidationError

from utils.db_utils import DataQuery

CONSTRAINT_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
CODE_LENGTH = 6


class ConstraintBase(Schema):
    con_id = fields.Int(required=True)


def validate_code(code):
    if not code.isalnum():
        raise ValidationError('Code must be alphanumeric.')

    if len(code) != CODE_LENGTH:
        raise ValidationError('Code must be exactly 6')


class UniqueCodeConstraint(ConstraintBase):
    uc_id = fields.Int(required=True)
    code = fields.Str(required=True, validate=validate_code)


class TimeConstraint(ConstraintBase):
    tc_id = fields.Int(required=True)
    start = fields.DateTime(CONSTRAINT_DATETIME_FORMAT, required=True)
    end = fields.DateTime(CONSTRAINT_DATETIME_FORMAT, required=True)

    # Need this or parsing issue occurs during database queries with results that contain Scheme.
    @pre_dump
    def handle_datetime(self, data):
        data['start'] = datetime.strptime(data['start'], CONSTRAINT_DATETIME_FORMAT)
        data['end'] = datetime.strptime(data['end'], CONSTRAINT_DATETIME_FORMAT)


class LocationConstraint(ConstraintBase):
    lc_id = fields.Int(required=True)
    latitude = fields.Number(required=True)
    longitude = fields.Number(required=True)
    radius = fields.Number(required=True)


class Constraints(Schema):
    code_constraints = fields.Nested(UniqueCodeConstraint, only=['code'], required=False, many=True)
    time_constraints = fields.Nested(TimeConstraint, only=['start', 'end'], required=False, many=True)
    location_constraints = fields.Nested(LocationConstraint, only=['latitude', 'longitude', 'radius'],
                                         required=False, many=True)

    doc_load_info = {'code_constraints': [{'code': '123ABC (LENGTH 6 ALPANUMERIC CODE)'}],
                     'time_constraints': [{"start": "2014-12-22 03:12:58",
                                           "end": "2018-12-22 03:12:58"}],
                     'location_constraints': [{"latitude": 40.7607793,
                                               "longitude": -111.8910474,
                                               "radius": 1000}]}


class GetUniqueCodeConstraints(DataQuery):

    def __init__(self):
        self.sql_text = """
        select * 
        from unique_code_claim
        where con_id = :con_id
        """
        self.schema_out = UniqueCodeConstraint()
        super().__init__()


class GetTimeConstraints(DataQuery):

    def __init__(self):
        self.sql_text = """
        select con_id, tc_id, start, end
        from time_claim 
        where con_id = :con_id
        """
        self.schema_out = TimeConstraint()
        super().__init__()


class GetLocationConstraints(DataQuery):

    def __init__(self):
        self.sql_text = """
        select * 
        from location_claim 
        where con_id = :con_id
        """
        self.schema_out = LocationConstraint()
        super().__init__()


class InsertUniqueCodeConstraint(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO unique_code_claim(con_id, unique_code) values(:con_id, :code);
        """

        self.schema_out = None
        super().__init__()


class InsertLocationConstraint(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO location_claim (con_id, latitude, longitude, radius) 
        values(:con_id, :latitude, :longitude, :radius);
        """

        self.schema_out = None
        super().__init__()


class InsertTimeConstraint(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO time_claim(con_id, start, end) values(:con_id, :start, :end) 
        """

        self.schema_out = None
        super().__init__()


def validate_uni_code_constraints(con_id, code):
    """
    This method validates that the collector has one of the unique codes required to claim this token.
    :param con_id: con_id of contract to check constraints against.
    :param code: code given by collector.
    :return: Boolean if validation is successful
    """
    # Get all possible unique code constraints
    ucs = GetUniqueCodeConstraints().execute_n_fetchall({'con_id': con_id})

    # If there are not codes associated with this contract then we are good.
    if len(ucs) == 0:
        return True

    # If we found codes and their is no codes given then we automatically fail validation.
    if code is None:
        return False

    # Go through and see if our code matches any.
    valid_codes = next((t for t in ucs if code == t['code']), None)
    if valid_codes:
        return True
    else:
        return False


def validate_time_constraints(con_id, time):
    """
    This method validates that the collector is attempting a claim at a valid time.
    :param con_id: con_id of contract to check constraints against.
    :param time: time of attempted claim.
    :return: Boolean if validation is successful
    """
    # Get all possible time constraints.
    time_constraints = GetTimeConstraints().execute_n_fetchall({'con_id': con_id}, load_out=True)

    if len(time_constraints) == 0:
        return True

    if time is None:
        return False

    # Go through and see if we find one. # BEAUTIFUL FIRST MATCH EXPRESSION.
    valid_times = next((t for t in time_constraints if t['start'] < time < t['end']), None)
    if valid_times:
        return True
    else:
        return False


def validate_location_constraints(con_id, loc_constraint):
    """
    This method validates that the given location is near enough one of the location constraints.
    :param con_id: con_id of contract to check constraints against.
    :param loc_constraint: location of collector
    :return: Boolean if validation is successful
    """
    # Get all possible location constraints.
    location_constraints = GetLocationConstraints().execute_n_fetchall({'con_id': con_id})

    if len(location_constraints) == 0:
        return True

    if not loc_constraint:
        return False

    # See if find a match.
    valid_locations = next((l for l in location_constraints if near_enough(l['latitude'], l['longitude'],
                                                                           loc_constraint['latitude'],
                                                                           loc_constraint['longitude'],
                                                                           l['radius'])),
                           None)
    if valid_locations:
        return True
    else:
        return False


def near_enough(dest_lat, dest_long, g_lat, g_long, radius):
    """
    Takes the distance between two pairs of latitude, and longitude to see if they are close enough together.
    :param dest_lat: lat of one pair.
    :param dest_long: long of one pair.
    :param g_lat: lat of another pair.
    :param g_long: long of another pair.
    :param radius: maximum distance between the two points for them to be considered near.
    :return: Boolean
    """
    if mpu.haversine_distance((dest_lat, dest_long), (g_lat, g_long)) <= radius:
        return True
    else:
        return False


def get_all_constraints(con_id):
    """
    This method gets all the constraints associated with a given contract.
    :param con_id: con_id to identify the contract.
    :return: a python dictionary of the constraints.
    """
    ucs = GetUniqueCodeConstraints().execute_n_fetchall({'con_id': con_id})
    time_constraints = GetTimeConstraints().execute_n_fetchall({'con_id': con_id})
    location_constraints = GetLocationConstraints().execute_n_fetchall({'con_id': con_id})

    return Constraints().dump({'location_constraints': location_constraints,
                               'time_constraints': time_constraints,
                               'code_constraints': ucs})