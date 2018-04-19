#!/usr/bin/python
from ether.geth_keeper import GethKeeper
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import create_engine


def update_contracts(rows, session):
    """ Updates contract status and address if an issue has been processed. 'S' = Success, 'F' = Failure

    :param rows: The rows to iterate over
    :param session: The database object to use
    """
    for row in rows:
        print('working on {c_id}'.format(c_id=row['con_id']))
        # Try to get the transaction receipt
        has_receipt, success, contract_addr = geth.check_contract_mine(row['con_tx'])
        if has_receipt:
            status, addr = 'F', None
            if success:
                status, addr = 'S', contract_addr
            # Update the status and contract address
            session.execute("update contracts set status = :new_status, con_addr = :con_addr where con_id = :this_id",
                                {'new_status': 'S', 'con_addr': addr, 'this_id': row['con_id']})
    sess.commit()


def update_tokens(rows, session):
    """ Updates token status if a claim has been processed. Sets status to 'S' on success or 'F' on failure

    :param rows: The rows to iterate over
    :param session: The database session object to use
    """
    for row in rows:
        print('working on {t_id}'.format(t_id=row['t_id']))
        # Try to get the transaction receipt
        has_receipt, success = geth.check_claim_mine(row['t_hash'])
        if has_receipt:
            status = 'F'
            if success:
                status = 'S'
            # Update the status
            session.execute("update tokens set status = :new_status where t_id = :this_id",
                            {'new_status': status, 'this_id': row['t_id']})
    sess.commit()


if __name__ == '__main__':
    # Create geth.
    geth = GethKeeper()
    print('running upact')

    # Creating session for querying.
    Session = sessionmaker()
    engine = create_engine('sqlite:///../temp.db')
    Session.configure(bind=engine)

    # Get contracts with pending status (for updating contracts)
    sess = Session()
    contract_rows = sess.execute("select con_id, con_tx from contracts where status = 'P'")
    update_contracts(contract_rows, sess)

    # Get tokens with pending status (for updating claimed tokens)
    sess = Session()
    token_rows = sess.execute("select t_id from tokens where status = 'P' and t_hash is not NULL")
    update_tokens(token_rows, sess)
    sess.close()
