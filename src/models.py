from enum import IntEnum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator


class ClearanceLevel(IntEnum):
    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    RESTRICTED = 3

    @classmethod
    def from_str(cls, value: str) -> "ClearanceLevel":
        if isinstance(value, cls):
            return value
        cleaned = str(value).strip().upper()
        mapping = {
            "PUBLIC": cls.PUBLIC,
            "INTERNAL": cls.INTERNAL,
            "CONFIDENTIAL": cls.CONFIDENTIAL,
            "RESTRICTED": cls.RESTRICTED,
        }
        if cleaned in mapping:
            return mapping[cleaned]
        raise ValueError(f"Unknown clearance level: {value}. Expected Public, Internal, Confidential, or Restricted.")

    def __str__(self) -> str:
        return self.name.capitalize()


class UserContext(BaseModel):
    user_id: str
    role: str
    department: str
    clearance: ClearanceLevel

    @field_validator("clearance", mode="before")
    @classmethod
    def validate_clearance(cls, v: Any) -> ClearanceLevel:
        return ClearanceLevel.from_str(v)


class Document(BaseModel):
    document_id: str
    title: str
    classification: ClearanceLevel
    allowed_departments: List[str] = Field(default_factory=list)
    allowed_roles: List[str] = Field(default_factory=list)
    version: str = "1.0"
    effective_date: str = ""
    content: str = ""
    owner: Optional[str] = None

    @field_validator("classification", mode="before")
    @classmethod
    def validate_classification(cls, v: Any) -> ClearanceLevel:
        return ClearanceLevel.from_str(v)

    @property
    def summary(self) -> str:
        return f"{self.title} (ID: {self.document_id}, v{self.version}, {self.effective_date})"


class AuthorizationDecision(BaseModel):
    document_id: str
    authorized: bool
    reasons: List[str] = Field(default_factory=list)
    classification: str
    allowed_departments: List[str]
    allowed_roles: List[str]


class AuditRecord(BaseModel):
    query_id: str
    timestamp: str
    user_id: str
    user_role: str
    user_dept: str
    user_clearance: str
    query_text: str
    retrieved_candidates: List[str] = Field(default_factory=list)
    authorized_docs: List[str] = Field(default_factory=list)
    unauthorized_docs: List[str] = Field(default_factory=list)
    rejection_reasons: Dict[str, List[str]] = Field(default_factory=dict)
    resolved_authoritative_doc_id: Optional[str] = None
    superseded_doc_ids: List[str] = Field(default_factory=list)
    evidence_used: List[str] = Field(default_factory=list)
    final_answer: str = ""
    citations: List[str] = Field(default_factory=list)
    safe_refusal_triggered: bool = False


class QueryResult(BaseModel):
    query: str
    answer: str
    citations: List[str] = Field(default_factory=list)
    superseded_notes: List[str] = Field(default_factory=list)
    candidate_count: int = 0
    authorized_count: int = 0
    unauthorized_count: int = 0
    query_id: str = ""
    safe_refusal_triggered: bool = False
