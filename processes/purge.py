#!/usr/bin/python
import sys

sys.path.insert(0, '/usr/apps/token/backend/backend/')

from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import text

# Creating session for querying.
Session = sessionmaker()
engine = create_engine('sqlite:////usr/apps/token/backend/backend/temp.db')
Session.configure(bind=engine)


def purge():
    delete_sql = text("""
    delete from issuers;
    delete from collectors;
    delete from contracts;
    delete from unique_code_claim;
    delete from time_claim;
    delete from location_claim;
    delete from tokens;
    delete from trade;
    delete from trade_item;""")

    sess = Session()
    sess.execute(delete_sql, {})
    sess.commit()