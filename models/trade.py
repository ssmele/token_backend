from marshmallow import Schema, fields, validate
from flask import g
from enum import Enum

from ether.geth_keeper import GethException
from utils.db_utils import DataQuery
from utils.utils import log_kv, LOG_INFO

from models.collector import TokenResponse, CollectorInfoRequest


class TradeStatus(Enum):
    REQUESTED = 'R'
    ACCEPTED = 'A'
    DECLINED = 'D'
    CANCELED = 'C'
    INVALID = 'I'


class DeleteTradeRequest(Schema):
    tr_id = fields.Int(required=True)

    doc_load_info = {'tr_id': 'integer (tr_id of trade request to delete).'}


class TradeResponseRequest(Schema):
    tr_id = fields.Int(required=True)
    accept = fields.Boolean(required=True)

    doc_load_info = {'tr_id': 'integer (tr_id of trade request to respond to)',
                     'accept': 'Boolean (True if accept, false if decline)'}


class TradeItem(Schema):
    con_id = fields.Int(required=True)
    t_id = fields.Int(required=True)


class TradeResponseInstance(Schema):
    collector = fields.Nested(CollectorInfoRequest, required=True)
    eth_offer = fields.Float(default=0.0)
    offers = fields.Nested(TokenResponse, many=True, required=True,
                           validate=validate.Length(min=1, error='Must contain one trade item.'))


class TradeResponse(Schema):
    trader = fields.Nested(TradeResponseInstance, required=True)
    tradee = fields.Nested(TradeResponseInstance, required=True)
    status = fields.Str(required=True)
    tr_id = fields.Int(required=True)


class TradeInstance(Schema):
    c_id = fields.Int(required=True)
    eth_offer = fields.Float(default=0.0)
    offers = fields.Nested(TradeItem, many=True, required=True,
                           validate=validate.Length(min=1, error='Must contain one trade item.'))


class TradeRequest(Schema):
    trader = fields.Nested(TradeInstance, required=True)
    tradee = fields.Nested(TradeInstance, required=True)

    doc_load_info = {'trader': {'c_id': 'c_id of collector issuing trade.',
                                'eth_offer': 'number of eth.',
                                'offers': [{'con_id': 'con_id of contract to trade.',
                                            't_id': 't_id of token to trade.'}]},
                     'tradee': {'c_id': 'c_id of collector issuer of trade is trying to trade with.',
                                'eth_offer': 'number of eth.',
                                'offers': [{'con_id': 'con_id of contract to trade.',
                                            't_id': 't_id of token to trade.'}]}}


def check_active_trade_item(c_id, con_id, t_id):
    """
    Checks to see user already has an active trade containing token.
    :param c_id: c_id of collector who's trades to look at.
    :param con_id: contract token should be under.
    :param t_id: token to see if active.
    :return: Boolean representing tokens active status in another trade.
    """
    if CheckActiveTradeItem().execute_n_fetchone({'c_id': c_id, 'con_id': con_id, 't_id': t_id}, schema_out=False):
        return True
    else:
        return False


def check_trade_item_ownership(c_id, con_id, t_id):
    """
    This method checks to ensure given c_id own s a token with a given con_id,
    and t_id.
    :param c_id: c_id of collector to ensure has ownership.
    :param con_id: con_id that token should be under.
    :param t_id: t_id that the collector should have ownership over.
    :return: Boolean that represents ownership status.
    """
    if CheckOwnership().execute_n_fetchone({'c_id': c_id, 'con_id': con_id, 't_id': t_id}, schema_out=False):
        return True
    else:
        return False


def create_trade_request(tr):
    """
    Insert representation of trade into the database.
    :param tr: Trade information given by user.
    :return:
    """
    # Insert the base trade request.
    InsertTrade().execute({'trader_c_id': tr['trader']['c_id'], 'tradee_c_id': tr['tradee']['c_id'],
                           'trader_eth_offer': tr['trader']['eth_offer'],
                           'tradee_eth_offer': tr['tradee']['eth_offer']})
    tr_id = g.sesh.execute("select last_insert_rowid() as 'tr_id'").fetchone()['tr_id']

    # Insert trade items associated with trader.
    for trader_item in tr['trader']['offers']:
        trader_item.update({'tr_id': tr_id, 'owner': tr['trader']['c_id']})
        InsertTradeItem().execute(trader_item)

    # Insert trade items associated with tradee.
    for tradee_item in tr['tradee']['offers']:
        tradee_item.update({'tr_id': tr_id, 'owner': tr['tradee']['c_id']})
        InsertTradeItem().execute(tradee_item)

    return tr_id


