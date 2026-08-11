"""
init_db.py
──────────
Automatic database initialization script for creating SQLite tables and indexes.
"""

from backend.database.connection import get_db, DB_PATH
from backend.database.models import (
    CREATE_DOCUMENTS_TABLE,
    CREATE_EXTRACTED_FIELDS_TABLE,
    CREATE_BUSINESS_CONTACTS_TABLE,
    CREATE_PROCESSING_LOGS_TABLE,
    CREATE_INDEXES
)
from backend.utils.logger import logger

def init_db():
    """Create SQLite database tables and indexes if they do not exist."""
    logger.log_step("Database Init", f"Initializing SQLite database at {DB_PATH}")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(CREATE_DOCUMENTS_TABLE)
        cursor.execute(CREATE_EXTRACTED_FIELDS_TABLE)
        cursor.execute(CREATE_BUSINESS_CONTACTS_TABLE)
        cursor.execute(CREATE_PROCESSING_LOGS_TABLE)
        for index_sql in CREATE_INDEXES:
            cursor.execute(index_sql)
    logger.log_step("Database Init", "SQLite tables and indexes initialized successfully.")

if __name__ == "__main__":
    init_db()
