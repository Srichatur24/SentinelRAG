# SentinelRAG

## 1. Team Details

**Team Name / ID:** Pragyaan Pythons

**Team Lead:** Mohammed Emad Uddin

**Team Members:**

<!--
One line per person, including the team lead. Role is optional.
Pick one, combine two, write your own, or leave it blank:
  Agent Whisperer (agents, prompts, LLMs)
  Backend Developer
  Frontend Developer
  UI/UX Designer
  Integrations Engineer (APIs, tools, connecting services)
  Data Engineer (data, databases, retrieval)
  Product & Pitch Lead (idea, presentation, demo)
  Cool Team Member (a bit of everything)
-->

- Mohammed Emad Uddin
- Gurram Pardha Venkata Sai Kumar
- Punna Srichatur
- Mohd Farhan Ahmed

**Repo Link (Optional):** N/A

**Demo Link (Optional):** N/A

---

## 2. Problem Statement

<!-- Paste the full problem statement exactly as it was given to you. Don't shorten, fix, or reword anything. No character limit here. -->

The Employee Who Asked for Too Much

Context
Your company has thousands of internal documents. Employees can ask questions such as:
"What was the revenue forecast for Q4?"
An AI assistant should be able to search documents, understand them, compare information and answer questions. But not every employee is allowed to access every document. Documents have classifications:
Public
Internal
Confidential
Restricted
Different employees have different permissions. The assistant must answer a question without exposing information that the employee is not authorized to access. Documents may also:
contradict each other 
be outdated 
have different versions 
contain incomplete information 
Critical requirement
An unauthorized document must never be provided to the LLM simply because it is relevant to the question.

The Challenge
Build a secure enterprise research agent that answers employee questions over internal documents while enforcing authorization. Documents have classifications and access rules. Relevant information that the requesting employee is not authorized to access must never be provided to the language model or revealed in the final answer.
Core Requirements
Accept a natural-language employee question and user context.
Ingest documents with classification, department, owner, and access-control metadata.
Search for relevant candidates but enforce authorization before document content reaches the LLM.
Handle outdated and conflicting authorized documents.
Return an answer with citations to the evidence the user is allowed to access.
Record an audit trail of the request, authorization decisions, and evidence used.
Safely respond when the answer exists only in documents the user cannot access.
Inputs Students Can Test
Test Input A — Authorized answer
user.json:
{
  "user_id": "U102",
  "role": "Finance",
  "department": "Finance",
  "clearance": "Internal"
}

documents.json:
[
  {
    "document_id": "DOC-101",
    "title": "Q4 Revenue Forecast",
    "classification": "Internal",
    "allowed_departments": ["Finance"],
    "allowed_roles": ["Finance"],
    "version": "2.0",
    "effective_date": "2026-09-01",
    "content": "Q4 projected revenue is 120 crore."
  },
  {
    "document_id": "DOC-102",
    "title": "Engineering Roadmap",
    "classification": "Internal",
    "allowed_departments": ["Engineering"],
    "allowed_roles": ["Engineer"],
    "version": "1.0",
    "effective_date": "2026-08-01",
    "content": "The next platform release is planned for October."
  }
]

prompt:
"What is the Q4 revenue forecast?
Test Input B — Relevant but unauthorized
user.json:
{
  "user_id": "U205",
  "role": "Marketing",
  "department": "Marketing",
  "clearance": "Internal"
}

documents.json:
[
  {
    "document_id": "DOC-201",
    "title": "Q4 Revenue Forecast",
    "classification": "Restricted",
    "allowed_departments": ["Executive"],
    "allowed_roles": ["Executive"],
    "version": "3.0",
    "effective_date": "2026-09-01",
    "content": "Q4 projected revenue is 145 crore."
  }
]

prompt:
"What is the Q4 revenue forecast?
Test Input C — Authorized conflict
user.json:
{
  "user_id": "U301",
  "role": "Finance",
  "department": "Finance",
  "clearance": "Internal"
}

documents.json:
[
  {
    "document_id": "DOC-301",
    "title": "Q4 Forecast",
    "classification": "Internal",
    "allowed_departments": ["Finance"],
    "allowed_roles": ["Finance"],
    "version": "1.0",
    "effective_date": "2026-06-01",
    "content": "Q4 projected revenue is 110 crore."
  },
  {
    "document_id": "DOC-302",
    "title": "Q4 Forecast",
    "classification": "Internal",
    "allowed_departments": ["Finance"],
    "allowed_roles": ["Finance"],
    "version": "2.0",
    "effective_date": "2026-09-01",
    "content": "Q4 projected revenue is 125 crore."
  }
]

