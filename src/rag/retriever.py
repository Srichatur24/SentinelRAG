from typing import List, Optional
from src.models import Document
from src.agents.query_planner import QueryPlan
from src.rag.vector_store import ChromaVectorStore


class SemanticRetriever:
    """Retrieves candidate documents from the knowledge base using semantic vector search.
    
    IMPORTANT: This component intentionally retrieves ALL relevant candidates without
    filtering for clearance. The candidate set is then handed directly to the
    deterministic Authorization Gatekeeper.
    """

    def __init__(self, vector_store: ChromaVectorStore):
        self.vector_store = vector_store

    def retrieve_candidates(
        self,
        query_plan: QueryPlan,
        top_k: int = 10,
        candidate_pool: Optional[List[Document]] = None
    ) -> List[Document]:
        """Retrieves candidate documents relevant to the query plan.
        
        If a specific candidate_pool is provided (e.g. during isolated test scenario execution),
        it indexes that pool or filters from it. Otherwise, it queries the persistent ChromaDB.
        """
        query_str = query_plan.cleaned_query or query_plan.original_query

        if candidate_pool is not None:
            # When candidate_pool is explicitly passed (e.g., test input documents.json),
            # all documents in the pool are evaluated by the Authorization Gatekeeper.
            return candidate_pool

        # Query persistent ChromaDB vector store
        return self.vector_store.search(query_str, n_results=top_k)
