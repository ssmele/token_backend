from ether.geth_keeper import GethKeeper
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import create_engine

def update_contracts():
    pass


def update_tokens():
    pass


if __name__ == '__main__':

    # Create geth.
    geth = GethKeeper()

    # Creating session for querying.
    Session = sessionmaker()
    engine = create_engine('sqlite:///../temp.db')
    Session.configure(bind=engine)
    sess = Session()

    # EXAMPLE.
    # .execute() returns ROWPROXY from sqlalchemy.
    r = sess.execute("select * from collectors")
    #r = sess.exeucte("select * from collectors where status = :desired_status", {'desired_status': 'P'})

    update_contracts()
    update_tokens()