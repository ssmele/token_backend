from marshmallow import Schema, fields


class CreateIssuerRequest(Schema):
    username = fields.Str()
    password = fields.Str(load_only=True)


class CreateIssuerResponse(Schema):
    issuer_id = fields.Str()