def is_valid_trade_items(trade_items):
    """
    Go through each trade item and ensure that the owners of the tokens are the same when the initial trade was
    invoked.
    :param trade_items: list of trade_item db records.
    :return: Boolean representing validity of trade.
    """
    # TODO: ADD ETHEREUM VERIFICATION HERE.
    # Go through each token and ensure it is owned by the correct collector.
    for trade_item in trade_items:

        # If we find a token in which the owner has changed then we have found an invalid trade request.
        if not check_trade_item_ownership(trade_item['owner'], trade_item['con_id'], trade_item['t_id']):
                log_kv(LOG_INFO, {'info': 'Owner of token has changed',
                                  'previous_owner_c_id': trade_item['owner'], 'con_id': trade_item['con_id'],
                                  't_id': trade_item['t_id']})

                return False

    return True


def validate_offer_and_trade(trade_items, tradee_id, trader_id, trader_eth_offer):
    """ Validate each item in trade_items is correctly owned on the ethereum network and once they are
    approved then perform the transfers.

    :param trade_items: The array of items up for trade
    :param tradee_id: The id of the tradee
    :param trader_id: The id of the trader
    :param trader_eth_offer: The amount of eth being offered
    """
    # TODO: Get estimated gas cost so we can validate there is enough for the transfers!!!

    # Get the account information for both the tradee and trader
    tradee_info = GetTraderInfo().execute_n_fetchone({'c_id': tradee_id}, schema_out=False)
    trader_info = GetTraderInfo().execute_n_fetchone({'c_id': trader_id}, schema_out=False)
    if not tradee_info or not trader_info:
        raise GethException('', message='Could not get either tradee or trader information')

    tradee_acct, tradee_key = tradee_info['address'], tradee_info['priv_key']
    trader_acct, trader_key = trader_info['address'], trader_info['priv_key']

    # Validate the eth offer
    if trader_eth_offer:
        balance = g.geth.get_eth_balance(trader_acct)
        if balance <= trader_eth_offer:
            raise GethException('', message='Trader does not have enough eth to cover the trade')

    # Validate the token offers and store them for the final transferring
    transfers = []
    for item in trade_items:
        acct, key = (tradee_acct, tradee_key) if item['owner'] == tradee_id else (trader_acct, trader_key)
        to_acct = tradee_acct if acct != tradee_acct else trader_acct
        contract_info = GetContractInfo().execute_n_fetchone({'t_id': item['t_id']}, schema_out=False)
        if not contract_info:
            raise GethException('', message='Could not get contract info for token_id {t_id}'.format(t_id=item['t_id']))

        # Get the contract addr and abi and make sure the account owns the token
        con_addr, con_abi = contract_info['addr'], contract_info['abi']
        owner = g.geth.get_user_from_token_id(con_addr, con_abi, item['t_id'])
        if acct.upper() != owner.upper():
            raise GethException('', message='Account {acct} does not own token {t_id}'
                                .format(acct=acct, t_id=item['t_id']))

        # Save the transfer for later
        transfers.append({
            'to': to_acct,
            'from': acct,
            'key': key,
            'con_addr': con_addr,
            'con_abi': con_abi,
            'token_id': item['t_id']
        })

    # Perform the eth transfer
    if trader_eth_offer:
        try:
            g.geth.send_eth(trader_eth_offer, src_acct=trader_acct, dest_acct=tradee_acct, src_priv_key=trader_key)
        except Exception as e:
            raise GethException(str(e), message='Could not perform ethereum trade')

    # Perform the token transfers
    for transfer in transfers:
        try:
            g.geth.perform_transfer(transfer['con_addr'], transfer['con_abi'], transfer['token_id'],
                                    src_acct=transfer['from'], dest_acct=transfer['to'],
                                    src_priv_key=transfer['key'])
        except Exception as e:
            raise GethException(str(e), message='Could not perform token transfer for token_id {t_id}'
                                .format(t_id=transfer['token_id']))


