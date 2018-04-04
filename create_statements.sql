CREATE TABLE issuers (
  i_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username CHAR(50) NOT NULL
);
CREATE TABLE collectors (
  c_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username CHAR(50) NOT NULL
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
CREATE TABLE tokens (
  t_id INTEGER PRIMARY KEY AUTOINCREMENT,
  con_id INTEGER,
  hash TEXT NOT NULL,
  FOREIGN KEY (con_id) REFERENCES contracts(con_id)
);
CREATE TABLE  wallets (
  w_id INTEGER PRIMARY KEY AUTOINCREMENT,
  hash CHAR(42) NOT NULL CHECK(length(hash) == 42),
  priv_key TEXT NOT NULL
);



--collector stuff
insert into collectors (username) values('first collector');
select * from collectors;

--issuer stuff
insert into issuers (username) values('first issuer');
select * from issuers;

--contract stuff
INSERT into contracts (i_id, hash, name, description, num_created, claim_type)
    VALUES (1, 'HAHSHSSHSHS', 'First Token', 'This is the first Token', 69, 'L');
INSERT into contracts (i_id, hash, name, description, num_created, claim_type)
    VALUES (222, 'HAHSHSSHSHS', 'First Token', 'This is the first Token', 69, 'L');
select * from contracts;

--token stuff
insert into tokens (con_id, hash) VALUES (1, 'HAHSHSHSSH');
insert into tokens (con_id, hash) VALUES (33, 'HAHSHSHSSH');
select * from tokens;

--wallet stuff1
insert into wallets (hash, priv_key) VALUES ('0x12960e126E81B63b941636e83c7b30fC51aA689C', 'priv_key');
select * from wallets;



---Dangerous Queries be careful.----
delete from tokens;
delete from wallets;
drop table tokens;
drop table contracts;
drop table wallets;