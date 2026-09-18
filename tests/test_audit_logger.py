import os
import pytest
from src.models import AuditRecord
from src.storage.audit_logger import AuditLogger


@pytest.fixture
def audit_logger(tmp_path):
    db_file = str(tmp_path / "test_audit.db")
    return AuditLogger(db_path=db_file)


def test_log_and_retrieve_audit(audit_logger):
    record = AuditRecord(
        query_id="QRY-TEST-01",
        timestamp="2026-09-18T10:00:00Z",
        user_id="U102",
        user_role="Finance",
        user_dept="Finance",
        user_clearance="Internal",
        query_text="What is Q4 forecast?",
        retrieved_candidates=["DOC-101", "DOC-102"],
        authorized_docs=["DOC-101"],
        unauthorized_docs=["DOC-102"],
        rejection_reasons={"DOC-102": ["Role mismatch"]},
        resolved_authoritative_doc_id="DOC-101",
        superseded_doc_ids=[],
        evidence_used=["DOC-101"],
        final_answer="Q4 projected revenue is 120 crore. [DOC-101, v2.0]",
        citations=["DOC-101 (v2.0)"],
        safe_refusal_triggered=False
    )

    audit_logger.log_audit(record)

    fetched = audit_logger.get_audit("QRY-TEST-01")
    assert fetched is not None
    assert fetched.user_id == "U102"
    assert fetched.authorized_docs == ["DOC-101"]
    assert fetched.unauthorized_docs == ["DOC-102"]
    assert fetched.rejection_reasons == {"DOC-102": ["Role mismatch"]}

    all_logs = audit_logger.list_audits()
    assert len(all_logs) == 1
