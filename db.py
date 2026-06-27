import sqlite3
from config import DB_PATH

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db() -> None:
    with open("schema.sql") as f:
        sql = f.read()
    with get_conn() as conn:
        conn.executescript(sql)
