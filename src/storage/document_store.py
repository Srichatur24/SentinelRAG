import json
from typing import List, Dict, Optional
from src.models import Document


class DocumentStore:
    """Manages raw document ingestion, JSON persistence, and in-memory document caching."""

    def __init__(self, json_path: Optional[str] = None):
        self._documents: Dict[str, Document] = {}
        if json_path:
            self.load_from_json(json_path)

    def load_from_json(self, json_path: str) -> List[Document]:
        """Loads and parses documents from a JSON file."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        docs = []
        if isinstance(data, list):
            for item in data:
                doc = Document(**item)
                self._documents[doc.document_id] = doc
                docs.append(doc)
        elif isinstance(data, dict):
            doc = Document(**data)
            self._documents[doc.document_id] = doc
            docs.append(doc)
        return docs

    def add_document(self, doc: Document) -> None:
        self._documents[doc.document_id] = doc

    def get_document(self, doc_id: str) -> Optional[Document]:
        return self._documents.get(doc_id)

    def get_all_documents(self) -> List[Document]:
        return list(self._documents.values())

    def clear(self) -> None:
        self._documents.clear()
