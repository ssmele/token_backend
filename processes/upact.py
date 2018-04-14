from ether.geth_keeper import GethKeeper
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import create_engine


def update_contracts(rows, geth_keeper, session):
    for row in rows:
        addr = 2 # geth_keeper.check_contract_mine(row['con_tx'])
        if addr is None:
            continue

        r = session.execute("update contracts set status = :new_status where con_id = :this_id",
                         {'new_status': 'S', 'this_id': row['con_id']})
        if r.rowcount == 1:
            print("Updated ID ", row['con_id'])

    sess.commit()


def update_tokens(rows, geth_keeper, session):
    for row in rows:
        # TODO: check if token has finished being claimed before updating its status here
        r = sess.execute("update tokens set status = :new_status where t_id = :this_id",
                         {'new_status': 'S', 'this_id': row['t_id']})
        if r.rowcount == 1:
            print("Updated ID ", row['t_id'])

    sess.commit()


if __name__ == '__main__':

    # Create geth.
    geth = GethKeeper()

    # Creating session for querying.
    Session = sessionmaker()
    engine = create_engine('sqlite:///../temp.db')
    Session.configure(bind=engine)
    sess = Session()

    # Get contracts with pending status (for updating contracts)
    contract_rows = sess.execute("select con_id, con_tx from contracts where status = :desired_status",
                                 {'desired_status': 'P'})

    update_contracts(contract_rows, geth, sess)

    sess = Session()
    # Get tokens with pending status (for updating claimed tokens)
    token_rows = sess.execute("select t_id from tokens where status = :desired_status",
                                 {'desired_status': 'P'})

    update_tokens(token_rows, geth, sess)
    sess.close()