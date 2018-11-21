CREATE TABLE issuers (
  i_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username CHAR(50) NOT NULL UNIQUE,
  password CHAR(50) NOT NULL,
  creation_ts DATE DEFAULT  (strftime('%Y-%m-%d %H:%M:%S')),
  i_hash VARCHAR(42) NOT NULL,
  i_priv_key TEXT NOT NULL
);
CREATE TABLE collectors (
  c_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username CHAR(50) NOT NULL UNIQUE ,
  password CHAR(50) NOT NULL,
  creation_ts DATE DEFAULT  (strftime('%Y-%m-%d %H:%M:%S')),
  c_hash VARCHAR(42) NOT NULL,
  c_priv_key TEXT NOT NULL
);

CREATE TABLE contracts (
  con_id INTEGER PRIMARY KEY AUTOINCREMENT,
  i_id INTEGER NOT NULL,
  con_tx TEXT NOT NULL,
  con_addr TEXT,
  con_abi BLOB NOT NULL,
  name CHAR(50) NOT NULL,
  description TEXT,
  tradable BOOLEAN NOT NULL DEFAULT true,
  num_created INTEGER NOT NULL,
  qr_code_claimable BOOLEAN NOT NULL DEFAULT false,
  pic_location varchar(35) NOT NULL,
  creation_ts DATE DEFAULT (strftime('%Y-%m-%d %H:%M:%S')),
  status CHAR(1) NOT NULL DEFAULT 'P',
  gas_price FLOAT,
  gas_cost FLOAT,
  metadata_location VARCHAR(64) NOT NULL DEFAULT '',
  FOREIGN KEY(i_id) REFERENCES issuers(i_id)
);

CREATE TABLE location_claim(
  lc_id INTEGER PRIMARY KEY AUTOINCREMENT,
  con_id INTEGER,
  latitude DECIMAL(8,6),
  longitude DECIMAL(9,6),
  radius REAL,
  FOREIGN KEY (con_id) REFERENCES contracts(con_id)
);

CREATE TABLE time_claim(
  tc_id INTEGER PRIMARY KEY AUTOINCREMENT,
  con_id INTEGER,
  start DATE NOT NULL ,
  end DATE NOT NULL ,
  FOREIGN KEY (con_id) REFERENCES contracts(con_id)
);

CREATE TABLE unique_code_claim(
  uc_id INTEGER PRIMARY KEY AUTOINCREMENT,
  con_id INTEGER,
  code TEXT,
  FOREIGN KEY (con_id) REFERENCES contracts(con_id)
);

CREATE TABLE tokens (
  t_id INTEGER PRIMARY KEY AUTOINCREMENT,
  con_id INTEGER,
  t_hash TEXT NOT NULL,
  owner_c_id INTEGER,
  claim_ts DATE,
  qr_code_location varchar(65) NOT NULL default '',
  gas_price FLOAT,
  gas_cost FLOAT,
  latitude DECIMAL(8,6),
  longitude DECIMAL(9,6),
  status CHAR(1) NOT NULL DEFAULT 'N',
  FOREIGN KEY (owner_c_id) REFERENCES collectors(c_id),
  FOREIGN KEY (con_id) REFERENCES contracts(con_id)
);
CREATE TABLE  wallets (
  w_id INTEGER PRIMARY KEY AUTOINCREMENT,
  hash CHAR(42) NOT NULL CHECK(length(hash) == 42),
  priv_key TEXT NOT NULL
);



CREATE TABLE trade (
tr_id INTEGER  PRIMARY KEY AUTOINCREMENT,
trader_c_id INTEGER NOT NULL,
tradee_c_id INTEGER NOT NULL,
trader_eth_offer FLOAT DEFAULT 0.0,
tradee_eth_offer FLOAT DEFAULT 0.0,
status CHAR(1) NOT NULL DEFAULT 'R',
creation_ts DATE DEFAULT  (strftime('%Y-%m-%d %H:%M:%S')),
FOREIGN KEY (trader_c_id) REFERENCES collectors(c_id),
FOREIGN KEY (tradee_c_id) REFERENCES collectors(c_id)
);

CREATE TABLE trade_item (
tr_id INTEGER,
con_id INTEGER,
t_id INTEGER,
owner INTEGER,
trade_hash TEXT,
gas_price FLOAT,
gas_cost FLOAT,
FOREIGN KEY (tr_id) REFERENCES trade(tr_id),
FOREIGN KEY (con_id) REFERENCES contracts(con_id),
FOREIGN KEY (t_id) REFERENCES tokens(t_id),
FOREIGN KEY (owner) REFERENCES collectors(c_id)
);