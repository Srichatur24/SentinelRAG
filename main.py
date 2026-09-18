from constants import K, AGENT_MODEL
from classes import User, AuditLog, RequestContext
from vector_store import VectorStore
from utils import department_role_authorized, evaluate_denials, resolve_order
import uuid
from datetime import datetime, timezone
from openai import AsyncOpenAI
from agents import Agent, Runner, RunContextWrapper, set_default_openai_client
from agents.decorators import tool


set_default_openai_client(AsyncOpenAI(default_headers={"Accept-Encoding": "identity"}))

# tool for agent to search for documents
@tool
def search_authorized_documents(wrapper: RunContextWrapper[RequestContext], query: str) -> str:
    '''
    '''
    ctx: RequestContext = wrapper.context
    classification_filtered = ctx.store.search(query, ctx.user, K)
    authorized = []
    for doc in classification_filtered:
        ok, reason = department_role_authorized(ctx.user, doc)
        if ok:
            authorized.append(doc)
    authorized_ids = {r["document_id"] for r in authorized}
    ctx.audit.decisions = evaluate_denials(ctx.store, ctx.user, query, K, authorized_ids)
    ctx.audit.candidate_doc_ids = [d["doc_id"] for d in ctx.audit.decisions]
    ordered = resolve_order(authorized)
    ctx.audit.docs_sent_to_llm = [r["document_id"] for r in ordered]
    if not ordered:
        return "NO_AUTHORIZED_DOCUMENTS_FOUND"
    blocks = []
    for r in ordered:
        blocks.append(
            f"document_id={r['document_id']} version={r['version']} effective_date={r['effective_date']} "
            f"title=\"{r['title']}\" content=\"{r['content']}\""
        )
    return "\n".join(blocks)

# get agent instructions
with open('instructions.txt', 'r') as f:
    instructions = f.read()

# agent
agent = Agent[RequestContext](
    name="agent",
    instructions=instructions,
    tools=[search_authorized_documents],
    model=AGENT_MODEL
)

# start
async def answer_question(query: str, user: User, store: VectorStore) -> AuditLog:
    audit = AuditLog(
        request_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        user_id=user.user_id,
        query=query,
    )
    ctx = RequestContext(user=user, store=store, audit=audit)
    result = await Runner.run(agent, query, context=ctx)
    audit.answer = result.final_output
    return audit