#!/usr/bin/env python3
"""
Bridge script for Vidhik Next.js frontend to query the persistent BM25 index and chunk corpus.
Can be executed via CLI:
  python prototype/scripts/retrieval_bridge.py --query "limitation period Section 37" --top_k 5
  python prototype/scripts/retrieval_bridge.py --doc "SC_2021 INSC 194"
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add prototype root to path
PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_ROOT))

from retrieval.bm25 import BM25Retriever

def search_query(query: str, top_k: int = 5):
    retriever = BM25Retriever()
    hits = retriever.search(query=query, top_k=top_k)
    
    results = []
    for idx, h in enumerate(hits, 1):
        # Extract title/court heuristic from doc_id or text
        doc_id = h.document_id
        is_sc = "SC_" in doc_id or "INSC" in doc_id
        is_hc = "HC_" in doc_id or "DLHC" in doc_id
        court = "Supreme Court of India" if is_sc else ("Delhi High Court" if is_hc else "Indian Judiciary")
        
        # Extract title if present in text or doc_id
        title = doc_id.replace(".pdf", "")
        if "2021 INSC 194" in doc_id:
            title = "Govt. of Maharashtra v. M/s Borse Brothers Engineers & Contractors Pvt. Ltd."
        elif "DLHC010427042021" in doc_id:
            title = "Delhi Development Authority v. M/s Ajab Singh & Co."
        elif "2021 INSC 883" in doc_id:
            title = "New India Assurance Co. Ltd. v. Hilli Multipurpose Cold Storage"
            
        results.append({
            "evidence_id": f"E{idx}",
            "document_id": doc_id,
            "chunk_id": h.chunk_id,
            "score": round(float(h.score), 4),
            "court": court,
            "case_title": title,
            "text": h.text,
            "preview": h.text[:350].strip() + ("..." if len(h.text) > 350 else ""),
        })
    return results

def get_doc_chunks(doc_id_query: str, max_chunks: int = 20):
    import pandas as pd
    mapping_path = PROTOTYPE_ROOT / "indexes" / "bm25" / "bm25_mapping.parquet"
    if not mapping_path.exists():
        return {"error": "Mapping file not found"}
        
    df = pd.read_parquet(mapping_path)
    match = df[df["document_id"].str.contains(doc_id_query, case=False, na=False)]
    if len(match) == 0:
        return {"error": f"No chunks found for {doc_id_query}"}
        
    chunks = []
    for _, row in match.head(max_chunks).iterrows():
        chunks.append({
            "chunk_id": row["chunk_id"],
            "text": row["text"],
            "length": len(row["text"]),
        })
        
    doc_name = match.iloc[0]["document_id"]
    return {
        "document_id": doc_name,
        "total_chunks_in_corpus": len(match),
        "returned_chunks": len(chunks),
        "chunks": chunks
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--top_k", type=int, default=5)
    parser.add_argument("--doc", type=str, default=None)
    args = parser.parse_args()
    
    if args.doc:
        data = get_doc_chunks(args.doc)
        print(json.dumps(data))
    elif args.query:
        hits = search_query(args.query, top_k=args.top_k)
        print(json.dumps({"query": args.query, "count": len(hits), "results": hits}))
    else:
        print(json.dumps({"error": "Specify --query or --doc"}))

if __name__ == "__main__":
    main()
