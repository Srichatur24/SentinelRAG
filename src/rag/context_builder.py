from typing import List
from src.models import Document


class ContextBuilder:
    """Context Augmentation Engine for SentinelRAG.
    
    Constructs the augmented prompt context using ONLY documents that have passed
    both the Authorization Gatekeeper and Conflict Resolver.
    """

    def build_context(
        self,
        authoritative_docs: List[Document],
        superseded_notes: List[str] = None,
        conflict_notes: List[str] = None
    ) -> str:
        """Constructs a structured context block with strict grounding boundaries."""
        if not authoritative_docs:
            return "No authorized evidence available."

        superseded_notes = superseded_notes or []
        conflict_notes = conflict_notes or []

        blocks: List[str] = []
        for doc in authoritative_docs:
            block = (
                f"--- DOCUMENT START ---\n"
                f"Document ID: {doc.document_id}\n"
                f"Title: {doc.title}\n"
                f"Classification: {doc.classification.name.capitalize()}\n"
                f"Version: {doc.version}\n"
                f"Effective Date: {doc.effective_date}\n"
                f"Content: {doc.content.strip()}\n"
                f"--- DOCUMENT END ---"
            )
            blocks.append(block)

        context_str = "\n\n".join(blocks)

        if superseded_notes:
            context_str += "\n\n--- VERSION SUPERSEDED NOTES ---\n"
            for note in superseded_notes:
                context_str += f"- {note}\n"

        if conflict_notes:
            context_str += "\n\n--- DOCUMENT DISCREPANCIES ---\n"
            for note in conflict_notes:
                context_str += f"- {note}\n"

        return context_str
