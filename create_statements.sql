CREATE TABLE issuers (
  i_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username CHAR(50) NOT NULL UNIQUE,
  password CHAR(50) NOT NULL,
  i_hash VARCHAR(42) NOT NULL,
  i_priv_key TEXT NOT NULL
);
CREATE TABLE collectors (
  c_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username CHAR(50) NOT NULL UNIQUE ,
  password CHAR(50) NOT NULL,
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
  num_created INTEGER NOT NULL,
  claim_type CHAR(1) NOT NULL,
  pic_location varchar(35) NOT NULL,
  status CHAR(1) NOT NULL DEFAULT 'P',
  FOREIGN KEY(i_id) REFERENCES issuers(i_id)
);

CREATE TABLE location_claim(
  lc_id INTEGER PRIMARY KEY AUTOINCREMENT,
  con_id INTEGER,
  latitude REAL,
  longitude REAL,
  radius REAL,
  FOREIGN KEY (con_id) REFERENCES contracts(con_id)
)

CREATE TABLE time_claim(
  tc_id INTEGER PRIMARY KEY AUTOINCREMENT,
  con_id INTEGER,
  start TEXT,
  end TEXT,
  FOREIGN KEY (con_id) REFERENCES contracts(con_id)
)

CREATE TABLE unique_code_claim(
  uc_id INTEGER PRIMARY KEY AUTOINCREMENT,
  con_id INTEGER,
  unique_code TEXT,
  FOREIGN KEY (con_id) REFERENCES contracts(con_id)
)

CREATE TABLE tokens (
  t_id INTEGER PRIMARY KEY AUTOINCREMENT,
  con_id INTEGER,
  t_hash TEXT NOT NULL,
  owner_c_id INTEGER,
  status CHAR(1) NOT NULL DEFAULT 'N',
  FOREIGN KEY (owner_c_id) REFERENCES collectors(c_id),
  FOREIGN KEY (con_id) REFERENCES contracts(con_id)
);
CREATE TABLE  wallets (
  w_id INTEGER PRIMARY KEY AUTOINCREMENT,
  hash CHAR(42) NOT NULL CHECK(length(hash) == 42),
  priv_key TEXT NOT NULL
);
