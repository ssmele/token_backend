from collections import defaultdict

from marshmallow import Schema, fields, validate
from flask import g
from enum import Enum

from utils.db_utils import DataQuery


class TradeStatus(Enum):
    REQUESTED = 'R'
    ACCEPTED = 'A'
    INVALID = 'I'


class TradeItem(Schema):
    con_id = fields.Int(required=True)
    t_id = fields.Int(required=True)


class TradeInstance(Schema):
    c_id = fields.Int(required=True)
    offers = fields.Nested(TradeItem, many=True, required=True,
                           validate=validate.Length(min=1, error='Must contain one trade item.'))


class TradeRequest(Schema):
    trader = fields.Nested(TradeInstance, required=True)
    tradee = fields.Nested(TradeInstance, required=True)


def create_trade_request(tr):
    """
    Insert representation of trade into the database.
    :param tr: Trade information given by user.
    :return:
    """
    # Insert the base trade request.
    InsertTrade().execute({'trader_c_id' : tr['trader']['c_id'], 'tradee_c_id' : tr['tradee']['c_id']})
    tr_id = g.sesh.execute("select last_insert_rowid() as 'tr_id'").fetchone()['tr_id']

    # Insert trade items associated with trader.
    for trader_item in tr['trader']['offers']:
        trader_item.update({'tr_id': tr_id, 'owner': tr['trader']['c_id']})
        InsertTradeItem().execute(trader_item)

    # Insert trade items associated with tradee.
    for tradee_item in tr['tradee']['offers']:
        tradee_item.update({'tr_id': tr_id, 'owner': tr['tradee']['c_id']})
        InsertTradeItem().execute(tradee_item)


def get_trades(trader_c_id):
    return []


class InsertTrade(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO trade(trader_c_id, tradee_c_id)
        values (:trader_c_id, :tradee_c_id);
        """
        self.schema_out = None
        super().__init__()


class InsertTradeItem(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO trade_item(tr_id, con_id, t_id, owner)
        values (:tr_id, :con_id, :t_id, :owner);
        """
        self.schema_out = None
        super().__init__()


class GetTrades(DataQuery):

    def __init__(self):
        self.sql_text = """
        select trade_item.tr_id, trade_item.owner,
        contracts.con_id, contracts.name,
        tokens.t_id, tokens.owner_c_id
        from trade, trade_item, contracts, tokens
        where trade_item.tr_id in (select trade.tr_id from trade where trader_c_id = :c_id)
        and contracts.con_id = trade_item.con_id
        and tokens.t_id = trade_item.t_id
        and trade.tr_id = trade_item.tr_id
        and trade.status != 'I';
        """
        self.schema_out = None
        super().__init__()