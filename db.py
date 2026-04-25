import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "app.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plans (
              id TEXT PRIMARY KEY,
              title TEXT,
              date TEXT,
              budget INTEGER,
              people_count INTEGER,
              preferences TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

