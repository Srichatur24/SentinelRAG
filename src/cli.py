import argparse
import json
import os
import sys
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.models import UserContext, Document, ClearanceLevel
from src.storage.document_store import DocumentStore
from src.storage.audit_logger import AuditLogger
from src.pipeline import SentinelRAGPipeline

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(force_terminal=True)


def load_user(user_path: Optional[str], user_id: str, role: str, dept: str, clearance: str) -> UserContext:
    if user_path and os.path.exists(user_path):
        with open(user_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return UserContext(**data)
    return UserContext(
        user_id=user_id or "U101",
        role=role or "General",
        department=dept or "General",
        clearance=ClearanceLevel.from_str(clearance or "Internal"),
    )


def cmd_ingest(args):
    """Ingests documents into the persistent ChromaDB vector store."""
    console.print(Panel(f"[bold cyan]Ingesting Documents into ChromaDB[/bold cyan]\nFile: {args.docs}", border_style="cyan"))
    if not os.path.exists(args.docs):
        console.print(f"[bold red]Error: Document file '{args.docs}' not found.[/bold red]")
        sys.exit(1)

    store = DocumentStore(args.docs)
    docs = store.get_all_documents()

    pipeline = SentinelRAGPipeline(persist_dir=args.persist_dir)
    pipeline.vector_store.add_documents(docs)

    table = Table(title=f"Successfully Ingested {len(docs)} Documents into ChromaDB")
    table.add_column("Doc ID", style="bold green")
    table.add_column("Title")
    table.add_column("Classification", style="yellow")
    table.add_column("Version", justify="center")
    table.add_column("Allowed Depts")
    table.add_column("Allowed Roles")

    for d in docs:
        table.add_row(
            d.document_id,
            d.title,
            d.classification.name.capitalize(),
            d.version,
            ", ".join(d.allowed_departments) or "All (*)",
            ", ".join(d.allowed_roles) or "All (*)"
        )

    console.print(table)
    console.print(f"[bold green][OK] Document vectors successfully persisted in '{args.persist_dir}'[/bold green]")


def cmd_query(args):
    """Executes a query through the SentinelRAG pipeline."""
    user = load_user(args.user, args.user_id, args.role, args.dept, args.clearance)

    candidate_pool = None
    if args.docs and os.path.exists(args.docs):
        store = DocumentStore(args.docs)
        candidate_pool = store.get_all_documents()

    pipeline = SentinelRAGPipeline(persist_dir=args.persist_dir, audit_db_path=args.audit_db)
    result = pipeline.run(query=args.query, user=user, candidate_pool=candidate_pool)

    # Fetch audit record for transparency display
    audit = pipeline.audit_logger.get_audit(result.query_id)

    console.print()
    console.print(Panel(
        f"[bold]Query:[/bold] {args.query}\n"
        f"[bold]User:[/bold] {user.user_id} | Role: {user.role} | Dept: {user.department} | Clearance: {user.clearance.name.capitalize()}\n"
        f"[bold]Audit Query ID:[/bold] {result.query_id}",
        title="[bold cyan]SentinelRAG Query Execution[/bold cyan]",
        border_style="cyan"
    ))

    # Gatekeeper summary table
    table = Table(title="Sentinel Gatekeeper Decisions")
    table.add_column("Metric", style="bold")
    table.add_column("Count / Details", style="white")

    table.add_row("Candidates Retrieved", str(result.candidate_count))
    table.add_row("Authorized Documents", f"[green]{result.authorized_count} permitted[/green]")
    table.add_row("Unauthorized Documents", f"[red]{result.unauthorized_count} blocked (Zero Leak)[/red]")

    if audit and audit.rejection_reasons:
        reasons_text = "\n".join(
            f"- {doc_id}: {'; '.join(reasons)}"
            for doc_id, reasons in audit.rejection_reasons.items()
        )
        table.add_row("Rejection Explanations", reasons_text)

    console.print(table)

    # Answer panel
    if result.safe_refusal_triggered:
        console.print(Panel(
            f"[bold yellow]{result.answer}[/bold yellow]",
            title="[bold red]Access-Aware Safe Refusal (Option B)[/bold red]",
            border_style="red"
        ))
    else:
        citations_str = ", ".join(result.citations) if result.citations else "None"
        console.print(Panel(
            f"{result.answer}\n\n[bold green]Citations:[/bold green] {citations_str}",
            title="[bold green]Authorized Answer[/bold green]",
            border_style="green"
        ))


def cmd_run_tests(args):
    """Automated verification runner for Test Inputs A, B, and C."""
    console.print(Panel("[bold cyan]Running SentinelRAG Test Scenarios (Inputs A, B, C)[/bold cyan]", border_style="cyan"))

    pipeline = SentinelRAGPipeline(audit_db_path=args.audit_db)
    scenarios = [
        {
            "name": "Test Input A: Authorized Answer",
            "user_file": "data/test_input_a/user.json",
            "docs_file": "data/test_input_a/documents.json",
            "query": "What is the Q4 revenue forecast?",
            "check": lambda res, rec: (
                "120 crore" in res.answer
                and any("DOC-101" in c for c in res.citations)
                and not any("DOC-102" in c for c in res.citations)
            )
        },
        {
            "name": "Test Input B: Relevant but Unauthorized (Zero-Leak)",
            "user_file": "data/test_input_b/user.json",
            "docs_file": "data/test_input_b/documents.json",
            "query": "What is the Q4 revenue forecast?",
            "check": lambda res, rec: (
                res.safe_refusal_triggered
                and "145 crore" not in res.answer
                and not any("DOC-201" in c for c in res.citations)
                and len(rec.unauthorized_docs) == 1
            )
        },
        {
            "name": "Test Input C: Authorized Conflict & Version Resolution",
            "user_file": "data/test_input_c/user.json",
            "docs_file": "data/test_input_c/documents.json",
            "query": "What is the latest Q4 revenue forecast?",
            "check": lambda res, rec: (
                "125 crore" in res.answer
                and any("DOC-302" in c for c in res.citations)
                and "DOC-301" in rec.superseded_doc_ids
            )
        }
    ]

    results_table = Table(title="Test Verification Matrix")
    results_table.add_column("Scenario", style="bold")
    results_table.add_column("Query", style="italic")
    results_table.add_column("Result", justify="center")
    results_table.add_column("Evidence & Citations")
    results_table.add_column("Zero-Leak Status")

    all_passed = True

    for s in scenarios:
        user = load_user(s["user_file"], None, None, None, None)
        docs = DocumentStore(s["docs_file"]).get_all_documents()
        res = pipeline.run(query=s["query"], user=user, candidate_pool=docs)
        rec = pipeline.audit_logger.get_audit(res.query_id)

        passed = s["check"](res, rec)
        all_passed = all_passed and passed

        status = "[bold green]PASS [OK][/bold green]" if passed else "[bold red]FAIL [X][/bold red]"
        citations = ", ".join(res.citations) if res.citations else "(None - Refusal)"
        zero_leak = "[green]VERIFIED (0 Leaks)[/green]" if "145 crore" not in res.answer else "[red]LEAK DETECTED[/red]"

        results_table.add_row(
            s["name"],
            s["query"],
            status,
            citations,
            zero_leak
        )

    console.print(results_table)

    if all_passed:
        console.print("[bold green]All 3 official benchmark test inputs PASSED with complete zero-leak verification![/bold green]")
    else:
        console.print("[bold red]Some tests did not pass. Check logs.[/bold red]")


def cmd_audit(args):
    """Displays compliance audit logs from the SQLite database."""
    logger = AuditLogger(db_path=args.audit_db)

    if args.query_id:
        record = logger.get_audit(args.query_id)
        if not record:
            console.print(f"[bold red]Audit record for query ID '{args.query_id}' not found.[/bold red]")
            return
        records = [record]
    else:
        records = logger.list_audits(limit=args.limit)

    table = Table(title=f"Compliance Audit Logs ({len(records)} entries)")
    table.add_column("Query ID", style="bold cyan")
    table.add_column("User & Dept")
    table.add_column("Clearance", style="yellow")
    table.add_column("Query")
    table.add_column("Auth / Unauth Docs")
    table.add_column("Refusal?")
    table.add_column("Citations")

    for r in records:
        table.add_row(
            r.query_id,
            f"{r.user_id} ({r.user_dept})",
            r.user_clearance,
            r.query_text,
            f"[green]{len(r.authorized_docs)}[/green] / [red]{len(r.unauthorized_docs)}[/red]",
            "[red]YES[/red]" if r.safe_refusal_triggered else "[green]NO[/green]",
            ", ".join(r.citations) or "-"
        )

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="SentinelRAG: Secure Enterprise Research Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Ingest Command
    p_ingest = subparsers.add_parser("ingest", help="Ingest documents into ChromaDB vector store")
    p_ingest.add_argument("--docs", default="data/sample_docs.json", help="Path to JSON documents")
    p_ingest.add_argument("--persist-dir", default="data/chroma_db", help="ChromaDB persistence folder")

    # Query Command
    p_query = subparsers.add_parser("query", help="Query the SentinelRAG assistant")
    p_query.add_argument("--query", required=True, help="Natural language employee question")
    p_query.add_argument("--user", help="Path to user.json file")
    p_query.add_argument("--user-id", default="U101", help="User ID")
    p_query.add_argument("--role", default="Finance", help="User Role")
    p_query.add_argument("--dept", default="Finance", help="User Department")
    p_query.add_argument("--clearance", default="Internal", help="User Clearance (Public, Internal, Confidential, Restricted)")
    p_query.add_argument("--docs", help="Optional specific document JSON file to query against")
    p_query.add_argument("--persist-dir", default="data/chroma_db", help="ChromaDB persistence folder")
    p_query.add_argument("--audit-db", default="data/audit.db", help="SQLite audit database path")

    # Run Tests Command
    p_tests = subparsers.add_parser("run-tests", help="Run Test Inputs A, B, and C benchmarks")
    p_tests.add_argument("--audit-db", default="data/audit.db", help="SQLite audit database path")

    # Audit Command
    p_audit = subparsers.add_parser("audit", help="Inspect compliance audit trail")
    p_audit.add_argument("--limit", type=int, default=10, help="Number of records to show")
    p_audit.add_argument("--query-id", help="Filter by specific Query ID")
    p_audit.add_argument("--audit-db", default="data/audit.db", help="SQLite audit database path")

    args = parser.parse_args()

    if args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "query":
        cmd_query(args)
    elif args.command == "run-tests":
        cmd_run_tests(args)
    elif args.command == "audit":
        cmd_audit(args)


if __name__ == "__main__":
    main()
