"""SQLite audit logger for trade signals and decisions."""
import sqlite3, json, datetime, os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "kalshi_data.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS markets (
        ticker TEXT PRIMARY KEY,
        title TEXT,
        category TEXT,
        status TEXT,
        last_updated TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS price_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        timestamp TEXT,
        yes_bid REAL, yes_ask REAL,
        no_bid REAL, no_ask REAL,
        volume INTEGER, open_interest INTEGER
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS trade_signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        timestamp TEXT,
        ev_percent REAL,
        confidence REAL,
        side TEXT,
        explanation TEXT,
        status TEXT DEFAULT 'LOGGED'
    )""")
    conn.commit()
    conn.close()

def log_signal(signal):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO trade_signals (ticker,timestamp,ev_percent,confidence,side,explanation) VALUES (?,?,?,?,?,?)",
        (signal.ticker, datetime.datetime.utcnow().isoformat(),
         signal.ev_percent, signal.confidence, signal.side, signal.explanation)
    )
    conn.commit()
    conn.close()