prompt:
"What is the latest Q4 revenue forecast?

---

## 3. TL;DR

<!-- One line each. A judge should get your idea in 10 seconds. -->

**Problem:** Deploying AI assistants to query company docs risks leaking Confidential/Restricted content to unauthorized employees.

**Solution:** Sentinel RAG performs document clearance before the LLM receives data, guaranteeing safe, secure answers.

**Who benefits:** Employees get fast, cited answers and the company avoids cross classification data leaks.

---

## 4. Scope of the Project

**What are you building?**

A secure research agent pipeline that retrieves candidate documents, enforces deterministic authorization before LLM access, resolves conflicts across authorized documents that contradict, are outdated, have different versions, or contain incomplete information, then returns a cited answer with a full audit log.

**How does it solve the problem statement?**

Authorization runs as deterministic and rule based code between retrieval and LLM generation, ensuring unauthorized, outdated, conflicting, version mismatched, or incomplete content is removed before prompt construction and not just filtered from the final answer.

**Key features you're building for this hackathon:**

<!-- Up to 5 features. -->

- Pre LLM authorization gate that blocks unauthorized docs before they ever reach the model
- Role/department/clearance based access control engine matching document metadata
- Conflict & version resolver to pick the latest authorized document by effective date
- Citation backed answers referencing only documents the user can access
- Full audit trail logging the request, authorization decisions, and evidence used

**What are you deliberately NOT doing? (Optional)**

Not building SSO or enterprise identity integration, production scale vector DB, or multi user admin dashboard.

---

## 5. Why an Agentic Approach?

<!-- This is an Agentic AI hackathon, so this is one of the most important answers in the file. Be specific. "It uses an LLM" is not an answer. -->

**What does your agent decide or do on its own?**

<!-- e.g. plans its steps, picks which tool to call, handles unexpected input, retries when something fails, hands work to another agent. -->

The agent interprets the question, plans to selects relevant documents, handles and resolves conflicts across contradictory, outdated, different version, or incomplete documents by choosing the authorized authoritative version, and safely refuses when no authorized evidence exists.

**Why wouldn't a fixed script, if-else rules, or a simple chatbot be enough?**

A chatbot can't reason over ambiguous, conflicting, outdated documents or explain trade offs. Using if-else rules can't summarize, compare versions, or generate natural, cited answers from varied phrasing. Hence, fixed scripts fail under dynamic scenarios.

---

## 6. Who It's For & What Changes

**Who or what is this for?**

<!-- Doesn't have to be end users. It could be people, a team, a business, developers, or an internal system or process. -->

Enterprises with restricted document access (Finance, HR, Legal, Executive) that need safe internal QnA over sensitive knowledge bases.

**The world today, without your solution:**

<!-- What happens right now? Who struggles, and what does it cost them in time, money, effort, errors, or missed opportunities? -->

Employees email document owners or search shared drives manually, often finding outdated or wrong version files, or accidentally get exposed to information above their clearance through loosely secured chat tools.

**The world with your solution, fully built and scaled to production:**

<!-- Imagine your whole idea is built properly and used by everyone it's meant for. What's different? -->

Every employee gets instant and correctly scoped answers from live company knowledge, with zero cross classification leaks and a complete compliance ready audit trail for every query.

**What your hackathon build actually delivers today:**

<!-- Of everything you proposed, which part have you built, and which part of the problem does that piece solve right now? A small piece that truly works is a great answer. -->

A working pipeline that ingests sample documents with access control metadata, enforces authorization before LLM access, resolves contradictory, outdated, different version or incomplete information and returns a cited answer or safe refusal with end to end audit logging.


**Before vs. After**

<!--
2 to 4 rows. Pick things that change: time, cost, effort, accuracy, scale, reach, manual work, risk.
Max 80 characters per cell. Replace the example row with your own.
-->

| What Changes | Today | With Our Current Build | At Production Scale |
|--------------|-------|------------------------|---------------------|
| Time to get an authorized answer | Hours to days | Seconds via querying | Under 10 seconds |
| Risk of unauthorized data exposure | High, depends on manual discretion | Near zero, enforced pre LLM | Near zero, audited continuously |
| Compliance traceability | Little to none | Full audit log per query | Searchable audit logs |
| Handling conflicting document versions | Manual checking by employee | Auto resolved by effective date | Auto resolved with owner alerts |

---

