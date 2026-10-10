"""
Vidhik Phase 4 - Step 1: Evidence Ingestion & Ground-Truth Fact Inventory
Extracts the verified Phase 3 retrieval evidence (3-sentence contextual windows)
and Phase 2 legal fact inventory across Development and Frozen Test documents.

Produces:
1. phase4_summarization/corpus/phase4_documents.parquet
2. phase4_summarization/corpus/phase4_evidence.parquet
3. phase4_summarization/corpus/fact_inventory.parquet
"""

import json
import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Phase4_Evidence_Prep")

ROOT_DIR = Path(__file__).resolve().parent
PHASE2_DIR = ROOT_DIR / "district_extraction"
PHASE3_DIR = ROOT_DIR / "rag_experiments"
PHASE4_DIR = ROOT_DIR / "phase4_summarization"
CORPUS_DIR = PHASE4_DIR / "corpus"
CORPUS_DIR.mkdir(parents=True, exist_ok=True)


def run_evidence_prep():
    logger.info("Ingesting Phase 2 & Phase 3 verified artifacts for Phase 4...")

    # Load Phase 2 manifests
    src_manifest = pd.read_parquet(PHASE2_DIR / "source_manifest" / "district_source_manifest_v1.parquet")
    par_df = pd.read_parquet(PHASE2_DIR / "structure" / "v1" / "paragraphs_provenance_v1.parquet")
    sen_df = pd.read_parquet(PHASE2_DIR / "structure" / "v1" / "sentences_provenance_v1.parquet")
    entity_pres = pd.read_parquet(PHASE2_DIR / "validation" / "legal_entity_preservation.parquet")

    # Load Phase 3 query set to preserve exact dev (calibration) vs frozen test separation
    with open(PHASE3_DIR / "queries" / "query_set_v1.jsonl", "r", encoding="utf-8") as f:
        query_set = [json.loads(line) for line in f]

    dev_docs = set(q["target_document_id"] for q in query_set if q["split"] == "calibration")
    test_docs = set(q["target_document_id"] for q in query_set if q["split"] == "test")
    # Ensure disjoint sets
    test_docs = test_docs - dev_docs

    logger.info("Identified %d Dev documents and %d Frozen Test documents.", len(dev_docs), len(test_docs))

    # Prepare document records
    doc_records = []
    for _, row in src_manifest.iterrows():
        doc_id = row["document_id"]
        split = "test" if doc_id in test_docs else ("development" if doc_id in dev_docs else "general_corpus")
        
        doc_records.append({
            "document_id": doc_id,
            "source_sha256": row["sha256"],
            "source_filename": row["source_filename"],
            "page_count": int(row["page_count"]),
            "file_size_bytes": int(row["file_size_bytes"]),
            "state_name": str(row.get("state_name", "")),
            "district_name": str(row.get("district_name", "")),
            "court_complex_name": str(row.get("court_complex_name", "")),
            "year": int(row["year"]) if pd.notna(row.get("year")) and str(row["year"]).isdigit() else None,
            "case_number": str(row.get("case_number", "")),
            "dataset_split": split
        })

    docs_df = pd.DataFrame(doc_records)
    docs_df.to_parquet(CORPUS_DIR / "phase4_documents.parquet", index=False)
    logger.info("Saved %d documents to phase4_documents.parquet", len(docs_df))

    # Build 3-sentence contextual windows for evidence
    logger.info("Constructing verified 3-sentence retrieval evidence windows...")
    evidence_records = []

    # Map structured JSONs for exact page and paragraph texts
    struct_dir = PHASE2_DIR / "structure" / "v1"

    for doc_id in sorted(list(dev_docs | test_docs)):
        json_path = struct_dir / f"{doc_id}.json"
        if not json_path.exists():
            continue
            
        with open(json_path, "r", encoding="utf-8") as f:
            doc_data = json.load(f)

        src_sha = doc_data["source"]["sha256"]
        pages = doc_data["structure"]["pages"]

        chunk_idx = 1
        for page in pages:
            page_num = page["page_number"]
            for par in page["paragraphs"]:
                par_id = par["paragraph_id"]
                sentences = par["sentences"]
                
                # Create 3-sentence overlapping windows
                if not sentences:
                    continue
                    
                for i in range(0, len(sentences), 2): # stride of 2
                    win_sens = sentences[i:i + 3]
                    win_text = " ".join(s["text"] for s in win_sens)
                    win_id = f"EV_{doc_id}_P{page_num:03d}_WIN{chunk_idx:03d}"
                    primary_sen_id = win_sens[0]["sentence_id"]

                    evidence_records.append({
                        "evidence_id": win_id,
                        "document_id": doc_id,
                        "source_sha256": src_sha,
                        "page_number": page_num,
                        "paragraph_id": par_id,
                        "primary_sentence_id": primary_sen_id,
                        "sentence_ids": [s["sentence_id"] for s in win_sens],
                        "evidence_text": win_text,
                        "word_count": len(win_text.split()),
                        "character_count": len(win_text),
                        "provenance_chain": f"{win_id} -> {primary_sen_id} -> {par_id} -> Page {page_num} -> {doc_id} -> SHA256:{src_sha[:16]}"
                    })
                    chunk_idx += 1

    ev_df = pd.DataFrame(evidence_records)
    ev_df.to_parquet(CORPUS_DIR / "phase4_evidence.parquet", index=False)
    logger.info("Saved %d verified evidence windows to phase4_evidence.parquet", len(ev_df))

    # Build ground-truth legal fact inventory for summarization factuality auditing
    logger.info("Extracting ground-truth legal fact inventory...")
    fact_records = []

    for doc_id in sorted(list(dev_docs | test_docs)):
        json_path = struct_dir / f"{doc_id}.json"
        if not json_path.exists():
            continue
        with open(json_path, "r", encoding="utf-8") as f:
            doc_data = json.load(f)

        norm_text = "\n".join(p["normalized_text"] for p in doc_data["normalized_pages"])
        
        # Extract ground truth facts using deterministic legal patterns
        # 1. Case identity
        import re
        case_matches = re.findall(r'(?:C\.C\.|Crl\.Misc\.|MAC Case|CS|PRC|C\.R\.\s*Case)\s*(?:No\.?)?\s*[\d\/\-]+', norm_text, re.IGNORECASE)
        # 2. Statutory provisions
        statute_matches = re.findall(r'(?:u/s|u/sec|section|sec\.)\s*[\d\(\)\sA-Za-z]+(?:Cr\.?P\.?C\.?|I\.?P\.?C\.?|Act[,\s\d]*)', norm_text, re.IGNORECASE)
        # 3. Dates
        date_matches = re.findall(r'\b\d{1,2}[\.\/-]\d{1,2}[\.\/-]\d{2,4}\b', norm_text)
        # 4. Dispositions
        disposition_matches = re.findall(r'\b(acquitted|convicted|dismissed|allowed|disposed|rejected|withdrawn|granted|denied|discharged)\b', norm_text, re.IGNORECASE)

        fact_records.append({
            "document_id": doc_id,
            "source_sha256": doc_data["source"]["sha256"],
            "case_numbers": list(set(case_matches[:3])),
            "statutory_sections": list(set(statute_matches[:4])),
            "dates": list(set(date_matches[:5])),
            "dispositions": list(set(m.lower() for m in disposition_matches)),
            "court_name": doc_data["metadata"].get("court_complex_name", ""),
            "district_name": doc_data["metadata"].get("district_name", ""),
            "state_name": doc_data["metadata"].get("state_name", "")
        })

    facts_df = pd.DataFrame(fact_records)
    facts_df.to_parquet(CORPUS_DIR / "fact_inventory.parquet", index=False)
    logger.info("Saved ground-truth fact inventory for %d documents to fact_inventory.parquet", len(facts_df))


if __name__ == "__main__":
    run_evidence_prep()
