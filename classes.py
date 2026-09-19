from dataclasses import dataclass, field

@dataclass
class User:
    user_id: str
    role: str
    department: str
    clearance: str

@dataclass
class Document:
    document_id: str
    title: str
    classification: str
    allowed_departments: list
    allowed_roles: list
    version: str
    effective_date: str
    content: str

@dataclass
class AuditLog:
    request_id: str
    timestamp: str
    user_id: str
    query: str
    candidate_doc_ids: list = field(default_factory=list)
    decisions: list = field(default_factory=list)
    docs_sent_to_llm: list = field(default_factory=list)
    answer: str = ""

@dataclass
class RequestContext:
    user: User
    store: "VectorStore"
    audit: AuditLog