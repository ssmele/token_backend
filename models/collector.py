from marshmallow import Schema, fields


class CreateCollectorRequest(Schema):
    username = fields.Str()
    password = fields.Str(load_only=True)


class CreateCollectorResponse(Schema):
    temp = fields.Str()
