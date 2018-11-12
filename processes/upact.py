#!/usr/bin/python
import sys

sys.path.insert(0, '/usr/apps/token/backend/backend/')
from utils.db_utils import DataQuery
from ether.geth_keeper import GethKeeper
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import create_engine
from utils.utils import log_kv, LOG_ERROR

# Create geth.
geth = GethKeeper()
print('running upact')

# Creating session for querying.
Session = sessionmaker()
engine = create_engine('sqlite:////usr/apps/token/backend/backend/temp.db')
Session.configure(bind=engine)


class UpdateContractStatus(DataQuery):
    """ Updates the status and address of a contract

    **binds**:
        * new_status: The status to update to
        * con_addr: The address of the contract
        * gas_cost: The gas_cost of the contract mine
        * this_id: The database's contract_id for this contract
    """

    def __init__(self):
        self.sql_text = """
            UPDATE contracts 
            SET status = :new_status, 
              con_addr = :con_addr,
              gas_cost = :gas_cost 
            WHERE con_id = :this_id;
        """
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


class UpdateTokenStatus(DataQuery):
    """ Updates the status and gas_cost of a token

    **binds**:
        * new_status: The new status of the token
        * gas_cost: The total gas consumed by the transaction
        * this_id: The ID of the token
    """

    def __init__(self):
        self.sql_text = """
            UPDATE tokens 
            SET status = :new_status, 
              gas_cost = :gas_cost 
            WHERE t_id = :this_id
        """
        super().__init__()


class GetPendingContracts(DataQuery):
    """ Gets all pending contracts """

    def __init__(self):
        self.sql_text = """
            SELECT con_id, con_tx 
            FROM contracts 
            WHERE status = 'P'
        """
        super().__init__()


class GetPendingTradeTRIDs(DataQuery):
    """
    Get all tr_ids of trade items in pending state.
    """

    def __init__(self):
        self.sql_text = """
        select * from trade
        where status = 'W'
        """
        super().__init__()


class GetTradeItemsByTRID(DataQuery):
    def __init__(self):
        self.sql_text = """
        select * from trade_item
        where tr_id = :tr_id
        """
        super().__init__()


# TODO: add this to the logic in the update trades.
class UpdateTradeItemGasCost(DataQuery):

    def __init__(self):
        self.sql_text = """
        UPDATE trade_item
        SET gas_cost = :gas_cost
        WHERE tr_id = :tr_id
        and con_id = :con_id
        and t_id = :t_id
        """
        super().__init__()


class UpdateTradeStatus(DataQuery):

    def __init__(self):
        self.sql_text = """
        UPDATE trade
        SET status = :new_status
        WHERE tr_id = :tr_id
        """
        super().__init__()


class GetPendingTokens(DataQuery):
    """ Gets all pending tokens """

    def __init__(self):
        self.sql_text = """
            SELECT t_id, t_hash 
            FROM tokens 
            WHERE status = 'P' 
              AND t_hash IS NOT NULL
        """
        super().__init__()


def update_contracts(rows, sess):
    """ Updates contract status and address if an issue has been processed. 'S' = Success, 'F' = Failure
    :param rows: The rows to iterate over
    :param sess: session to use.
    """
    for row in rows:
        print('working on contract - contract_id: {c_id}'.format(c_id=row['con_id']))
        # Try to get the transaction receipt
        has_receipt, success, receipt = geth.check_contract_mine(row['con_tx'])
        if has_receipt:
            status, address, gas_cost = 'F', None, None
            if success:
                status, address = 'S', receipt['contractAddress']
                gas_cost = receipt['gasUsed']
                print('Contract mined - contract_id: {c_id}'.format(c_id=row['con_id']))
            else:
                print('Contract failed!! - contract_id: {c_id}'.format(c_id=row['con_id']))
            # Update the status and contract address
            UpdateContractStatus().execute(
                {'new_status': 'S', 'con_addr': address, 'this_id': row['con_id'], 'gas_cost': gas_cost},
                sesh=sess)
    sess.commit()


def update_tokens(rows, sess):
    """ Updates token status if a claim has been processed. Sets status to 'S' on success or 'F' on failure

    :param rows: The rows to iterate over
    :param sess: session to use.
    """
    for row in rows:
        print('working on token - token_id: {t_id}'.format(t_id=row['t_id']))
        # Try to get the transaction receipt
        has_receipt, success, receipt = geth.check_claim_mine(row['t_hash'])
        if has_receipt:
            status = 'F'
            if success:
                status = 'S'
                gas_cost = receipt['gasUsed']
                print('Token claim mined - token_id: {t_id}, gas_used: {gas}'.format(t_id=row['t_id'], gas=gas_cost))
            else:
                gas_cost = None
                print('Token claim failed!! - token_id: {t_id}'.format(t_id=row['t_id']))
            # Update the status
            UpdateTokenStatus().execute({'new_status': status, 'gas_cost': gas_cost, 'this_id': row['t_id']}, sesh=sess)
    sess.commit()


