from marshmallow import Schema, fields


class CreateCollectorRequest(Schema):
    c_id = fields.Int(dump_only=True)
    username = fields.Str()
    password = fields.Str(load_only=True)


class CreateCollectorResponse(Schema):
    temp = fields.Str()
