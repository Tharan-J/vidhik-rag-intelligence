#!/usr/bin/env python3
"""
Vidhik Hybrid Retrieval CLI Tool
================================
Engineering verification CLI for testing the completed hybrid retrieval engine.
Executes BGE-M3 dense retrieval, BM25 sparse lexical retrieval, and RRF fusion.

Usage:
    python scripts/retrieve.py --query "What is the limitation period for filing an appeal?"
    python scripts/retrieve.py --query "Section 438 CrPC anticipatory bail" --top-k 10
    python scripts/retrieve.py --health-check
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

from retrieval.engine import HybridRetrievalEngine
from retrieval.config import load_retrieval_config


def main():
    parser = argparse.ArgumentParser(
        description="Vidhik Hybrid Legal Retrieval CLI (BGE-M3 Dense + BM25 Lexical + RRF)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Legal query string to retrieve evidence chunks for.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="Number of final hybrid results to return (default: 20).",
    )
    parser.add_argument(
        "--dense-top-k",
        type=int,
        default=50,
        help="Number of dense candidates to retrieve (default: 50).",
    )
    parser.add_argument(
        "--bm25-top-k",
        type=int,
        default=50,
        help="Number of BM25 candidates to retrieve (default: 50).",
    )
    parser.add_argument(
        "--rrf-k",
        type=int,
        default=60,
        help="RRF smoothing constant k (default: 60).",
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Check health of Qdrant Cloud connection and BM25 index and exit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed debug logs.",
    )

    args = parser.parse_args()

    # Logging setup
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # 1. Initialize Engine
    print("=" * 80)
    print("VIDHIK HYBRID RETRIEVAL ENGINE")
    print("=" * 80)
    print("Loading models and indexes (BGE-M3 1024-d, BM25 29,156 chunks, Qdrant Cloud)...")
    
    try:
        engine = HybridRetrievalEngine()
    except Exception as e:
        print(f"\n[FATAL ERROR] Engine initialization failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Health check flag
    if args.health_check:
        print("\nPerforming System Health Check...")
        health = engine.health_check()
        print(json.dumps(health, indent=2))
        sys.exit(0)

    if not args.query or not args.query.strip():
        parser.error("The --query argument is required unless using --health-check.")

    query = args.query.strip()
    print(f"\nExecuting Hybrid Search for Query: '{query}'")
    print(f"Parameters: dense_k={args.dense_top_k}, bm25_k={args.bm25_top_k}, rrf_k={args.rrf_k}, final_k={args.top_k}")
    print("-" * 80)

    try:
        results = engine.search(
            query=query,
            top_k=args.top_k,
            dense_top_k=args.dense_top_k,
            bm25_top_k=args.bm25_top_k,
            rrf_k=args.rrf_k,
        )
    except Exception as e:
        print(f"\n[ERROR] Retrieval search failed: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        serialized = [r.to_dict() for r in results]
        print(json.dumps(serialized, indent=2))
        return

    # Print formatted text output
    print(f"\nQUERY\n-----\n{query}\n")
    print(f"HYBRID RESULTS ({len(results)} chunks returned)\n" + "-" * 80)

    if not results:
        print("No matching legal chunks found.")
        return

    for res in results:
        dense_str = f"Rank {res.dense_rank} (score: {res.dense_score:.4f})" if res.dense_rank else "Not in top-K"
        bm25_str = f"Rank {res.bm25_rank} (score: {res.bm25_score:.4f})" if res.bm25_rank else "Not in top-K"

        # Truncate text for CLI display
        text_preview = res.text.strip().replace("\r", "")
        if len(text_preview) > 350:
            text_preview = text_preview[:350] + " ... [TRUNCATED]"

        print(f"{res.rrf_rank}. RRF Score : {res.rrf_score:.6f}")
        print(f"   Document  : {res.document_id}")
        print(f"   Court     : {res.court_level} ({res.court})")
        print(f"   Case      : {res.case_title}")
        print(f"   Case No   : {res.case_number}")
        print(f"   Date      : {res.decision_date} (Year: {res.year or 'N/A'})")
        print(f"   Pages     : {res.page_number} | Paragraph: {res.paragraph_id} | Sentence: {res.sentence_id}")
        print(f"   Chunk ID  : {res.chunk_id} (Qdrant Point: {res.qdrant_point_id})")
        print(f"   Dense Rank: {dense_str}")
        print(f"   BM25 Rank : {bm25_str}")
        print(f"\n   Text:")
        # Indent text nicely
        for line in text_preview.split("\n"):
            print(f"     {line}")
        print("\n" + "-" * 80)

    print(f"\n✓ Search completed successfully. Retrieved {len(results)} ranked chunks with full provenance.")


if __name__ == "__main__":
    main()
