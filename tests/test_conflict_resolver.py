import pytest
from src.models import Document
from src.agents.conflict_resolver import ConflictResolver


@pytest.fixture
def resolver():
    return ConflictResolver()


def test_effective_date_and_version_superseding(resolver):
    doc_v1 = Document(
        document_id="DOC-301",
        title="Q4 Forecast",
        classification="Internal",
        allowed_departments=["Finance"],
        allowed_roles=["Finance"],
        version="1.0",
        effective_date="2026-06-01",
        content="Q4 projected revenue is 110 crore."
    )
    doc_v2 = Document(
        document_id="DOC-302",
        title="Q4 Forecast",
        classification="Internal",
        allowed_departments=["Finance"],
        allowed_roles=["Finance"],
        version="2.0",
        effective_date="2026-09-01",
        content="Q4 projected revenue is 125 crore."
    )

    active, superseded, notes, conflicts = resolver.resolve([doc_v1, doc_v2])

    assert len(active) == 1
    assert active[0].document_id == "DOC-302"
    assert len(superseded) == 1
    assert superseded[0].document_id == "DOC-301"
    assert "DOC-301" in notes[0]
    assert "superseded by DOC-302" in notes[0]


def test_identical_date_and_version_tie_break(resolver):
    doc_a = Document(
        document_id="DOC-A",
        title="Revenue Target",
        classification="Internal",
        version="1.0",
        effective_date="2026-09-01",
        content="Target is 100 crore."
    )
    doc_b = Document(
        document_id="DOC-B",
        title="Revenue Target",
        classification="Internal",
        version="1.0",
        effective_date="2026-09-01",
        content="Target is 105 crore."
    )

    active, superseded, notes, conflicts = resolver.resolve([doc_a, doc_b])

    # Tie-break rule: keep both and report discrepancy note
    assert len(active) == 2
    assert len(superseded) == 0
    assert len(conflicts) == 1
    assert "Discrepancy detected between DOC-A and DOC-B" in conflicts[0]
