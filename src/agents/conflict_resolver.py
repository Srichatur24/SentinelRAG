import re
from typing import List, Tuple, Dict
from datetime import datetime
from src.models import Document


def parse_version(v_str: str) -> Tuple[int, ...]:
    """Parses a version string like '2.0', 'v2.1', '1' into a numeric tuple."""
    cleaned = re.sub(r"[^0-9.]", "", v_str)
    parts = []
    for p in cleaned.split("."):
        if p.isdigit():
            parts.append(int(p))
    return tuple(parts) if parts else (0,)


def parse_date(d_str: str) -> datetime:
    """Parses an ISO date string like '2026-09-01', fallback to epoch."""
    if not d_str:
        return datetime.min
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%B %d, %Y"):
        try:
            return datetime.strptime(d_str.strip(), fmt)
        except ValueError:
            continue
    return datetime.min


def normalize_title(title: str) -> str:
    """Normalizes document titles for grouping (e.g. 'Q4 Revenue Forecast' -> 'q4 forecast')."""
    t = title.lower()
    t = re.sub(r"revenue", "", t)
    t = re.sub(r"[^a-z0-9]", " ", t)
    return " ".join(t.split())


class ConflictResolver:
    """Resolves version discrepancies, effective dates, and outdated content among authorized documents."""

    def resolve(
        self, authorized_docs: List[Document]
    ) -> Tuple[List[Document], List[Document], List[str], List[str]]:
        """Analyzes authorized documents, selecting the authoritative active version
        and flagging superseded or conflicting versions.
        
        Returns:
            authoritative_docs: List of active documents to synthesize into the answer.
            superseded_docs: List of older superseded documents.
            superseded_notes: List of user-facing notes explaining superseded versions.
            conflict_notes: List of notes explaining any contradictions between active versions.
        """
        if not authorized_docs:
            return [], [], [], []

        if len(authorized_docs) == 1:
            return [authorized_docs[0]], [], [], []

        # Group documents by normalized topic/title
        groups: Dict[str, List[Document]] = {}
        for doc in authorized_docs:
            key = normalize_title(doc.title)
            groups.setdefault(key, []).append(doc)

        authoritative_docs: List[Document] = []
        superseded_docs: List[Document] = []
        superseded_notes: List[str] = []
        conflict_notes: List[str] = []

        for key, docs in groups.items():
            if len(docs) == 1:
                authoritative_docs.append(docs[0])
                continue

            # Sort documents by (effective_date, version) descending
            sorted_docs = sorted(
                docs,
                key=lambda d: (parse_date(d.effective_date), parse_version(d.version)),
                reverse=True
            )

            primary = sorted_docs[0]
            primary_date = parse_date(primary.effective_date)
            primary_ver = parse_version(primary.version)

            group_active: List[Document] = [primary]

            for other in sorted_docs[1:]:
                other_date = parse_date(other.effective_date)
                other_ver = parse_version(other.version)

                # Check if identical version and date -> tie-break requirement: keep both and note discrepancy
                if other_date == primary_date and other_ver == primary_ver:
                    group_active.append(other)
                    if other.content.strip() != primary.content.strip():
                        conflict_notes.append(
                            f"Discrepancy detected between {primary.document_id} and {other.document_id}: "
                            f"both share version {primary.version} and effective date {primary.effective_date}, "
                            f"but have differing content."
                        )
                else:
                    # other is superseded by primary
                    superseded_docs.append(other)
                    superseded_notes.append(
                        f"{other.document_id} (v{other.version}, {other.effective_date}) is superseded by "
                        f"{primary.document_id} (v{primary.version}, {primary.effective_date})."
                    )

            authoritative_docs.extend(group_active)

        return authoritative_docs, superseded_docs, superseded_notes, conflict_notes
