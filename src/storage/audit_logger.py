import json
import sqlite3
import os
from typing import List, Optional
from src.models import AuditRecord


class AuditLogger:
    """Persistent SQLite logger for enterprise audit trails and zero-leak verification."""

    def __init__(self, db_path: str = "data/audit.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    query_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    user_id TEXT,
                    user_role TEXT,
                    user_dept TEXT,
                    user_clearance TEXT,
                    query_text TEXT,
                    retrieved_candidates TEXT,
                    authorized_docs TEXT,
                    unauthorized_docs TEXT,
                    rejection_reasons TEXT,
                    resolved_authoritative_doc_id TEXT,
                    superseded_doc_ids TEXT,
                    evidence_used TEXT,
                    final_answer TEXT,
                    citations TEXT,
                    safe_refusal_triggered INTEGER
                )
            """)
            conn.commit()

    def log_audit(self, record: AuditRecord) -> None:
        """Persists a complete query audit entry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO audit_logs (
                    query_id, timestamp, user_id, user_role, user_dept, user_clearance,
                    query_text, retrieved_candidates, authorized_docs, unauthorized_docs,
                    rejection_reasons, resolved_authoritative_doc_id, superseded_doc_ids,
                    evidence_used, final_answer, citations, safe_refusal_triggered
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.query_id,
                record.timestamp,
                record.user_id,
                record.user_role,
                record.user_dept,
                record.user_clearance,
                record.query_text,
                json.dumps(record.retrieved_candidates),
                json.dumps(record.authorized_docs),
                json.dumps(record.unauthorized_docs),
                json.dumps(record.rejection_reasons),
                record.resolved_authoritative_doc_id,
                json.dumps(record.superseded_doc_ids),
                json.dumps(record.evidence_used),
                record.final_answer,
                json.dumps(record.citations),
                1 if record.safe_refusal_triggered else 0
            ))
            conn.commit()

    def get_audit(self, query_id: str) -> Optional[AuditRecord]:
        """Retrieves a single audit log entry by query_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs WHERE query_id = ?", (query_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_record(row)

    def list_audits(self, limit: int = 50) -> List[AuditRecord]:
        """Lists the most recent audit logs, ordered by timestamp descending."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [self._row_to_record(r) for r in rows]

    def clear_audits(self) -> None:
        """Clears all audit logs for fresh testing."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM audit_logs")
            conn.commit()

    def _row_to_record(self, row: tuple) -> AuditRecord:
        return AuditRecord(
            query_id=row[0],
            timestamp=row[1],
            user_id=row[2],
            user_role=row[3],
            user_dept=row[4],
            user_clearance=row[5],
            query_text=row[6],
            retrieved_candidates=json.loads(row[7]),
            authorized_docs=json.loads(row[8]),
            unauthorized_docs=json.loads(row[9]),
            rejection_reasons=json.loads(row[10]),
            resolved_authoritative_doc_id=row[11],
            superseded_doc_ids=json.loads(row[12]),
            evidence_used=json.loads(row[13]),
            final_answer=row[14],
            citations=json.loads(row[15]),
            safe_refusal_triggered=bool(row[16])
        )
