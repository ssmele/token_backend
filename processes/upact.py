#!/usr/bin/python
import sys

sys.path.insert(0, '/usr/apps/token/backend/backend/')
from utils.db_utils import DataQuery
from ether.geth_keeper import GethKeeper
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import create_engine


class UpdateContractStatus(DataQuery):
    """ Updates the status and address of a contract

    **binds**:
        * new_status: The status to update to
        * con_addr: The address of the contract
        * this_id: The database's contract_id for this contract
    """

    def __init__(self):
        self.sql_text = """
            UPDATE contracts 
            SET status = :new_status, 
              con_addr = :con_addr 
            WHERE con_id = :this_id;
        """
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


def update_contracts(rows):
    """ Updates contract status and address if an issue has been processed. 'S' = Success, 'F' = Failure

    :param rows: The rows to iterate over
    """
    for row in rows:
        print('working on contract - contract_id: {c_id}'.format(c_id=row['con_id']))
        # Try to get the transaction receipt
        has_receipt, success, contract_addr = geth.check_contract_mine(row['con_tx'])
        if has_receipt:
            status, addr = 'F', None
            if success:
                status, addr = 'S', contract_addr
                print('Contract mined - contract_id: {c_id}'.format(c_id=row['con_id']))
            else:
                print('Contract failed!! - contract_id: {c_id}'.format(c_id=row['con_id']))
            # Update the status and contract address
            UpdateContractStatus().execute({'new_status': 'S', 'con_addr': addr, 'this_id': row['con_id']}, sesh=sess)
    sess.commit()


def update_tokens(rows):
    """ Updates token status if a claim has been processed. Sets status to 'S' on success or 'F' on failure

    :param rows: The rows to iterate over
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


if __name__ == '__main__':
    # Create geth.
    geth = GethKeeper()
    print('running upact')

    # Creating session for querying.
    Session = sessionmaker()
    engine = create_engine('sqlite:////usr/apps/token/backend/backend/temp.db')
    Session.configure(bind=engine)

    # Get contracts with pending status (for updating contracts)
    sess = Session()
    contract_rows = GetPendingContracts().execute_n_fetchall({}, sess, schema_out=False)
    if contract_rows:
        update_contracts(contract_rows)

    # Get tokens with pending status (for updating claimed tokens)
    token_rows = GetPendingTokens().execute_n_fetchall({}, sess, schema_out=False)

    if token_rows:
        update_tokens(token_rows)
    sess.close()
