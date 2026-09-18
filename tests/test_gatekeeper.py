import pytest
from src.models import Document, UserContext, ClearanceLevel
from src.agents.authorization_gate import AuthorizationGatekeeper


@pytest.fixture
def gatekeeper():
    return AuthorizationGatekeeper()


def test_clearance_hierarchy(gatekeeper):
    user_internal = UserContext(
        user_id="U1", role="Finance", department="Finance", clearance="Internal"
    )
    doc_public = Document(
        document_id="D1", title="Public Doc", classification="Public",
        allowed_departments=["Finance"], allowed_roles=["Finance"], content="Public data"
    )
    doc_internal = Document(
        document_id="D2", title="Internal Doc", classification="Internal",
        allowed_departments=["Finance"], allowed_roles=["Finance"], content="Internal data"
    )
    doc_confidential = Document(
        document_id="D3", title="Confidential Doc", classification="Confidential",
        allowed_departments=["Finance"], allowed_roles=["Finance"], content="Confidential data"
    )
    doc_restricted = Document(
        document_id="D4", title="Restricted Doc", classification="Restricted",
        allowed_departments=["Finance"], allowed_roles=["Finance"], content="Restricted data"
    )

    auth, unauth, decisions = gatekeeper.evaluate(
        [doc_public, doc_internal, doc_confidential, doc_restricted], user_internal
    )

    auth_ids = [d.document_id for d in auth]
    unauth_ids = [d.document_id for d in unauth]

    assert auth_ids == ["D1", "D2"]
    assert unauth_ids == ["D3", "D4"]
    assert decisions["D3"].authorized is False
    assert "Clearance insufficient" in decisions["D3"].reasons[0]


def test_department_mismatch(gatekeeper):
    user = UserContext(user_id="U2", role="Engineer", department="Engineering", clearance="Internal")
    doc_finance = Document(
        document_id="D10", title="Finance Doc", classification="Internal",
        allowed_departments=["Finance"], allowed_roles=["Engineer"], content="Data"
    )

    auth, unauth, decisions = gatekeeper.evaluate([doc_finance], user)
    assert len(auth) == 0
    assert len(unauth) == 1
    assert "Department mismatch" in decisions["D10"].reasons[0]


def test_role_mismatch(gatekeeper):
    user = UserContext(user_id="U3", role="Analyst", department="Finance", clearance="Internal")
    doc_manager = Document(
        document_id="D11", title="Manager Doc", classification="Internal",
        allowed_departments=["Finance"], allowed_roles=["Manager"], content="Data"
    )

    auth, unauth, decisions = gatekeeper.evaluate([doc_manager], user)
    assert len(auth) == 0
    assert len(unauth) == 1
    assert "Role mismatch" in decisions["D11"].reasons[0]


def test_wildcard_permissions(gatekeeper):
    user = UserContext(user_id="U4", role="Marketing", department="Marketing", clearance="Internal")
    doc_open = Document(
        document_id="D12", title="Open Doc", classification="Internal",
        allowed_departments=[], allowed_roles=[], content="All access data"
    )

    auth, unauth, _ = gatekeeper.evaluate([doc_open], user)
    assert len(auth) == 1
    assert len(unauth) == 0