def update_trade_items(trade_items, trade, sess):
    """
    Goes through and makes sure all trade_items given have been mined fully.
    :param trade_items: List of trade_item dictionary objects.
    :param trade: tr_id of trade.
    :return: list of booleans.
    """
    print("Working on trade_items in trade with tr_id: {}".format(trade['tr_id']))

    claimed = []
    gas_cost_list = []

    # Go through trade items and ensure they have been mined.
    for ti in trade_items:
        has_receipt, success, receipt = geth.check_claim_mine(ti['trade_hash'])
        if has_receipt:
            if success:
                # If they have been mined and success add to the list.
                gas_cost_list.append(receipt['gasUsed'])
                claimed.append(True)
            else:
                # If any of the tis fail. Then we need to fail the whole transfer and update the status.
                print('Trade_item mine fail. Failing whole transfer.-tr_id:{}, t_id:{}, con_id:{}'.format(ti['tr_id'],
                                                                                                          ti['t_id'],
                                                                                                          ti['con_id']))
                UpdateTradeStatus().execute({'tr_id': trade['tr_id'], 'new_status': 'F'})
        else:
            # If any fail then its over.
            claimed.append(False)
            break

    # Check to make sure all tokens have been mined.
    if all(claimed):
        try:
            perform_ownership_transfer(trade, trade_items, sess)
            UpdateTradeStatus().execute({'tr_id': trade['tr_id'], 'new_status': 'A'}, sesh=sess)
            for ti, gas_cost in zip(trade_items, gas_cost_list):
                UpdateTradeItemGasCost().execute({'gas_cost': gas_cost, 'tr_id': ti['tr_id'], 'con_id': ti['con_id'],
                                                  't_id': ti['t_id']}, sesh=sess)
            print('Trade transfer mined - tr_id: {tr_id}, gas_cost: {gas_cost_list}'
                  .format(tr_id=trade['tr_id'], gas_cost_list=gas_cost_list))
            sess.commit()
        except Exception as e:
            print('Exception while checking transfer mine: ERROR: {err}'.format(err=str(e)))
            log_kv(LOG_ERROR, {'error': 'exception while checking transfer mine', 'exception': str(e)},
                   exception=True)
            sess.rollback()
    else:
        print('Not all trade_items mined will try again later.'.format(t_id=trade['tr_id']))


def perform_ownership_transfer(trade, trade_items, sess):
    # Go through and transfer ownership over
    trader_c_id, tradee_c_id = trade['trader_c_id'], trade['tradee_c_id']
    for trade_item in trade_items:
        try:
            # Figure out new ownership.
            if trade_item['owner'] == trader_c_id:
                prev_owner, new_owner = trader_c_id, tradee_c_id
            else:
                prev_owner, new_owner = tradee_c_id, trader_c_id

            # Update the ownership.
            upt_cnt = UpdateOwnership().execute({'con_id': trade_item['con_id'], 't_id': trade_item['t_id'],
                                                 'new_owner': new_owner, 'prev_owner': prev_owner},
                                                sesh=sess)
            # Ensure that the ownership was actually updated.
            if upt_cnt != 1:
                log_kv(LOG_ERROR, {'error': 'error transferring token ownership',
                                   'con_id': trade_item['con_id'], 't_id': trade_item['t_id']})

        except Exception as e:
            log_kv(LOG_ERROR, {'error': 'error transferring ownership of token.',
                               'con_id': trade_item['con_id'], 't_id': trade_item['t_id'],
                               'owner_c_id': trade_item['owner'], 'exception': str(e)}, exception=True)
            sess.rollback()


def main():
    # Get contracts with pending status (for updating contracts)
    sess = Session()
    contract_rows = GetPendingContracts().execute_n_fetchall({}, sess, schema_out=False)
    if contract_rows:
        update_contracts(contract_rows, sess)
    sess.close()

    # Get tokens with pending status (for updating claimed tokens)
    sess = Session()
    token_rows = GetPendingTokens().execute_n_fetchall({}, sess, schema_out=False)
    if token_rows:
        update_tokens(token_rows, sess)
    sess.close()

    # Get pending trades.
    sess = Session()
    trades = GetPendingTradeTRIDs().execute_n_fetchall({}, sess, schema_out=False)
    for trade in trades:
        trade_items = GetTradeItemsByTRID().execute_n_fetchall({'tr_id': trade['tr_id']}, sess, schema_out=False)
        update_trade_items(trade_items, trade, sess)
    sess.close()


if __name__ == '__main__':
    main()
