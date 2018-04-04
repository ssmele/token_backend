from marshmallow import Schema, fields


class TokenRequest(Schema):
    temp = fields.Str()
