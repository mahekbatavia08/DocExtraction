"""
models.py
─────────
SQL table schemas and data models for SQLite database storage.
"""

CREATE_DOCUMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_filename TEXT NOT NULL,
    document_type TEXT DEFAULT 'Unknown',
    file_type TEXT DEFAULT 'image/png',
    upload_timestamp TEXT NOT NULL,
    processing_time REAL DEFAULT 0.0,
    overall_confidence REAL DEFAULT 0.0,
    processing_status TEXT DEFAULT 'completed',
    raw_ocr_text TEXT DEFAULT '',
    image_data TEXT DEFAULT ''
);
"""

CREATE_EXTRACTED_FIELDS_TABLE = """
CREATE TABLE IF NOT EXISTS extracted_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    field_value TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
"""

CREATE_BUSINESS_CONTACTS_TABLE = """
CREATE TABLE IF NOT EXISTS business_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    name TEXT DEFAULT '',
    company TEXT DEFAULT '',
    designation TEXT DEFAULT '',
    email TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    website TEXT DEFAULT '',
    address TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
"""

CREATE_PROCESSING_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    stage TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    duration REAL DEFAULT 0.0,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_documents_upload_timestamp ON documents(upload_timestamp DESC);",
    "CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents(document_type);",
    "CREATE INDEX IF NOT EXISTS idx_documents_confidence ON documents(overall_confidence DESC);",
    "CREATE INDEX IF NOT EXISTS idx_extracted_fields_document_id ON extracted_fields(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_business_contacts_document_id ON business_contacts(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_processing_logs_document_id ON processing_logs(document_id);"
]
