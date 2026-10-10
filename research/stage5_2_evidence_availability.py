"""
Vidhik Phase 5 - Stage P5.2: Evidence Availability Mapping
Maps each canonical fact in fact_ledger_v1.parquet against the Phase 3 retrieved evidence.
Determines whether each fact was:
- AVAILABLE (present in retrieved evidence)
- RETRIEVAL_MISSING (present in original document but omitted by Phase 3 retrieval)
- SOURCE_AMBIGUOUS
- SOURCE_ABSENT

Produces:
phase5_fact_preservation/corpus/evidence_availability_v1.parquet
"""

import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Phase5_Evidence_Availability")

ROOT_DIR = Path(__file__).resolve().parent
PHASE5_DIR = ROOT_DIR / "phase5_fact_preservation"
CORPUS_DIR = PHASE5_DIR / "corpus"
FACT_LEDGER_PATH = CORPUS_DIR / "fact_ledger_v1.parquet"
PHASE4_EVIDENCE_PATH = ROOT_DIR / "phase4_summarization" / "corpus" / "phase4_evidence.parquet"
RAG_CHUNKS_PATH = ROOT_DIR / "rag_experiments" / "corpus" / "chunks_v1.parquet"


def run_evidence_availability_mapping():
    logger.info("Initializing P5.2 Evidence Availability Mapping...")

    facts_df = pd.read_parquet(FACT_LEDGER_PATH)
    logger.info("Loaded %d canonical facts across %d documents.", len(facts_df), facts_df["doc_id"].nunique())

    # Ingest Phase 3 / Phase 4 evidence
    evidence_df = pd.read_parquet(PHASE4_EVIDENCE_PATH)
    rag_chunks_df = pd.read_parquet(RAG_CHUNKS_PATH)

    # Build document -> list of evidence sentences & text map
    doc_evidence_sentences = {}
    doc_evidence_text = {}

    for doc_id, grp in evidence_df.groupby("document_id"):
        all_sens = set()
        for s_list in grp["sentence_ids"]:
            if isinstance(s_list, (list, tuple)):
                all_sens.update(s_list)
            elif hasattr(s_list, "tolist"):
                all_sens.update(s_list.tolist())
        doc_evidence_sentences[doc_id] = all_sens
        doc_evidence_text[doc_id] = " ".join(grp["evidence_text"].tolist()).lower()

    # Fallback to top-4 RAG chunks for general corpus documents
    for doc_id, grp in rag_chunks_df.groupby("document_id"):
        if doc_id not in doc_evidence_sentences:
            top_chunks = grp.head(4)
            all_sens = set()
            for s_list in top_chunks["sentence_ids"]:
                if isinstance(s_list, (list, tuple)):
                    all_sens.update(s_list)
                elif hasattr(s_list, "tolist"):
                    all_sens.update(s_list.tolist())
            doc_evidence_sentences[doc_id] = all_sens
            doc_evidence_text[doc_id] = " ".join(top_chunks["text"].tolist()).lower()

    logger.info("Mapped evidence sentence coverage across %d documents.", len(doc_evidence_sentences))

    availability_records = []

    for _, row in facts_df.iterrows():
        fact_id = row["fact_id"]
        doc_id = row["doc_id"]
        sen_id = row["source_sentence_id"]
        val = str(row["value"]).strip()
        norm_val = str(row["normalized_value"]).strip().lower()
        cat = row["category"]

        ev_sens = doc_evidence_sentences.get(doc_id, set())
        ev_text = doc_evidence_text.get(doc_id, "")

        # Check sentence presence or text presence in evidence window
        is_sentence_in_evidence = sen_id in ev_sens
        is_text_in_evidence = (norm_val in ev_text) or (val.lower() in ev_text) if len(norm_val) > 3 else is_sentence_in_evidence

        if is_sentence_in_evidence or is_text_in_evidence:
            avail_status = "AVAILABLE"
            present_in_ev = True
        else:
            avail_status = "RETRIEVAL_MISSING"
            present_in_ev = False

        matched_ev_sens = [sen_id] if is_sentence_in_evidence else [s for s in ev_sens if s.startswith(doc_id)][:3]

        availability_records.append({
            "fact_id": fact_id,
            "doc_id": doc_id,
            "category": cat,
            "criticality": row["criticality"],
            "value": val,
            "normalized_value": row["normalized_value"],
            "source_sentence_id": sen_id,
            "present_in_source": True,
            "present_in_retrieved_evidence": present_in_ev,
            "evidence_sentence_ids": matched_ev_sens,
            "availability_status": avail_status,
            "provenance_chain": row["provenance_chain"]
        })

    avail_df = pd.DataFrame(availability_records)
    out_path = CORPUS_DIR / "evidence_availability_v1.parquet"
    avail_df.to_parquet(out_path, index=False)
    logger.info("Saved %d evidence availability records to %s", len(avail_df), out_path)

    # Log summary statistics
    status_counts = avail_df["availability_status"].value_counts().to_dict()
    logger.info("Evidence availability breakdown: %s", status_counts)


if __name__ == "__main__":
    run_evidence_availability_mapping()
