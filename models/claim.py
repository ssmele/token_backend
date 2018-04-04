from marshmallow import Schema, fields


class ClaimRequest(Schema):
    temp = fields.Str()
