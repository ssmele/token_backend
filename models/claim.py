from marshmallow import Schema, fields
from utils.db_utils import DataQuery
from models import db


class ClaimRequest(Schema):
    con_id = fields.Int(required=True)

    doc_load_info = {
        'con_id': {'type': 'int', 'desc': 'con_id of contract in which you want to claim a token from.'},
    }


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



class SetTokenIfOneAvailable(DataQuery):

    def __init__(self):
        self.sql_text = """
        UPDATE tokens
        SET owner_c_id = :c_id
        WHERE con_id = :con_id
        AND t_id = (SELECT t_id
                    FROM tokens
                    WHERE owner_c_id is NULL
                    AND con_id = :con_id
                    LIMIT 1);
        """

        self.schema_out = None
        super().__init__()


def claim_token_for_user(con_id, c_id):
    with db.engine.begin() as connection:
        have_token_already = DoesCollectorOwnToken().execute_n_fetchone({'con_id': con_id, 'c_id': c_id},
                                                                        con=connection,
                                                                        schema_out=False)
        if have_token_already:
            return None

        rows_updated = SetTokenIfOneAvailable().execute({'con_id': con_id, 'c_id': c_id}, con=connection)
        if rows_updated == 1:
            return True
        else:
            return None

