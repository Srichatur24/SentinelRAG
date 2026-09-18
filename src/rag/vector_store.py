import os
import json
from typing import List, Optional
import chromadb
from chromadb.config import Settings
from src.models import Document, ClearanceLevel


class ChromaVectorStore:
    """Persistent on-disk Vector Database powered by ChromaDB.
    
    Indexes document titles and content, computes embeddings, and performs
    fast nearest-neighbor similarity search.
    """

    def __init__(self, persist_dir: str = "data/chroma_db", collection_name: str = "sentinel_docs"):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, docs: List[Document]) -> None:
        """Ingests, embeds, and stores documents persistently in ChromaDB."""
        if not docs:
            return

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[dict] = []

        for doc in docs:
            ids.append(doc.document_id)
            # Embed both title and content for optimal semantic retrieval
            text = f"{doc.title}\n{doc.content}"
            documents.append(text)

            meta = {
                "document_id": doc.document_id,
                "title": doc.title,
                "classification": doc.classification.name.capitalize(),
                "classification_val": int(doc.classification.value),
                "version": doc.version,
                "effective_date": doc.effective_date or "",
                "allowed_departments": json.dumps(doc.allowed_departments),
                "allowed_roles": json.dumps(doc.allowed_roles),
                "content": doc.content,
                "owner": doc.owner or "",
            }
            metadatas.append(meta)

        # Upsert documents into Chroma collection
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def search(self, query_text: str, n_results: int = 10, distance_threshold: float = 0.60) -> List[Document]:
        """Searches ChromaDB for the top candidate documents matching the query.
        
        Applies distance_threshold to filter out semantically unrelated documents.
        """
        count = self.collection.count()
        if count == 0:
            return []

        limit = min(n_results, count)
        results = self.collection.query(
            query_texts=[query_text],
            n_results=limit
        )

        matched_docs: List[Document] = []
        if results and results.get("metadatas") and results.get("distances"):
            meta_list = results["metadatas"][0]
            dist_list = results["distances"][0]
            for meta, dist in zip(meta_list, dist_list):
                if dist > distance_threshold:
                    continue  # Exclude semantically irrelevant documents
                doc = Document(
                    document_id=meta["document_id"],
                    title=meta["title"],
                    classification=ClearanceLevel.from_str(meta["classification"]),
                    allowed_departments=json.loads(meta.get("allowed_departments", "[]")),
                    allowed_roles=json.loads(meta.get("allowed_roles", "[]")),
                    version=meta.get("version", "1.0"),
                    effective_date=meta.get("effective_date", ""),
                    content=meta.get("content", ""),
                    owner=meta.get("owner") or None,
                )
                matched_docs.append(doc)

        return matched_docs

    def get_all_documents(self) -> List[Document]:
        """Returns all documents currently stored in the vector collection."""
        count = self.collection.count()
        if count == 0:
            return []

        results = self.collection.get()
        all_docs: List[Document] = []
        if results and results.get("metadatas"):
            for meta in results["metadatas"]:
                doc = Document(
                    document_id=meta["document_id"],
                    title=meta["title"],
                    classification=ClearanceLevel.from_str(meta["classification"]),
                    allowed_departments=json.loads(meta.get("allowed_departments", "[]")),
                    allowed_roles=json.loads(meta.get("allowed_roles", "[]")),
                    version=meta.get("version", "1.0"),
                    effective_date=meta.get("effective_date", ""),
                    content=meta.get("content", ""),
                    owner=meta.get("owner") or None,
                )
                all_docs.append(doc)
        return all_docs

    def clear(self) -> None:
        """Deletes all entries in the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
