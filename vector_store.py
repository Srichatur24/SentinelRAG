from constants import CHROMA_COLLECTION_NAME, CHROMA_PATH
from classes import User
from utils import embed_text, embed_batch, clearance_rank
import chromadb


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )


    def upsert_documents(self, documents: list) -> None:
        texts = [f"{d.title}\n{d.content}" for d in documents]
        vectors = embed_batch(texts)
        ids = [d.document_id for d in documents]
        metadatas = [
            {
                "title": d.title,
                "classification": d.classification,
                "classification_rank": clearance_rank(d.classification),
                "allowed_departments": ",".join(d.allowed_departments),
                "allowed_roles": ",".join(d.allowed_roles),
                "version": d.version,
                "effective_date": d.effective_date,
            }
            for d in documents
        ]
        self.collection.upsert(
            ids=ids,
            embeddings=vectors,
            metadatas=metadatas,
            documents=[d.content for d in documents],
        )


    def search(self, query: str, user: User, k: int) -> list[dict]:
        qvec = embed_text(query)
        result = self.collection.query(
            query_embeddings=[qvec],
            n_results=k,
            where={"classification_rank": {"$lte": clearance_rank(user.clearance)}},
            include=["metadatas", "documents", "distances"],
        )
        docs = []
        ids = result["ids"][0]
        metadatas = result["metadatas"][0]
        contents = result["documents"][0]
        distances = result["distances"][0]
        for doc_id, meta, content, distance in zip(ids, metadatas, contents, distances):
            allowed_departments = [d for d in meta["allowed_departments"].split(",") if d]
            allowed_roles = [r for r in meta["allowed_roles"].split(",") if r]
            docs.append({
                "document_id": doc_id,
                "title": meta["title"],
                "classification": meta["classification"],
                "allowed_departments": allowed_departments,
                "allowed_roles": allowed_roles,
                "version": meta["version"],
                "effective_date": meta["effective_date"],
                "content": content,
                "similarity": 1 - distance,
            })
        return docs


    def search_unfiltered(self, query: str, k: int) -> list[dict]:
        qvec = embed_text(query)
        result = self.collection.query(
            query_embeddings=[qvec],
            n_results=k,
            include=["metadatas", "distances"],
        )
        docs = []
        ids = result["ids"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]
        for doc_id, meta, distance in zip(ids, metadatas, distances):
            allowed_departments = [d for d in meta["allowed_departments"].split(",") if d]
            allowed_roles = [r for r in meta["allowed_roles"].split(",") if r]
            docs.append({
                "document_id": doc_id,
                "classification": meta["classification"],
                "allowed_departments": allowed_departments,
                "allowed_roles": allowed_roles,
                "similarity": 1 - distance,
            })
        return docs