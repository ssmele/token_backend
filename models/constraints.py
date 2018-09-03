from marshmallow import Schema, fields

from utils.db_utils import DataQuery


class ConstraintBase(Schema):
    con_id = fields.Int(required=True)


class UniqueCodeConstraint(ConstraintBase):
    uc_id = fields.Int(required=True)
    unique_code = fields.Str(required=True)

class TimeConstraint(ConstraintBase):
    tc_id = fields.Int(required=True)
    start = fields.DateTime(required=True)
    end = fields.DateTime(required=True)

class LocationConstraint(ConstraintBase):
    lc_id = fields.Int(required=True)
    latitude = fields.Number(required=True)
    longitude = fields.Numer(required=True)

class ValidateUniqueCodeConstraint(DataQuery):

    def __init__(self):
        self.sql_text = """
        select * 
        from unique_code_claim
        where cod_id = :con_id
        and unique_code = :unique_code
        """
        self.schema_out = UniqueCodeConstraint()
        super().__init__()

class GetTimeConstraints():

    def __init__(self):
        self.sql_text = """
        select * 
        from time_claim 
        where con_id = :con_id
        """
        self.schema_out  = TimeConstraint()
        super().__init__()

class GetLocationConstraints():

    def __init__(self):
        self.sql_text = """
        select * 
        from location_claim 
        where con_id = :con_id
        """
        self.schema_out  = LocationConstraint()
        super().__init__()

def validate_time_constraints(con_id, time):
    # Get all possible time constraints.
    time_constraints = GetTimeConstraints().execute_n_fetch_all({'con_id': con_id})

    # Go through and see if we find one. # BEAUTIFUL FIRST MATCH EXPRESSION.
    valid_times = next((t for t in time_constraints if t.start < time >  t.end ), None)
    if valid_times:
        return True
    else:
        return False

def validate_location_constraints(con_id, lat, long):
    # Get all possible location contraints.
    location_constraints = GetLocationConstraints().execute_n_fetch_all({'con_id': con_id})

    # See if find a match.
    valid_locations = next((l for l in location_constraints if near_enough(l.longitude, l.latitude, lat, long)), None)

    if valid_locations:
        return True
    else:
        return False

def near_enough(dest_long, dest_lat, g_lat, g_long):
    pass