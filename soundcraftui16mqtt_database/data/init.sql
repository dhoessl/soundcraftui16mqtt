CREATE TABLE IF NOT EXISTS misc(
  id integer PRIMARY KEY AUTOINCREMENT,
  parameter TEXT,
  value TEXT
);

CREATE TABLE IF NOT EXISTS channel(
  id integer PRIMARY KEY,
  mute integer DEFAULT 0,
  solo integer DEFAULT 0,
  mix REAL DEFAULT 0,
  gain REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS channel_fx(
  id integer PRIMARY KEY AUTOINCREMENT,
  channel_id integer NOT NULL,
  fx_id integer NOT NULL,
  mix REAL DEFAULT 0,
  mute REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fx(
  id integer PRIMARY KEY,
  par1 REAL DEFAULT 0,
  par2 REAL DEFAULT 0,
  par3 REAL DEFAULT 0,
  par4 REAL DEFAULT 0,
  par5 REAL DEFAULT 0,
  par6 REAL DEFAULT 0,
  mute INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS status(
  id integer PRIMARY KEY,
  name TEXT NOT NULL,
  state integer DEFAULT 0
);

CREATE TABLE IF NOT EXISTS entity_config(
  id integer PRIMARY KEY,
  name TXT NOT NULL,
  address TEXT NOT NULL,
  port int NOT NULL
);
