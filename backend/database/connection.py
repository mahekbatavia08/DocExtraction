import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "ocr_app.db"

def get_connection():
    """Returns a SQLite connection with dict-like row factory and foreign keys enabled."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db():
    """Context manager for managing SQLite database connection and transaction safety."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
