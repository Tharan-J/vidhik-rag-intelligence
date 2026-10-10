"""
Vidhik Phase 5 - Stage P5.1: Full Canonical Legal Fact Ledger Generation
Processes all 161 frozen District Court documents to generate:
1. phase5_fact_preservation/corpus/fact_ledger_v1.parquet
2. phase5_fact_preservation/corpus/fact_ledger_sources.parquet
"""

import json
import logging
from pathlib import Path
import pandas as pd
from stage5_1_fact_ledger_prototype import extract_document_facts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Phase5_Fact_Ledger_Full")

ROOT_DIR = Path(__file__).resolve().parent
STRUCT_DIR = ROOT_DIR / "district_extraction" / "structure" / "v1"
SRC_MANIFEST_PATH = ROOT_DIR / "district_extraction" / "source_manifest" / "district_source_manifest_v1.parquet"
PHASE5_DIR = ROOT_DIR / "phase5_fact_preservation"
CORPUS_DIR = PHASE5_DIR / "corpus"
CORPUS_DIR.mkdir(parents=True, exist_ok=True)


def run_full_fact_ledger_generation():
    logger.info("Starting Full Canonical Legal Fact Ledger Generation across 161 documents...")
    
    src_manifest = pd.read_parquet(SRC_MANIFEST_PATH)
    logger.info("Loaded source manifest with %d documents.", len(src_manifest))

    json_files = sorted(list(STRUCT_DIR.glob("DC_*.json")))
    logger.info("Found %d structured document JSONs.", len(json_files))

    all_facts = []
    source_records = []

    for idx, jf in enumerate(json_files, 1):
        with open(jf, "r", encoding="utf-8") as f:
            doc_data = json.load(f)

        doc_id = doc_data["document_id"]
        sha256 = doc_data["source"]["sha256"]
        meta = doc_data.get("metadata", {})

        doc_facts = extract_document_facts(doc_data)
        all_facts.extend(doc_facts)

        crit_count = sum(1 for f in doc_facts if f["criticality"] == "CRITICAL")
        imp_count = sum(1 for f in doc_facts if f["criticality"] == "IMPORTANT")

        source_records.append({
            "doc_id": doc_id,
            "source_sha256": sha256,
            "source_filename": doc_data["source"].get("filename", ""),
            "court_complex_name": str(meta.get("court_complex_name", "")),
            "state_name": str(meta.get("state_name", "")),
            "district_name": str(meta.get("district_name", "")),
            "year": int(meta["year"]) if pd.notna(meta.get("year")) and str(meta["year"]).isdigit() else None,
            "case_number": str(meta.get("case_number", "")),
            "page_count": int(doc_data["source"].get("page_count", 1)),
            "total_facts_count": len(doc_facts),
            "critical_facts_count": crit_count,
            "important_facts_count": imp_count
        })

        if idx % 40 == 0 or idx == len(json_files):
            logger.info("Processed %d/%d documents (Accumulated facts: %d)...", idx, len(json_files), len(all_facts))

    # Save fact ledger
    facts_df = pd.DataFrame(all_facts)
    ledger_path = CORPUS_DIR / "fact_ledger_v1.parquet"
    facts_df.to_parquet(ledger_path, index=False)
    logger.info("Saved %d canonical legal facts to %s", len(facts_df), ledger_path)

    # Save sources
    sources_df = pd.DataFrame(source_records)
    sources_path = CORPUS_DIR / "fact_ledger_sources.parquet"
    sources_df.to_parquet(sources_path, index=False)
    logger.info("Saved %d document sources to %s", len(sources_df), sources_path)


if __name__ == "__main__":
    run_full_fact_ledger_generation()
