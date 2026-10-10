#!/usr/bin/env python3
"""
Vidhik Legal RAG Query CLI Tool
===============================
Executes end-to-end evidence-grounded legal question answering:
Hybrid Retrieval -> Evidence Selection -> Qwen Generation -> Claim-to-Evidence Provenance.

Usage:
    python scripts/rag_query.py --query "What is the limitation period for filing an appeal?"
    python scripts/rag_query.py --query "What are the requirements for anticipatory bail under Section 438 CrPC?"
    python scripts/rag_query.py --query "..." --json
"""

import sys
import json
import argparse
import logging
from pathlib import Path

# Ensure prototype root is in PYTHONPATH
PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_DIR))

from rag.engine import LegalRAGEngine


def main():
    parser = argparse.ArgumentParser(
        description="Vidhik Legal RAG Engine CLI (Evidence-Constrained Indian Law Q&A)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Legal question or query to answer using evidence.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="Number of initial retrieval candidates to query (default: 20).",
    )
    parser.add_argument(
        "--max-evidence",
        type=int,
        default=None,
        help="Maximum evidence chunks to present to Qwen (default: from config).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full response as structured JSON.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed debug logs.",
    )

    args = parser.parse_args()

    # Logging configuration
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    print("=" * 80)
    print("VIDHIK LEGAL RAG ENGINE")
    print("=" * 80)
    print("Initializing retrieval and Qwen generator subsystems...")

    try:
        engine = LegalRAGEngine()
    except Exception as e:
        print(f"\n[FATAL ERROR] Engine initialization failed: {e}", file=sys.stderr)
        sys.exit(1)

    query = args.query.strip()
    print(f"\nProcessing Legal Query: '{query}'")
    print(f"Retrieval Top-K: {args.top_k} | Max Evidence: {args.max_evidence}")
    print("-" * 80)

    try:
        response = engine.answer(
            query=query,
            top_k=args.top_k,
            max_evidence=args.max_evidence,
        )
    except Exception as e:
        print(f"\n[ERROR] RAG generation failed: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(response.to_dict(), indent=2))
        return

    # Print formatted human-readable output
    print(f"\nQUESTION\n--------\n{response.query}\n")
    print(f"ANSWER\n------\n{response.answer}\n")

    print(f"CLAIMS\n------")
    if not response.claims:
        print("No attributed claims generated.")
    else:
        for idx, c in enumerate(response.claims, start=1):
            print(f"[{idx}] {c.claim}")
            if c.evidence_ids:
                print(f"    SUPPORTED BY: {', '.join(c.evidence_ids)}")
                for auth in c.authorities:
                    print(f"      ↳ [{auth.evidence_id}] {auth.court} | {auth.case_title} (Page {auth.page_number}, {auth.paragraph_id})")
            else:
                print(f"    SUPPORTED BY: [UNSUPPORTED - GENERAL/INFERENTIAL]")
            print()

    print(f"EVIDENCE\n--------")
    if not response.evidence:
        print("No evidence retrieved or included.")
    else:
        for ev in response.evidence:
            print(f"[{ev['evidence_id']}]")
            print(f"Court: {ev.get('court')} ({ev.get('court_level')})")
            print(f"Case : {ev.get('case_title')}")
            print(f"Date : {ev.get('decision_date')} | Case No: {ev.get('case_number')}")
            print(f"Page : {ev.get('page_number')} | Paragraph: {ev.get('paragraph_id')}")
            print(f"Doc  : {ev.get('document_id')} (Point: {ev.get('qdrant_point_id')})")
            
            text_snippet = ev.get('text', '').strip()
            if len(text_snippet) > 280:
                text_snippet = text_snippet[:280] + " ... [TRUNCATED]"
            print(f"Text : {text_snippet}\n")

    print(f"LIMITATIONS\n-----------")
    print(f"{response.limitations or 'None identified.'}\n")

    print(f"CONFIDENCE\n----------")
    print(f"{response.confidence.upper()} (Execution Time: {response.execution_time_seconds:.2f}s)\n")
    print("=" * 80)


if __name__ == "__main__":
    main()
