from marshmallow import Schema, fields


class ExternalTransfer(Schema):
    con_id = fields.Int(required=True)
    t_id = fields.Int(required=True)
    destination_wallet_hash = fields.Str(required=True)