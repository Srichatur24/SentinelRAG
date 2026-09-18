import json
import os
import streamlit as st
import pandas as pd
from datetime import datetime

from src.models import UserContext, ClearanceLevel, Document
from src.storage.document_store import DocumentStore
from src.storage.audit_logger import AuditLogger
from src.pipeline import SentinelRAGPipeline

# Streamlit Page Config
st.set_page_config(
    page_title="SentinelRAG - Secure Enterprise Research Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .badge-public { background-color: #10B981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
    .badge-internal { background-color: #3B82F6; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
    .badge-confidential { background-color: #F59E0B; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
    .badge-restricted { background-color: #EF4444; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
    .card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Ensure ChromaDB and sample docs are loaded
@st.cache_resource
def get_pipeline():
    p = SentinelRAGPipeline(persist_dir="data/chroma_db", audit_db_path="data/audit.db")
    # Ingest sample docs if empty
    if p.vector_store.collection.count() == 0 and os.path.exists("data/sample_docs.json"):
        store = DocumentStore("data/sample_docs.json")
        p.vector_store.add_documents(store.get_all_documents())
    return p

pipeline = get_pipeline()

# Header
st.markdown('<div class="main-header">🛡️ SentinelRAG: Secure Enterprise Research Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Pre-LLM Authorization Firewall, Conflict Resolution & ChromaDB Vector Retrieval</div>', unsafe_allow_html=True)

# Sidebar: User Context
st.sidebar.header("👤 Employee Context")
persona_choice = st.sidebar.selectbox(
    "Select Employee Persona:",
    [
        "Finance Analyst (U102 - Finance / Internal)",
        "Marketing Manager (U205 - Marketing / Internal)",
        "Finance Director (U301 - Finance / Internal)",
        "Executive Counsel (U401 - Executive / Restricted)",
        "Custom Persona..."
    ]
)

if persona_choice == "Finance Analyst (U102 - Finance / Internal)":
    user_id, role, dept, clearance = "U102", "Finance", "Finance", "Internal"
elif persona_choice == "Marketing Manager (U205 - Marketing / Internal)":
    user_id, role, dept, clearance = "U205", "Marketing", "Marketing", "Internal"
elif persona_choice == "Finance Director (U301 - Finance / Internal)":
    user_id, role, dept, clearance = "U301", "Finance", "Finance", "Internal"
elif persona_choice == "Executive Counsel (U401 - Executive / Restricted)":
    user_id, role, dept, clearance = "U401", "Executive", "Executive", "Restricted"
else:
    user_id = st.sidebar.text_input("User ID", "U999")
    role = st.sidebar.text_input("Role", "Finance")
    dept = st.sidebar.text_input("Department", "Finance")
    clearance = st.sidebar.selectbox("Clearance Level", ["Public", "Internal", "Confidential", "Restricted"], index=1)

current_user = UserContext(
    user_id=user_id,
    role=role,
    department=dept,
    clearance=ClearanceLevel.from_str(clearance)
)

st.sidebar.divider()
st.sidebar.markdown(f"**Active User:** `{current_user.user_id}`")
st.sidebar.markdown(f"**Department:** `{current_user.department}`")
st.sidebar.markdown(f"**Role:** `{current_user.role}`")
badge_class = f"badge-{current_user.clearance.name.lower()}"
st.sidebar.markdown(f"**Clearance:** <span class='{badge_class}'>{current_user.clearance.name.capitalize()}</span>", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.markdown(f"📦 **ChromaDB Vector Index:** `{pipeline.vector_store.collection.count()} Documents`")
st.sidebar.markdown(f"📋 **SQLite Audit Database:** `data/audit.db`")

# Tabs
tab_query, tab_benchmarks, tab_audit, tab_docs = st.tabs([
    "💬 Live RAG Query",
    "🧪 Official Benchmarks (A, B, C)",
    "📜 Compliance Audit Trail",
    "📂 Knowledge Base"
])

# TAB 1: Live RAG Query
with tab_query:
    st.subheader("Enterprise Question & Answer")

    sample_col1, sample_col2, sample_col3 = st.columns(3)
    query_input = st.text_input(
        "Ask a question over internal company documents:",
        value="What is the Q4 revenue forecast?"
    )

    with sample_col1:
        if st.button("Sample: Q4 Revenue Forecast"):
            query_input = "What is the Q4 revenue forecast?"
    with sample_col2:
        if st.button("Sample: Latest Q4 Forecast"):
            query_input = "What is the latest Q4 revenue forecast?"
    with sample_col3:
        if st.button("Sample: Project Apollo Acquisition"):
            query_input = "What is the Project Apollo acquisition target?"

    if st.button("🚀 Run SentinelRAG Query", type="primary"):
        with st.spinner("Executing Sentinel Pipeline (Retrieval -> Gatekeeper -> Resolver -> Synthesis)..."):
            result = pipeline.run(query=query_input, user=current_user)
            audit = pipeline.audit_logger.get_audit(result.query_id)

        st.divider()

        # Step-by-step pipeline view
        col_res1, col_res2 = st.columns([3, 2])

        with col_res1:
            if result.safe_refusal_triggered:
                st.error("### 🛑 Access-Aware Safe Refusal (Option B)")
                st.warning(result.answer)
                st.info("💡 **Zero-Leak Guarantee Enforced**: Relevant classified documents exist in the vector store, but were dropped before prompt augmentation. Content was never exposed.")
            else:
                st.success("### ✅ Authorized Grounded Answer")
                st.write(result.answer)
                if result.citations:
                    st.markdown("**Citations:** " + ", ".join([f"`{c}`" for c in result.citations]))

            if result.superseded_notes:
                st.info("ℹ️ **Version Superseded Notes:**\n" + "\n".join([f"- {n}" for n in result.superseded_notes]))

        with col_res2:
            st.markdown("#### 🛡️ Sentinel Gatekeeper Metrics")
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Retrieved", result.candidate_count)
            m_col2.metric("Authorized", result.authorized_count)
            m_col3.metric("Blocked", result.unauthorized_count)

            if audit and audit.rejection_reasons:
                with st.expander("Inspection: Why Documents Were Blocked", expanded=True):
                    for doc_id, reasons in audit.rejection_reasons.items():
                        st.markdown(f"**Doc `{doc_id}`:**")
                        for r in reasons:
                            st.markdown(f"- ❌ `{r}`")

            st.caption(f"Audit Query ID: `{result.query_id}`")

# TAB 2: Official Benchmarks
with tab_benchmarks:
    st.subheader("Official Benchmark Scenarios Verification")
    st.write("Executes the exact scenarios defined in the hackathon challenge specification.")

    if st.button("▶️ Execute Benchmark Suite", type="primary"):
        scenarios = [
            {
                "id": "A",
                "title": "Test Input A: Authorized Answer",
                "user": "data/test_input_a/user.json",
                "docs": "data/test_input_a/documents.json",
                "prompt": "What is the Q4 revenue forecast?",
                "expected": "Authorized answer citing DOC-101 (120 crore). DOC-102 blocked."
            },
            {
                "id": "B",
                "title": "Test Input B: Relevant but Unauthorized (Zero-Leak)",
                "user": "data/test_input_b/user.json",
                "docs": "data/test_input_b/documents.json",
                "prompt": "What is the Q4 revenue forecast?",
                "expected": "Safe refusal (Option B). DOC-201 blocked. 0 Leaks."
            },
            {
                "id": "C",
                "title": "Test Input C: Authorized Conflict & Version Resolution",
                "user": "data/test_input_c/user.json",
                "docs": "data/test_input_c/documents.json",
                "prompt": "What is the latest Q4 revenue forecast?",
                "expected": "DOC-302 (v2.0, 125 crore) cited. DOC-301 (v1.0) superseded."
            }
        ]

        for sc in scenarios:
            with open(sc["user"], "r") as uf:
                u_data = json.load(uf)
            u = UserContext(**u_data)
            d = DocumentStore(sc["docs"]).get_all_documents()
            res = pipeline.run(query=sc["prompt"], user=u, candidate_pool=d)
            rec = pipeline.audit_logger.get_audit(res.query_id)

            if sc["id"] == "A":
                passed = "120 crore" in res.answer and any("DOC-101" in c for c in res.citations)
            elif sc["id"] == "B":
                passed = res.safe_refusal_triggered and "145 crore" not in res.answer and len(res.citations) == 0
            else:
                passed = "125 crore" in res.answer and any("DOC-302" in c for c in res.citations) and "DOC-301" in rec.superseded_doc_ids

            badge = "✅ PASSED" if passed else "❌ FAILED"
            with st.expander(f"{sc['title']} — {badge}", expanded=True):
                st.markdown(f"**Query:** `{sc['prompt']}`")
                st.markdown(f"**User Context:** `{u.user_id}` ({u.role}, {u.department}, {u.clearance.name})")
                st.markdown(f"**System Response:** {res.answer}")
                st.markdown(f"**Citations:** `{', '.join(res.citations) if res.citations else 'None (Refusal)'}`")
                st.markdown(f"**Authorized Docs:** `{rec.authorized_docs}` | **Blocked Docs:** `{rec.unauthorized_docs}`")

# TAB 3: Audit Trail
with tab_audit:
    st.subheader("Compliance & Traceability Audit Trail")
    st.write("All queries, authorization decisions, and evidence trails persisted in SQLite.")

    audits = pipeline.audit_logger.list_audits(limit=50)
    if not audits:
        st.info("No audit entries yet. Run a query to generate logs!")
    else:
        audit_data = []
        for a in audits:
            audit_data.append({
                "Query ID": a.query_id,
                "Timestamp": a.timestamp,
                "User": f"{a.user_id} ({a.user_role}/{a.user_dept})",
                "Clearance": a.user_clearance,
                "Query": a.query_text,
                "Authorized Docs": len(a.authorized_docs),
                "Blocked Docs": len(a.unauthorized_docs),
                "Refusal": "YES" if a.safe_refusal_triggered else "NO",
                "Citations": ", ".join(a.citations) if a.citations else "-"
            })
        st.dataframe(pd.DataFrame(audit_data), use_container_width=True)

# TAB 4: Knowledge Base Explorer
with tab_docs:
    st.subheader("Internal Enterprise Documents")
    all_docs = DocumentStore("data/sample_docs.json").get_all_documents() if os.path.exists("data/sample_docs.json") else []

    cols = st.columns(2)
    for i, doc in enumerate(all_docs):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="card">
                <h4>{doc.title} <span class="badge-{doc.classification.name.lower()}">{doc.classification.name.capitalize()}</span></h4>
                <p><b>ID:</b> <code>{doc.document_id}</code> | <b>Version:</b> <code>{doc.version}</code> | <b>Effective Date:</b> <code>{doc.effective_date}</code></p>
                <p><b>Allowed Departments:</b> {", ".join(doc.allowed_departments) or "All (*)"}</p>
                <p><b>Allowed Roles:</b> {", ".join(doc.allowed_roles) or "All (*)"}</p>
                <p style="background:#FFFFFF; padding:8px; border-radius:4px; border:1px dashed #CBD5E1;">{doc.content}</p>
            </div>
            """, unsafe_allow_html=True)
