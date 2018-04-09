from marshmallow import fields
from models.contract import GetContractResponse


class TokenResponse(GetContractResponse):
    t_id = fields.Int(required=True)
    con_id = fields.Int(required=True)
    t_hash = fields.Str(required=True)

