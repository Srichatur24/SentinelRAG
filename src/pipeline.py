import uuid
from datetime import datetime, timezone
from typing import List, Optional
from src.models import UserContext, Document, QueryResult, AuditRecord
from src.storage.audit_logger import AuditLogger
from src.rag.vector_store import ChromaVectorStore
from src.rag.retriever import SemanticRetriever
from src.rag.context_builder import ContextBuilder
from src.rag.generator import GroundedGenerator
from src.agents.query_planner import QueryPlanner
from src.agents.authorization_gate import AuthorizationGatekeeper
from src.agents.conflict_resolver import ConflictResolver


class SentinelRAGPipeline:
    """Master Orchestration Pipeline for SentinelRAG.
    
    Coordinates Query Planning, Semantic Retrieval, Deterministic Pre-LLM
    Authorization, Conflict Resolution, Context Augmentation, Grounded Generation,
    and SQLite Audit Logging.
    """

    def __init__(
        self,
        persist_dir: str = "data/chroma_db",
        audit_db_path: str = "data/audit.db"
    ):
        self.vector_store = ChromaVectorStore(persist_dir=persist_dir)
        self.retriever = SemanticRetriever(self.vector_store)
        self.planner = QueryPlanner()
        self.gatekeeper = AuthorizationGatekeeper()
        self.conflict_resolver = ConflictResolver()
        self.context_builder = ContextBuilder()
        self.generator = GroundedGenerator()
        self.audit_logger = AuditLogger(db_path=audit_db_path)

    def run(
        self,
        query: str,
        user: UserContext,
        candidate_pool: Optional[List[Document]] = None
    ) -> QueryResult:
        """Executes the SentinelRAG pipeline for a given user query."""
        query_id = f"QRY-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Step 1: Query Planning
        query_plan = self.planner.plan(query, user)

        # Step 2: Semantic Candidate Retrieval (R)
        candidates = self.retriever.retrieve_candidates(
            query_plan=query_plan,
            top_k=10,
            candidate_pool=candidate_pool
        )
        candidate_ids = [d.document_id for d in candidates]

        # Step 3: Deterministic Pre-LLM Authorization Gatekeeper [SENTINEL FIREWALL]
        authorized_docs, unauthorized_docs, decisions = self.gatekeeper.evaluate(
            candidate_docs=candidates,
            user=user
        )
        authorized_ids = [d.document_id for d in authorized_docs]
        unauthorized_ids = [d.document_id for d in unauthorized_docs]
        rejection_reasons = {
            doc_id: dec.reasons
            for doc_id, dec in decisions.items()
            if not dec.authorized
        }

        # Step 4: Conflict and Version Resolution (Authorized documents only)
        (
            authoritative_docs,
            superseded_docs,
            superseded_notes,
            conflict_notes
        ) = self.conflict_resolver.resolve(authorized_docs)

        resolved_auth_id = authoritative_docs[0].document_id if authoritative_docs else None
        superseded_ids = [d.document_id for d in superseded_docs]

        # Step 5: Context Augmentation (A)
        # Guarantees that ONLY authoritative authorized documents are formatted into prompt context
        context_str = self.context_builder.build_context(
            authoritative_docs=authoritative_docs,
            superseded_notes=superseded_notes,
            conflict_notes=conflict_notes
        )

        # Step 6: Grounded Generation (G)
        answer, citations = self.generator.generate_response(
            query=query,
            user=user,
            authoritative_docs=authoritative_docs,
            superseded_notes=superseded_notes,
            conflict_notes=conflict_notes,
            candidates_found=len(candidates) > 0,
            unauthorized_count=len(unauthorized_docs)
        )

        safe_refusal_triggered = len(unauthorized_docs) > 0 and len(authoritative_docs) == 0
        evidence_used = [d.document_id for d in authoritative_docs]

        # Step 7: SQLite Audit Logging
        audit_record = AuditRecord(
            query_id=query_id,
            timestamp=timestamp,
            user_id=user.user_id,
            user_role=user.role,
            user_dept=user.department,
            user_clearance=user.clearance.name.capitalize(),
            query_text=query,
            retrieved_candidates=candidate_ids,
            authorized_docs=authorized_ids,
            unauthorized_docs=unauthorized_ids,
            rejection_reasons=rejection_reasons,
            resolved_authoritative_doc_id=resolved_auth_id,
            superseded_doc_ids=superseded_ids,
            evidence_used=evidence_used,
            final_answer=answer,
            citations=citations,
            safe_refusal_triggered=safe_refusal_triggered
        )
        self.audit_logger.log_audit(audit_record)

        return QueryResult(
            query=query,
            answer=answer,
            citations=citations,
            superseded_notes=superseded_notes,
            candidate_count=len(candidates),
            authorized_count=len(authorized_docs),
            unauthorized_count=len(unauthorized_docs),
            query_id=query_id,
            safe_refusal_triggered=safe_refusal_triggered
        )
