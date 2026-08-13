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

        # Automatic schema migrations for existing SQLite databases
        cursor.execute("PRAGMA table_info(documents)")
        existing_cols = [row[1] for row in cursor.fetchall()]
        migrations = [
            ("ocr_engine", "ALTER TABLE documents ADD COLUMN ocr_engine TEXT DEFAULT 'Azure Document Intelligence'"),
            ("extraction_engine", "ALTER TABLE documents ADD COLUMN extraction_engine TEXT DEFAULT 'auto'"),
            ("raw_ocr", "ALTER TABLE documents ADD COLUMN raw_ocr TEXT DEFAULT ''"),
            ("error_message", "ALTER TABLE documents ADD COLUMN error_message TEXT DEFAULT ''")
        ]
        for col_name, alter_sql in migrations:
            if col_name not in existing_cols:
                try:
                    cursor.execute(alter_sql)
                    logger.log_step("Database Migration", f"Added column '{col_name}' to 'documents' table.")
                except Exception as ex:
                    logger.log_step("Database Migration Notice", str(ex))

    logger.log_step("Database Init", "SQLite tables and indexes initialized successfully.")

if __name__ == "__main__":
    init_db()
