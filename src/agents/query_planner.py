import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from src.models import UserContext


class QueryPlan(BaseModel):
    original_query: str
    cleaned_query: str
    search_terms: List[str]
    is_latest_requested: bool = False
    temporal_qualifiers: List[str] = Field(default_factory=list)
    user_context_summary: str = ""


class QueryPlanner:
    """Agent that analyzes user questions to determine search intent and retrieval strategy."""

    def plan(self, query: str, user: UserContext) -> QueryPlan:
        q_lower = query.lower().strip()

        # Check for 'latest', 'most recent', 'current', 'newest'
        is_latest = bool(re.search(r"\b(latest|recent|newest|current|updated)\b", q_lower))

        # Check for temporal quarters/years (e.g. Q1, Q2, Q3, Q4, 2026, 2027)
        temporal_matches = re.findall(r"\b(q[1-4]|\b20\d\d\b)\b", q_lower)

        # Clean search terms by removing common stop words
        stop_words = {
            "what", "is", "the", "for", "a", "an", "of", "and", "or", "in", "to",
            "can", "you", "tell", "me", "show", "give", "please", "about", "latest",
            "recent", "newest"
        }
        tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", q_lower)
        search_terms = [w for w in tokens if w not in stop_words]

        cleaned_query = " ".join(tokens)

        user_summary = (
            f"User {user.user_id} (Role: {user.role}, Dept: {user.department}, "
            f"Clearance: {user.clearance.name.capitalize()})"
        )

        return QueryPlan(
            original_query=query,
            cleaned_query=cleaned_query,
            search_terms=search_terms,
            is_latest_requested=is_latest,
            temporal_qualifiers=temporal_matches,
            user_context_summary=user_summary,
        )