## 7. Architecture & Agents

<!--
All the examples in this section describe ONE made-up project, a college helpdesk agent,
so you can see how the parts fit together. Aim for this level of detail, no more.
You don't need to list every library or every function.
-->

**How is your system put together?**

<!--
Example:
Students ask questions in a web chat. A Triage Agent sorts each message, an Answer Agent
replies using college policy documents, and anything needing a human becomes a helpdesk ticket.
-->

An employee submits a question with their user context via CLI or API. A Query Planning Agent interprets intent, a Retrieval Agent fetches candidate documents, an Authorization Gatekeeper (non LLM) strips unauthorized ones, a Conflict Resolver picks the authoritative version and an Answer Synthesis Agent generates the cited reply with every step logged.

### 7.1 Agents

<!--
One line per agent. For each one, say what its job is, which model it uses and why that model
fits the job, and what it talks to (other agents, APIs, databases, services).

Example:
- **Triage Agent:** Reads each message and decides if it's a policy question, a complaint, or needs a human. Uses Llama 3.1 8B locally, since sorting is simple and student data stays on our machine. Talks to the Answer Agent and Web Chat.
- **Answer Agent:** Answers policy questions from college documents and files a ticket when approval is needed. Uses Claude Sonnet because it handles long policy text and reasons well about exceptions. Talks to College Docs Store and Helpdesk Ticket API.
-->

- **Query Planning Agent:** Parses the question and user context, decides retrieval strategy. Talks to Retrieval Agent.
- **Retrieval Agent:** Searches the document store for relevant candidates by keyword and metadata match. Uses no LLM (deterministic search). Talks to Document Store, Authorization Gatekeeper.
- **Authorization Gatekeeper:** Deterministic rule engine checking classification, department, role, clearance to discard unauthorized docs. Talks to Audit Log DB, Conflict Resolver.
- **Conflict Resolver:** Among authorized docs only, resolves duplicates/contradictions by version and effective date, flags superseded content. Talks to Answer Synthesis Agent.
- **Answer Synthesis Agent:** Generates the final natural language answer with citations strictly from resolved authorized evidence, or a safe refusal. Talks to Audit Log DB, API interface.

### 7.2 Services, APIs, Databases & Memory

<!--
One line for everything that isn't an agent: databases, APIs, external services, tools,
and your interface (web app, bot, CLI). Say what it is, what it does, and who uses it.
Mention if it's mocked.

Example:
- **College Docs Store (Chroma vector database):** Holds fee, exam, and hostel policy PDFs. Used by the Answer Agent.
- **Helpdesk Ticket API (mocked):** Creates a ticket for the right college office. Used by the Answer Agent.
- **Web Chat (Streamlit):** Where students type questions and see answers. Talks to the Triage Agent.
-->

- **Document Store (JSON file, mocked vector DB):** Holds documents with classification, department, role, version, effective_date metadata. Used by Retrieval Agent.
- **Audit Log DB (SQLite):** Stores each request, authorization decision per document, and evidence used in the final answer. Used by Authorization Gatekeeper and Answer Synthesis Agent.
- **User Context Loader (mocked):** Supplies role/department/clearance from user.json. Used by Authorization Gatekeeper.
- **CLI Interface (Python script):** Accepts the question and user.json, prints the answer and citations. Used by the employee.

**How does your system remember things (memory & state)?**

<!--
Example:
Each chat keeps its last 10 messages in session memory so follow-up questions make sense.
Tickets are saved in SQLite so students can check their status later.
-->

No conversation memory across turns in this build. Each query is handled statelessly and only the SQLite audit log persists across requests for traceability.

**Diagram Link (Optional):** N/A

### 7.3 Example Walkthrough

<!--
Take ONE realistic input and show how it moves through your system: which agent picks it up,
what gets passed on, which tools or databases are used, and what comes out at the end.
Up to 8 steps. If the flow branches, use 3a / 3b.

Example:
**Example input:** A student types "Can I pay my semester fee late? I'm waiting on my scholarship."

1. [Web Chat] Sends the message and the student's ID to the Triage Agent.
2. [Triage Agent] Classifies it as a fee-policy question and passes it to the Answer Agent.
3. [Answer Agent] Finds the late-fee policy (uses: College Docs Store) and sees scholarship cases need approval.
4. [Answer Agent] Explains the policy and files an approval request (uses: Helpdesk Ticket API).
5. [Web Chat] Shows the student the answer and their ticket number.

**Final output:** A clear answer quoting the late-fee policy, plus a ticket raised with the accounts office.
-->

