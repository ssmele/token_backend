from marshmallow import Schema, fields


class ContractRequest(Schema):
    temp = fields.Str()
