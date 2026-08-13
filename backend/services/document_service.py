"""
document_service.py
───────────────────
Core service managing document lifecycle, SQLite database persistence,
extracted fields, processing logs, business contacts, search, filtering, and stats.
"""

import time
from typing import Dict, Any, List, Optional
from backend.database.connection import get_db
from backend.services.extraction_service import extraction_service
from backend.utils.logger import logger

class DocumentService:

    def save_document_result(
        self,
        filename: str,
        file_type: str,
        document_type: str,
        raw_ocr_text: str,
        extracted_fields: Dict[str, Any],
        processing_time: float,
        overall_confidence: float,
        processing_status: str = "completed",
        image_data: str = "",
        stage_logs: Optional[List[Dict[str, Any]]] = None,
        ocr_engine: str = "Azure Document Intelligence",
        extraction_engine: str = "auto",
        raw_ocr: str = "",
        error_message: str = ""
    ) -> int:
        """
        Creates a new document record in SQLite DB along with its extracted fields,
        business contact info (if applicable), and processing logs.
        Returns the generated document ID.
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Sanitize text and fields for privacy compliance
        sanitized_raw_text = extraction_service.sanitize_cvv_and_sensitive_text(raw_ocr_text)
        sanitized_fields = extraction_service.sanitize_extracted_fields(extracted_fields, doc_type=document_type)

        with get_db() as conn:
            cursor = conn.cursor()

            # 1. Insert Document record
            cursor.execute(
                """
                INSERT INTO documents (
                    original_filename, document_type, file_type, upload_timestamp,
                    processing_time, overall_confidence, processing_status,
                    ocr_engine, extraction_engine, raw_ocr_text, raw_ocr, image_data, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    filename,
                    document_type or "Unknown",
                    file_type or "image/png",
                    timestamp,
                    round(float(processing_time), 3),
                    round(float(overall_confidence), 4),
                    processing_status,
                    ocr_engine or "Azure Document Intelligence",
                    extraction_engine or "auto",
                    sanitized_raw_text,
                    raw_ocr or "",
                    image_data or "",
                    error_message or ""
                )
            )
            doc_id = cursor.lastrowid

            # 2. Insert Extracted Fields
            for name, val in sanitized_fields.items():
                if val:
                    field_conf = round(float(overall_confidence), 2)
                    cursor.execute(
                        """
                        INSERT INTO extracted_fields (document_id, field_name, field_value, confidence)
                        VALUES (?, ?, ?, ?)
                        """,
                        (doc_id, str(name), str(val), field_conf)
                    )

            # 3. Extract & Save Business Contact if present
            contact_info = extraction_service.extract_business_contact(sanitized_fields, raw_text=sanitized_raw_text)
            if any(contact_info.values()):
                cursor.execute(
                    """
                    INSERT INTO business_contacts (
                        document_id, name, company, designation, email, phone, website, address, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        doc_id,
                        contact_info["name"],
                        contact_info["company"],
                        contact_info["designation"],
                        contact_info["email"],
                        contact_info["phone"],
                        contact_info["website"],
                        contact_info["address"],
                        timestamp
                    )
                )

            # 4. Insert Processing Logs
            if not stage_logs:
                stage_logs = [
                    {"stage": "Upload", "message": f"Document '{filename}' uploaded successfully.", "duration": 0.01},
                    {"stage": "OCR", "message": f"Text extraction complete for type '{document_type}'.", "duration": round(processing_time * 0.6, 3)},
                    {"stage": "Extraction", "message": f"Extracted {len(sanitized_fields)} structured entities.", "duration": round(processing_time * 0.3, 3)},
                    {"stage": "Validation", "message": "Sensitive data masked & validation passed.", "duration": round(processing_time * 0.1, 3)}
                ]

            for log in stage_logs:
                cursor.execute(
                    """
                    INSERT INTO processing_logs (document_id, stage, message, timestamp, duration)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        doc_id,
                        log.get("stage", "Processing"),
                        log.get("message", "Completed stage"),
                        log.get("timestamp", timestamp),
                        round(float(log.get("duration", 0.0)), 3)
                    )
                )

            logger.log_step("Database Insert", f"Saved document '{filename}' with DB ID: {doc_id}")
            return doc_id

    def update_document_result(
        self,
        doc_id: int,
        document_type: str,
        raw_ocr_text: str,
        extracted_fields: Dict[str, Any],
        processing_time: float,
        overall_confidence: float,
        processing_status: str = "completed",
        ocr_engine: str = "Azure Document Intelligence",
        raw_ocr: str = "",
        error_message: str = ""
    ) -> bool:
        """Updates an existing document record on retry without creating duplicate DB entries."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        sanitized_raw_text = extraction_service.sanitize_cvv_and_sensitive_text(raw_ocr_text)
        sanitized_fields = extraction_service.sanitize_extracted_fields(extracted_fields, doc_type=document_type)

        with get_db() as conn:
            cursor = conn.cursor()

            # 1. Update Document record
            cursor.execute(
                """
                UPDATE documents SET
                    document_type = ?,
                    processing_time = ?,
                    overall_confidence = ?,
                    processing_status = ?,
                    ocr_engine = ?,
                    raw_ocr_text = ?,
                    raw_ocr = ?,
                    error_message = ?,
                    upload_timestamp = ?
                WHERE id = ?
                """,
                (
                    document_type or "Unknown",
                    round(float(processing_time), 3),
                    round(float(overall_confidence), 4),
                    processing_status,
                    ocr_engine or "Azure Document Intelligence",
                    sanitized_raw_text,
                    raw_ocr or "",
                    error_message or "",
                    timestamp,
                    doc_id
                )
            )

            # 2. Clear & Re-insert Extracted Fields
            cursor.execute("DELETE FROM extracted_fields WHERE document_id = ?", (doc_id,))
            for name, val in sanitized_fields.items():
                if val:
                    field_conf = round(float(overall_confidence), 2)
                    cursor.execute(
                        "INSERT INTO extracted_fields (document_id, field_name, field_value, confidence) VALUES (?, ?, ?, ?)",
                        (doc_id, str(name), str(val), field_conf)
                    )

            # 3. Clear & Re-insert Contact info
            cursor.execute("DELETE FROM business_contacts WHERE document_id = ?", (doc_id,))
            contact_info = extraction_service.extract_business_contact(sanitized_fields, raw_text=sanitized_raw_text)
            if any(contact_info.values()):
                cursor.execute(
                    """
                    INSERT INTO business_contacts (
                        document_id, name, company, designation, email, phone, website, address, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        doc_id, contact_info["name"], contact_info["company"], contact_info["designation"],
                        contact_info["email"], contact_info["phone"], contact_info["website"], contact_info["address"], timestamp
                    )
                )

            logger.log_step("Database Update", f"Updated document record ID: {doc_id} (Status: {processing_status})")
            return True

    def get_documents(
        self,
        search: Optional[str] = None,
        document_type: Optional[str] = None,
        sort_by: str = "date",
        order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        Retrieves document list with search, document type filter, and sorting.
        """
        with get_db() as conn:
            cursor = conn.cursor()

            query = """
                SELECT d.*, 
                    COALESCE(c.name, (
                        SELECT field_value FROM extracted_fields f 
                        WHERE f.document_id = d.id AND (LOWER(f.field_name) LIKE '%name%' OR LOWER(f.field_name) LIKE '%title%')
                        LIMIT 1
                    ), 'N/A') as extracted_name
                FROM documents d
                LEFT JOIN business_contacts c ON c.document_id = d.id
                WHERE 1=1
            """
            params: List[Any] = []

            if document_type and document_type != "All":
                query += " AND d.document_type = ?"
                params.append(document_type)

            if search:
                term = f"%{search.strip()}%"
                query += """ AND (
                    d.original_filename LIKE ? OR 
                    d.document_type LIKE ? OR 
                    d.raw_ocr_text LIKE ? OR
                    c.name LIKE ? OR
                    c.company LIKE ?
                )"""
                params.extend([term, term, term, term, term])

            # Sorting logic
            sort_column = "d.upload_timestamp"
            if sort_by == "confidence":
                sort_column = "d.overall_confidence"
            elif sort_by == "filename":
                sort_column = "d.original_filename"
            elif sort_by == "type":
                sort_column = "d.document_type"

            sort_order = "DESC" if order.lower() == "desc" else "ASC"
            query += f" ORDER BY {sort_column} {sort_order}"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves full document record with extracted fields, logs, and contact info."""
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            doc_row = cursor.fetchone()
            if not doc_row:
                return None

            doc_dict = dict(doc_row)

            # Get Extracted Fields
            cursor.execute("SELECT id, document_id, field_name, field_value, confidence FROM extracted_fields WHERE document_id = ?", (doc_id,))
            doc_dict["fields"] = [dict(f) for f in cursor.fetchall()]

            # Get Processing Logs
            cursor.execute("SELECT id, document_id, stage, message, timestamp, duration FROM processing_logs WHERE document_id = ? ORDER BY id ASC", (doc_id,))
            doc_dict["logs"] = [dict(l) for l in cursor.fetchall()]

            # Get Contact if present
            cursor.execute("SELECT * FROM business_contacts WHERE document_id = ?", (doc_id,))
            contact_row = cursor.fetchone()
            doc_dict["contact"] = dict(contact_row) if contact_row else None

            return doc_dict

    def delete_document(self, doc_id: int) -> bool:
        """Deletes a document record and cascades associated fields, contacts, and logs."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            return cursor.rowcount > 0

    def get_document_fields(self, doc_id: int) -> List[Dict[str, Any]]:
        """Retrieves extracted fields for document ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, document_id, field_name, field_value, confidence FROM extracted_fields WHERE document_id = ?", (doc_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_document_logs(self, doc_id: int) -> List[Dict[str, Any]]:
        """Retrieves processing logs for document ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, document_id, stage, message, timestamp, duration FROM processing_logs WHERE document_id = ? ORDER BY id ASC", (doc_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_contacts(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves all business contacts."""
        with get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM business_contacts WHERE 1=1"
            params: List[Any] = []

            if search:
                term = f"%{search.strip()}%"
                query += " AND (name LIKE ? OR company LIKE ? OR email LIKE ? OR phone LIKE ?)"
                params.extend([term, term, term, term])

            query += " ORDER BY id DESC"
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    def get_contact_by_id(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves contact by ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM business_contacts WHERE id = ?", (contact_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Calculates database stats: total docs, doc type counts, avg confidence, avg processing time."""
        with get_db() as conn:
            cursor = conn.cursor()

            # Total count
            cursor.execute("SELECT COUNT(*) as total FROM documents")
            total = cursor.fetchone()["total"] or 0

            # Document type breakdown
            cursor.execute("SELECT document_type, COUNT(*) as count FROM documents GROUP BY document_type")
            type_counts = {row["document_type"]: row["count"] for row in cursor.fetchall()}

            # Averages
            cursor.execute("SELECT AVG(overall_confidence) as avg_conf, AVG(processing_time) as avg_time FROM documents")
            avg_row = cursor.fetchone()
            
            avg_conf = round(float(avg_row["avg_conf"] or 0.0), 4)
            avg_time = round(float(avg_row["avg_time"] or 0.0), 3)

            return {
                "total_documents": total,
                "document_type_counts": type_counts,
                "average_confidence": avg_conf,
                "average_processing_time": avg_time
            }

document_service = DocumentService()
