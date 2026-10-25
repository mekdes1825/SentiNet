"""Database layer: schema, helpers, fictional seed data. LAB ONLY."""
import hashlib, os, sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("SENTINET_DB", os.path.join(BASE, "sentinet.db"))
# Set SENTINET_HARDENED=1 to switch the controlled weaknesses off (before/after demo).
HARDENED = os.environ.get("SENTINET_HARDENED", "0") == "1"
ATTACKER_DEVICE = "DEV-ATTACKER-01"
# Phone numbers must look like 09 + 8 digits. Use made-up numbers only (fictional data rule).
PHONE_RE = r"09\d{8}"
# Accounts hidden from the Phone / SIM / Phishing lists: the fixed recipient (id 7) and auto-created ones.
VISIBLE = "id<>7 AND name NOT LIKE 'External %'"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY, name TEXT, phone TEXT UNIQUE, pin_hash TEXT, balance REAL,
  home_device TEXT, device_id TEXT, sim_state TEXT DEFAULT 'victim',
  secret_answer TEXT, restricted INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, source TEXT, event_type TEXT,
  user_id INTEGER, phone TEXT, session_id TEXT, device_id TEXT, details TEXT);
CREATE INDEX IF NOT EXISTS ev_user ON events(user_id, ts);
CREATE TABLE IF NOT EXISTS sessions(
  id TEXT PRIMARY KEY, user_id INTEGER, device_id TEXT, state TEXT, data TEXT,
  created REAL, last_seen REAL, ended INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS transactions(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, from_user INTEGER, to_user INTEGER,
  amount REAL, status TEXT);
CREATE TABLE IF NOT EXISTS campaigns(
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, scenario TEXT, lang TEXT, created REAL);
CREATE TABLE IF NOT EXISTS targets(
  id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_id INTEGER, user_id INTEGER, token TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS rules(
  id TEXT PRIMARY KEY, name TEXT, description TEXT, window_sec INTEGER,
  points INTEGER, enabled INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS alerts(
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, first_ts REAL, updated REAL,
  score INTEGER, level TEXT, rules TEXT, explanation TEXT, recommended TEXT,
  status TEXT DEFAULT 'open');
"""

# name, phone, PIN, balance, birth-year (used only when hardened). ALL FICTIONAL.
SEED_USERS = [
    ("Abebe Kebede",      "0900000001", "1234", 25000, "1990"),
    ("Tigist Alemu",      "0900000002", "4321", 18000, "1988"),
    ("Dawit Tesfaye",     "0900000003", "1111", 12000, "1995"),
    ("Hana Mulugeta",     "0900000004", "2222", 30000, "1992"),
    ("Samuel Bekele",     "0900000005", "3333", 9000,  "1985"),
    ("Marta Girma",       "0900000006", "4444", 15000, "1998"),
    ("Unknown Recipient", "0900000099", "0000", 100,   "1980"),
]

SEED_RULES = [
    ("R1", "SIM re-registration + PIN reset",
     "PIN reset requested shortly after a SIM re-registration.", 120, 50),
    ("R2", "Repeated failed PINs",
     "Three or more wrong PIN entries inside the window.", 300, 25),
    ("R3", "New device, then sensitive action",
     "A session from an unfamiliar handset followed by PIN reset, PIN change or transfer.", 300, 20),
    ("R4", "Rapid changes after SIM swap",
     "Two or more account changes soon after a SIM re-registration.", 600, 20),
    ("R5", "Transfer after account recovery",
     "A transfer started soon after a PIN reset completed.", 600, 30),
    ("R6", "Previously phished user",
     "Another rule fired for a user whose Human Risk Index is 60 or higher.", 0, 5),
]


def weak_hash(pin):
    # INTENTIONALLY WEAK (unsalted MD5) - a controlled lab weakness. Fictional PINs only.
    return hashlib.md5(pin.encode()).hexdigest()


def conn():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    return c


def query(sql, args=(), one=False):
    c = conn()
    try:
        rows = c.execute(sql, args).fetchall()
    finally:
        c.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, args=()):
    c = conn()
    try:
        cur = c.execute(sql, args)
        c.commit()
        return cur.lastrowid
    finally:
        c.close()


def _add_missing_columns(c):
    """Upgrade a database created by an older schema, keeping all rows.
    CREATE TABLE IF NOT EXISTS never adds columns, so an old table would make the
    CREATE INDEX lines in SCHEMA fail (e.g. 'no such column: ts')."""
    ref = sqlite3.connect(":memory:")
    try:
        ref.executescript(SCHEMA)
        for (table,) in ref.execute("SELECT name FROM sqlite_master "
                                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
            have = {r[1] for r in c.execute(f"PRAGMA table_info({table})")}
            if not have:          # table not in the database yet; SCHEMA creates it
                continue
            for _cid, name, ctype, _nn, dflt, pk in ref.execute(f"PRAGMA table_info({table})").fetchall():
                if name in have or pk:
                    continue
                sql = f"ALTER TABLE {table} ADD COLUMN {name} {ctype or ''}"
                if dflt is not None:
                    sql += f" DEFAULT {dflt}"
                c.execute(sql)
        c.commit()
    finally:
        ref.close()


def init_db():
    c = conn()
    try:
        _add_missing_columns(c)
        c.executescript(SCHEMA)
        if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            for i, (name, phone, pin, bal, secret) in enumerate(SEED_USERS, start=1):
                dev = f"DEV-HOME-{i:02d}"
                c.execute("INSERT INTO users(id,name,phone,pin_hash,balance,home_device,device_id,"
                          "sim_state,secret_answer) VALUES(?,?,?,?,?,?,?,?,?)",
                          (i, name, phone, weak_hash(pin), bal, dev, dev, "victim", secret))
        for r in SEED_RULES:
            c.execute("INSERT OR IGNORE INTO rules(id,name,description,window_sec,points) "
                      "VALUES(?,?,?,?,?)", r)
        c.commit()
    finally:
        c.close()


def reset_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()


def create_account(name, phone, pin, balance, secret="1990"):
    """Insert a fictional account and give it its own handset id. Returns the user id."""
    uid = execute("INSERT INTO users(name,phone,pin_hash,balance,home_device,device_id,sim_state,secret_answer)"
                  " VALUES(?,?,?,?,?,?,?,?)", (name, phone, weak_hash(pin), balance, "", "", "victim", secret))
    dev = f"DEV-HOME-{uid:02d}"
    execute("UPDATE users SET home_device=?, device_id=? WHERE id=?", (dev, dev, uid))
    return uid