**Example input:** Finance employee U301 asks "What is the latest Q4 revenue forecast?" (Test Input C).

1. CLI Sends question and user.json (Finance, Internal clearance) to Query Planning Agent.
2. Query Planning Agent Extracts intent "Q4 revenue forecast lookup," passes to Retrieval Agent.
3. Retrieval Agent Finds DOC-301 and DOC-302 as candidates (uses: Document Store).
4. Authorization Gatekeeper Confirms both pass Finance/Internal rules; logs decision (uses: Audit Log DB).
5. Conflict Resolver Compares versions; selects DOC-302 (v2.0, 2026-09-01) as authoritative, flags DOC-301 as superseded.
6. Answer Synthesis Agent Generates answer citing DOC-302, notes the older figure is outdated.
7. Answer Synthesis Agent Writes final evidence trail to Audit Log DB.
8. CLI Displays the answer, citation, and superseded-doc note to the user.

**Final output:** "Latest Q4 forecast: 125 crore (DOC-302, v2.0). Note: DOC-301 (v1.0) is superseded." plus a logged audit entry

**Anything special about how your workflow runs? (Optional)**

<!--
An algorithm you use, how agents decide what to do next, routing logic, loops, agents working
in parallel, scoring, self-checks. Anything you want us to notice.

Example:
The Triage Agent gives a confidence score with every decision. Below 0.7, the message skips the
Answer Agent and goes straight to a human, so students never get a confident wrong answer.
-->

The Authorization Gatekeeper is purely deterministic, never an LLM call so that no document content enters any LLM prompt until it clears the ACL check, removing prompt injection or leakage risk from retrieval stage content.

---

## 8. Tech Stack

<!-- Write N/A for any row that doesn't apply. Models are already listed per agent in 7.1. Max 60 characters per cell. -->

| Layer | Technology |
|-------|------------|
| Frontend / Interface | CLI (Python script) |
| Backend | Python |
| Agent Framework | Custom code (LangGraph-style orchestration) |
| Database / Storage | JSON document store + SQLite audit log |
| Hosting | Local machine |
| Other | N/A |

---

## 9. What to Expect From Our Current Build

<!--
Be honest. Unfinished, faked, or hard-coded parts are completely normal at a hackathon.
Telling us means we judge what you actually built, and that works in your favour.
Max 120 characters per bullet.
-->

**Working:**

- Pre LLM authorization gate blocking unauthorized documents
- Version and conflict resolution for authorized documents
- Cited answers and safe refusals when unauthorized
- Full audit trail logging per query

**Partly working, mocked, or hard-coded:**

- Document store uses static JSON sample data, not a live vector DB
- Retrieval uses keyword/metadata matching instead of embeddings

**Not working or not built yet:**

- Semantic vector search, web UI, multi turn conversation memory

**What we'd most like to be judged on:**

The Authorization Gatekeeper's zero leak guarantee that is unauthorized document content is provably stripped before any LLM prompt is constructed, verified via the audit log.

---

## 10. Future Scope

<!-- 2 or 3 things you're NOT building yet but plan to. If you clear the checkpoint, you may be asked to build one of them, so keep them concrete and doable. -->

### Idea 1

**Name:** Semantic Vector Retrieval

**What it is:** Replace keyword matching with embedding-based semantic search over the document store.

**Why it matters:** Improves recall for paraphrased or vague employee questions.

**How we'd build it:** Add a vector DB (Chroma), embed documents at ingestion, query by similarity.

**Done when:** Paraphrased test queries return the same correct authorized documents as exact phrase queries.

### Idea 2

**Name:** Auto-Classification Ingestion Pipeline

**What it is:** Automatically tag new documents with classification, department, and role metadata on upload.

**Why it matters:** Removes manual tagging errors that could cause leaks or wrongful denials.

**How we'd build it:** Use an LLM classifier plus human review before documents go live.

**Done when:** Newly ingested sample docs get correct metadata tags without manual entry.

### Idea 3 (Optional)

**Name:** Audit Trail Dashboard

**What it is:** A web dashboard visualizing every query, authorization decision, and evidence used.

**Why it matters:** Gives compliance teams a searchable, real time view for audits.

**How we'd build it:** Build a Streamlit/React frontend reading from the Audit Log DB.

**Done when:** A compliance reviewer can filter and inspect any past query's decisions in the UI.

---

## 11. Additional Notes (Optional)

<!-- Anything else you'd like us to know. -->

N/A