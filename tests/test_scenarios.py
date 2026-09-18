import os
import pytest
from src.models import UserContext
from src.storage.document_store import DocumentStore
from src.pipeline import SentinelRAGPipeline


@pytest.fixture
def pipeline(tmp_path):
    chroma_dir = str(tmp_path / "chroma")
    audit_db = str(tmp_path / "audit.db")
    return SentinelRAGPipeline(persist_dir=chroma_dir, audit_db_path=audit_db)


def test_scenario_a_authorized_answer(pipeline):
    """Test Input A — Authorized answer
    User: U102 (Finance, Internal)
    Docs: DOC-101 (Finance/Finance, 120 crore), DOC-102 (Engineering/Engineer)
    Query: 'What is the Q4 revenue forecast?'
    Expected: DOC-101 authorized and cited, DOC-102 blocked/dropped.
    """
    user = UserContext(
        user_id="U102",
        role="Finance",
        department="Finance",
        clearance="Internal"
    )
    docs = DocumentStore("data/test_input_a/documents.json").get_all_documents()

    result = pipeline.run("What is the Q4 revenue forecast?", user=user, candidate_pool=docs)
    audit = pipeline.audit_logger.get_audit(result.query_id)

    assert result.safe_refusal_triggered is False
    assert "120 crore" in result.answer
    assert "DOC-101 (v2.0)" in result.citations
    assert "DOC-102" not in [c for c in result.citations]

    assert audit is not None
    assert "DOC-101" in audit.authorized_docs
    assert "DOC-102" in audit.unauthorized_docs
    assert "Department mismatch" in audit.rejection_reasons["DOC-102"][0]


def test_scenario_b_unauthorized_zero_leak(pipeline):
    """Test Input B — Relevant but unauthorized (Zero Leak Guarantee)
    User: U205 (Marketing, Internal)
    Docs: DOC-201 (Restricted, Executive, 145 crore)
    Query: 'What is the Q4 revenue forecast?'
    Expected: Safe refusal (Option B), zero leak of '145 crore' or 'DOC-201' content.
    """
    user = UserContext(
        user_id="U205",
        role="Marketing",
        department="Marketing",
        clearance="Internal"
    )
    docs = DocumentStore("data/test_input_b/documents.json").get_all_documents()

    result = pipeline.run("What is the Q4 revenue forecast?", user=user, candidate_pool=docs)
    audit = pipeline.audit_logger.get_audit(result.query_id)

    # ZERO LEAK INVARIANTS:
    assert result.safe_refusal_triggered is True
    assert "145 crore" not in result.answer
    assert "DOC-201" not in result.answer
    assert len(result.citations) == 0
    assert "does not permit access" in result.answer

    assert audit is not None
    assert "DOC-201" in audit.unauthorized_docs
    assert "DOC-201" not in audit.evidence_used
    assert "Clearance insufficient" in audit.rejection_reasons["DOC-201"][0]


def test_scenario_c_conflict_and_version_resolution(pipeline):
    """Test Input C — Authorized conflict & version resolution
    User: U301 (Finance, Internal)
    Docs: DOC-301 (v1.0, 2026-06-01, 110 crore), DOC-302 (v2.0, 2026-09-01, 125 crore)
    Query: 'What is the latest Q4 revenue forecast?'
    Expected: DOC-302 (v2.0) cited, DOC-301 marked superseded.
    """
    user = UserContext(
        user_id="U301",
        role="Finance",
        department="Finance",
        clearance="Internal"
    )
    docs = DocumentStore("data/test_input_c/documents.json").get_all_documents()

    result = pipeline.run("What is the latest Q4 revenue forecast?", user=user, candidate_pool=docs)
    audit = pipeline.audit_logger.get_audit(result.query_id)

    assert result.safe_refusal_triggered is False
    assert "125 crore" in result.answer
    assert "DOC-302 (v2.0)" in result.citations
    assert "DOC-301 (v1.0, 2026-06-01) is superseded by DOC-302 (v2.0, 2026-09-01)" in result.answer

    assert audit is not None
    assert audit.resolved_authoritative_doc_id == "DOC-302"
    assert "DOC-301" in audit.superseded_doc_ids
