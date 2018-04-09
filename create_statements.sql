CREATE TABLE issuers (
  i_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username CHAR(50) NOT NULL UNIQUE,
  password CHAR(50) NOT NULL
);
drop table collectors;
commit;
CREATE TABLE collectors (
  c_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username CHAR(50) NOT NULL UNIQUE ,
  password CHAR(50) NOT NULL
);
CREATE TABLE contracts (
  con_id INTEGER PRIMARY KEY AUTOINCREMENT,
  i_id INTEGER NOT NULL,
  hash TEXT NOT NULL,
  name CHAR(50) NOT NULL,
  description TEXT,
  num_created INTEGER NOT NULL,
  claim_type CHAR(1) NOT NULL,
  FOREIGN KEY(i_id) REFERENCES issuers(i_id)
);
DROP TABLE tokens;
CREATE TABLE tokens (
  t_id INTEGER PRIMARY KEY AUTOINCREMENT,
  con_id INTEGER,
  hash TEXT NOT NULL,
  owner_c_id INTEGER,
  FOREIGN KEY (owner_c_id) REFERENCES issuers(i_id),
  FOREIGN KEY (con_id) REFERENCES contracts(con_id)
);
CREATE TABLE  wallets (
  w_id INTEGER PRIMARY KEY AUTOINCREMENT,
  hash CHAR(42) NOT NULL CHECK(length(hash) == 42),
  priv_key TEXT NOT NULL
);