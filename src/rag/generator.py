import os
import re
from typing import List, Tuple, Optional
from src.models import Document, UserContext


class GroundedGenerator:
    """Generation Engine for SentinelRAG.
    
    Produces grounded natural language answers with source citations from
    augmented authorized context, or produces Option B access-aware refusals
    with zero leakage.
    """

    def __init__(self):
        self.gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.openai_key = os.environ.get("OPENAI_API_KEY")

    def generate_response(
        self,
        query: str,
        user: UserContext,
        authoritative_docs: List[Document],
        superseded_notes: List[str],
        conflict_notes: List[str],
        candidates_found: bool,
        unauthorized_count: int,
    ) -> Tuple[str, List[str]]:
        """Generates the final cited response or safe refusal.
        
        Returns:
            (answer_text, citations_list)
        """
        # Case 1: Relevant documents were retrieved, but all were blocked by the Gatekeeper (Option B)
        if unauthorized_count > 0 and not authoritative_docs:
            refusal_text = (
                f"Documents answering this query exist in the knowledge base, but your "
                f"current clearance level ({user.clearance.name.capitalize()}) or department "
                f"({user.department}) does not permit access."
            )
            return refusal_text, []

        # Case 2: No candidates found at all
        if not authoritative_docs:
            return "No authorized documents were found matching your query.", []

        # Case 3: Authorized evidence exists -> Generate grounded answer
        return self._synthesize_authorized(
            query=query,
            docs=authoritative_docs,
            superseded_notes=superseded_notes,
            conflict_notes=conflict_notes
        )

    def _synthesize_authorized(
        self,
        query: str,
        docs: List[Document],
        superseded_notes: List[str],
        conflict_notes: List[str]
    ) -> Tuple[str, List[str]]:
        """Synthesizes the answer from authorized active documents."""
        citations: List[str] = [f"{d.document_id} (v{d.version})" for d in docs]

        # Extract factual statements from documents
        doc_contents = [d.content.strip() for d in docs]
        main_fact = " ".join(doc_contents)

        # Build clean answer text with citation
        primary_doc = docs[0]
        if len(docs) == 1:
            answer = f"{primary_doc.content.strip()} [{primary_doc.document_id}, v{primary_doc.version}]"
        else:
            doc_summaries = [f"{d.content.strip()} [{d.document_id}, v{d.version}]" for d in docs]
            answer = " ".join(doc_summaries)

        # Append superseded notices
        if superseded_notes:
            notes_str = " Note: " + " ".join(superseded_notes)
            answer += notes_str

        # Append conflict / discrepancy notices (tie-breaking requirement)
        if conflict_notes:
            discrepancy_str = " Discrepancy Note: " + " ".join(conflict_notes)
            answer += discrepancy_str

        return answer, citations
