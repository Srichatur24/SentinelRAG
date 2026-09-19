from constants import MONGO_CLIENT, DATABASE_NAME, USERS_COLLECTION, EMBEDDING_MODEL, CLASSIFICATION_LEVELS
from classes import User, Document, AuditLog
from pymongo import MongoClient
from openai import OpenAI

# connect mongodb
mongo_client = MongoClient(MONGO_CLIENT)
db = mongo_client[DATABASE_NAME]
users_collection = db[USERS_COLLECTION]

# openai client for embeddings
openai_client = OpenAI(
    default_headers={
        "Accept-Encoding": "identity"
    }
)

# get the user info
def get_user(user_id: str) -> User:
    user = users_collection.find_one({"user_id": user_id}, {"_id": 0})
    return User(**user)

# get all documents of a collection
def get_documents(collection: str) -> list[Document]:
    docs = db[collection].find({}, {"_id": 0})
    return [Document(**{**doc, "effective_date": str(doc["effective_date"])}) for doc in docs]

# embed a string
def embed_text(text: str) -> list[float]:
    resp = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return resp.data[0].embedding

# embed multiple strings
def embed_batch(texts: list[str]) -> list[list[float]]:
    resp = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in resp.data]

# rank clearance
def clearance_rank(classification: str) -> int:
    return CLASSIFICATION_LEVELS.index(classification)

# authorize
def department_role_authorized(user: User, doc: dict) -> tuple[bool, str]:
    if doc["allowed_departments"] and user.department not in doc["allowed_departments"]:
        return False, f"department '{user.department}' not in {doc['allowed_departments']}"
    if doc["allowed_roles"] and user.role not in doc["allowed_roles"]:
        return False, f"role '{user.role}' not in {doc['allowed_roles']}"
    return True, "authorized"

# sort the documents based on effective_date and version
def resolve_order(docs: list[dict]) -> list[dict]:
    return sorted(docs, key=lambda r: (r["effective_date"], r["version"]), reverse=True)

# remove denails
def evaluate_denials(store: "VectorStore", user: User, query: str, k: int, authorized_ids: set) -> list:
    all_candidates = store.search_unfiltered(query, k)
    decisions = []
    for doc in all_candidates:
        doc_id = doc["document_id"]
        if doc_id in authorized_ids:
            decisions.append({"doc_id": doc_id, "allowed": True, "reason": "authorized", "similarity": round(doc["similarity"], 4)})
            continue
        if clearance_rank(user.clearance) < clearance_rank(doc["classification"]):
            reason = f"clearance '{user.clearance}' insufficient for '{doc['classification']}'"
        else:
            ok, reason = department_role_authorized(user, doc)
        decisions.append({"doc_id": doc_id, "allowed": False, "reason": reason, "similarity": round(doc["similarity"], 4)})
    return decisions

# print audit
def print_audit(audit: AuditLog):
    print("=" * 70)
    print(f"Request ID:  {audit.request_id}")
    print(f"Timestamp:   {audit.timestamp}")
    print(f"User:        {audit.user_id}")
    print(f"Query:       {audit.query}")
    print(f"Candidates:  {audit.candidate_doc_ids}")
    print("Authorization decisions:")
    for d in audit.decisions:
        status = "ALLOW" if d["allowed"] else "DENY "
        print(f"  [{status}] {d['doc_id']:10s} sim={d['similarity']:.4f} - {d['reason']}")
    print(f"Sent to LLM: {audit.docs_sent_to_llm}")
    print(f"Answer:      {audit.answer}")
    print("=" * 70)