class GetContractInfo(DataQuery):

    def __init__(self):
        self.sql_text = """
            SELECT c.con_abi AS abi, c.con_addr AS addr
            FROM contracts c, tokens t
            WHERE c.con_id = t.con_id
              AND t.t_id = :t_id;
        """
        self.schema_out = None
        super().__init__()


class GetTraderInfo(DataQuery):

    def __init__(self):
        self.sql_text = """
            SELECT c_hash AS address, c_priv_key AS priv_key
            FROM collectors 
            WHERE c_id = :c_id;
        """
        self.schema_out = None
        super().__init__()


class GetTradeItems(DataQuery):

    def __init__(self):
        self.sql_text = """
        select * from trade_item where tr_id = :tr_id;
        """
        self.schema_out = None
        super().__init__()


class CheckActiveTradeItem(DataQuery):

    def __init__(self):
        self.sql_text = """
        select * from trade_item, trade
        where trade_item.tr_id = trade.tr_id
        and status = '{}'
        and trader_c_id = :c_id
        and con_id = :con_id
        and t_id = :t_id
        and owner = :c_id;
        """.format(TradeStatus.REQUESTED.value)
        self.schema_out = None
        super().__init__()


class CheckOwnership(DataQuery):

    def __init__(self):
        self.sql_text = """
        select * from tokens 
        where t_id = :t_id
        and owner_c_id = :c_id
        and con_id = :con_id
        and status = 'S'
        """
        self.schema_out = None
        super().__init__()


class InsertTrade(DataQuery):

    def __init__(self):
        self.sql_text = """
        INSERT INTO trade(trader_c_id, tradee_c_id, trader_eth_offer, tradee_eth_offer)
        values (:trader_c_id, :tradee_c_id, :trader_eth_offer, :tradee_eth_offer);
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


class GetTradeByTRID(DataQuery):

    def __init__(self):
        self.sql_text = """
        select * from trade
        where trade.tr_id = :tr_id
        """
        self.schema_out = None
        super().__init__()


class UpdateTradeStatus(DataQuery):

    def __init__(self):
        self.sql_text = """
        update trade
        set status = :new_status
        where trade.tr_id = :tr_id;
        """
        self.schema_out = None
        super().__init__()


class InvalidateTradeRequests(DataQuery):

    def __init__(self):
        self.sql_text = """
        update trade
        set status = 'I'
        where trade.tr_id  in (select trd.tr_id from trade trd, trade_item
                                                where trd.tr_id = trade_item.tr_id
                                                and trade_item.t_id = :t_id
                                                and trade_item.con_id = :con_id
                                                and trd.status = 'R');
        """
        self.schema_out = None
        super().__init__()


class GetActiveTradeRequests(DataQuery):

    def __init__(self, version):
        if version == 'tradee':
            self.sql_text = """
            select tr_id from trade 
            where tradee_c_id = :c_id
            and status in ('R', 'A');
            """
        elif version == 'trader':
            self.sql_text = """
            select tr_id from trade 
            where trader_c_id = :c_id
            and status in ('R', 'A');
            """
        else:
            self.sql_text = """
            select tr_id from trade 
            where (trader_c_id = :c_id
            or tradee_c_id = :c_id)
            and status in ('R', 'A');
            """
        self.schema_out = None
        super().__init__()


class UpdateOwnership(DataQuery):

    def __init__(self):
        self.sql_text = """
        update tokens
        set owner_c_id = :new_owner
        where con_id = :con_id
        and t_id = :t_id
        and owner_c_id = :prev_owner;
        """
        self.schema_out = None
        super().__init__()


class GetUntradables(DataQuery):

    def __init__(self):
        self.sql_text = """
        select con_id from contracts 
        where con_id in (:con_ids)
        and tradable = 0;
        """
        self.schema_out = None
        super().__init__()


class GetTokenInfo(DataQuery):

    def __init__(self):
        self.sql_text = """
        SELECT  contracts.con_id, issuers.i_id, issuers.username as issuer_username, contracts.con_tx as con_hash,
                contracts.name, contracts.description, contracts.num_created, contracts.pic_location, contracts.tradable,
                contracts.status, tokens.t_id, tokens.t_hash, tokens.owner_c_id
        FROM tokens, contracts, issuers
        WHERE tokens.t_id = :t_id
        AND contracts.con_id = :con_id
        AND contracts.con_id = tokens.con_id
        AND contracts.i_id = issuers.i_id;
        """

        self.schema_out = TokenResponse()
        super().__init__()