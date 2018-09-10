from marshmallow import Schema, fields
from marshmallow.validate import ValidationError

from utils.db_utils import DataQuery


class ConstraintBase(Schema):
    con_id = fields.Int(required=True)


# TODO: Need to move this so it also validates the input.
CODE_LENGTH = 6


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
    start = fields.DateTime(required=True)
    end = fields.DateTime(required=True)


class LocationConstraint(ConstraintBase):
    lc_id = fields.Int(required=True)
    latitude = fields.Number(required=True)
    longitude = fields.Number(required=True)


class Constraints(Schema):
    code_constraints = fields.Nested(UniqueCodeConstraint, only=['code'], required=False, many=True)
    time_constraints = fields.Nested(TimeConstraint, only=['start', 'end'], required=False, many=True)
    location_constraints = fields.Nested(LocationConstraint, only=['latitude', 'longitude'], required=False, many=True)


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
        select * 
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


def validate_uni_code_constraints(con_id, code):
    # Get all possible unique code constraints
    ucs = GetUniqueCodeConstraints().execute_n_fetchall({'con_id': con_id})

    # If there are not codes associated with this contract then we are good.
    if len(ucs) == 0:
        return True

    # Go through and see if our code matches any.
    valid_codes = next((t for t in ucs if code == t['code']), None)
    if valid_codes:
        return True
    else:
        return False


def validate_time_constraints(con_id, time):
    # Get all possible time constraints.
    time_constraints = GetTimeConstraints().execute_n_fetch_all({'con_id': con_id})

    if len(time_constraints) == 0:
        return True

    # Go through and see if we find one. # BEAUTIFUL FIRST MATCH EXPRESSION.
    valid_times = next((t for t in time_constraints if t.start < time > t.end), None)
    if valid_times:
        return True
    else:
        return False


def validate_location_constraints(con_id, lat, long):
    # Get all possible location contraints.
    location_constraints = GetLocationConstraints().execute_n_fetch_all({'con_id': con_id})

    if len(location_constraints) == 0:
        return True

    # See if find a match.
    valid_locations = next((l for l in location_constraints if near_enough(l.longitude, l.latitude, lat, long)), None)

    if valid_locations:
        return True
    else:
        return False


def near_enough(dest_long, dest_lat, g_lat, g_long):
    pass
