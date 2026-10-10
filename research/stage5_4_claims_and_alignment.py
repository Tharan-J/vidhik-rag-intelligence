"""
Vidhik Phase 5 - Stage P5.4 & P5.5: Claim Decomposition & Fact-to-Claim Alignment
Decomposes generated summaries into atomic propositions, assigns categories and normalization,
links full provenance, and classifies alignment against the canonical Legal Fact Ledger:
- SUPPORTED
- PARTIALLY_SUPPORTED
- CONTRADICTED
- UNSUPPORTED
- AMBIGUOUS
- OMITTED (for canonical facts not represented in summary)

Produces:
1. phase5_fact_preservation/claims/claims_v1.parquet
2. phase5_fact_preservation/claims/claim_fact_alignment_v1.parquet
3. phase5_fact_preservation/claims/claim_provenance_v1.parquet
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Phase5_Claims_Alignment")

ROOT_DIR = Path(__file__).resolve().parent
PHASE5_DIR = ROOT_DIR / "phase5_fact_preservation"
CORPUS_DIR = PHASE5_DIR / "corpus"
GEN_DIR = PHASE5_DIR / "generation"
CLAIMS_DIR = PHASE5_DIR / "claims"

CLAIMS_DIR.mkdir(parents=True, exist_ok=True)

DISPOSITION_MAP = {
    "acquitted": ["acquitted", "not guilty", "விடுவிக்கப்பட்டார்", "விடுதலை", "बरी", "दोषमुक्त", "ಖುಲಾಸೆ", "निर्दोष"],
    "convicted": ["convicted", "guilty", "தண்டிக்கப்பட்டார்", "दोषी", "सजा", "ದೋಷಿ"],
    "dismissed": ["dismissed", "தள்ளுபடி", "खारिज", "निरस्त", "ವಜಾ", "फेटाळले"],
    "allowed": ["allowed", "அனுமதிக்கப்பட்டது", "स्वीकार", "अनुमति", "ಅನುಮತಿಸಲಾಗಿದೆ", "मंजूर"],
    "transferred": ["transferred", "மாற்றப்பட்டது", "स्थानांतरित", "ವರ್ಗಾಯಿಸಲಾಗಿದೆ"],
    "committed": ["committed", "ஒப்படைக்கப்பட்டது", "सुपुर्द", "ವಹಿಸಿಕೊಡಲಾಗಿದೆ"]
}


def categorize_claim(text: str) -> str:
    t_low = text.lower()
    if any(k in t_low for k in ["court of", "judge", "present:", "magistrate"]):
        return "COURT"
    if any(k in t_low for k in ["cc ", "c.c.", "prc", "case no", "no."]) and re.search(r'\d+', t_low):
        return "CASE_NUMBER"
    if any(k in t_low for k in ["complainant", "accused", "petitioner", "respondent", "state of", "police"]):
        return "PARTIES"
    if any(k in t_low for k in ["section", "sec.", "u/s", "ipc", "crpc", "act"]):
        return "STATUTORY_SECTION"
    if any(k in t_low for k in ["acquitted", "convicted", "dismissed", "allowed", "transferred", "committed", "disposed"]):
        return "DISPOSITION"
    if re.search(r'\b\d{1,2}[\.\/-]\d{1,2}[\.\/-]\d{2,4}\b', t_low) or "201" in t_low or "199" in t_low:
        return "DECISION_DATE"
    if any(k in t_low for k in ["rs.", "inr", "₹", "rupees", "fine"]):
        return "AMOUNT"
    if any(k in t_low for k in ["bail", "liberty", "released", "custody"]):
        return "RELIEF"
    if any(k in t_low for k in ["proved", "doubt", "failed", "witness"]):
        return "JUDICIAL_FINDING"
    return "OTHER_CRITICAL_FACT"


def run_claims_and_alignment():
    logger.info("Initializing P5.4 Claim Decomposition & P5.5 Fact-to-Claim Alignment...")

    manifest_df = pd.read_parquet(GEN_DIR / "generation_manifest_v1.parquet")
    facts_df = pd.read_parquet(CORPUS_DIR / "fact_ledger_v1.parquet")
    avail_df = pd.read_parquet(CORPUS_DIR / "evidence_availability_v1.parquet")

    # Evaluate successfully generated summaries
    success_runs = manifest_df[manifest_df["status"] == "SUCCESS"].copy()
    logger.info("Processing claims across %d successful summaries.", len(success_runs))

    # Pre-index canonical facts by document
    facts_by_doc = {}
    for doc_id, grp in facts_df.groupby("doc_id"):
        facts_by_doc[doc_id] = grp.to_dict(orient="records")

    claims_records = []
    alignment_records = []
    provenance_records = []

    for _, run_row in success_runs.iterrows():
        run_id = run_row["run_id"]
        doc_id = run_row["doc_id"]
        lang = run_row["language"]
        sum_text = run_row["summary_text"]
        sha256 = run_row["source_sha256"]
        doc_facts = facts_by_doc.get(doc_id, [])

        # Decompose summary into atomic clauses
        raw_sentences = [s.strip() for s in re.split(r'[.\n।]+', sum_text) if len(s.strip()) > 8]
        if not raw_sentences:
            raw_sentences = [sum_text.strip()]

        summary_claim_ids = []
        represented_fact_ids = set()

        for c_idx, raw_claim in enumerate(raw_sentences, 1):
            claim_id = f"CLM_{run_id}_{c_idx:03d}"
            summary_claim_ids.append(claim_id)
            cat = categorize_claim(raw_claim)
            norm_claim = re.sub(r'\s+', ' ', raw_claim).strip()

            # Align against document facts
            alignment_status = "UNSUPPORTED"
            matched_fact = None
            evidence_sens = []

            # Contradiction check: disposition clash
            claim_disp = None
            for disp_key, variants in DISPOSITION_MAP.items():
                if any(v in raw_claim.lower() for v in variants):
                    claim_disp = disp_key
                    break

            doc_dispositions = [f for f in doc_facts if f["category"] == "DISPOSITION"]
            canonical_disp = doc_dispositions[0]["normalized_value"] if doc_dispositions else None

            if claim_disp and canonical_disp:
                if claim_disp == canonical_disp:
                    alignment_status = "SUPPORTED"
                    matched_fact = doc_dispositions[0]
                    represented_fact_ids.add(matched_fact["fact_id"])
                else:
                    alignment_status = "CONTRADICTED"
                    matched_fact = doc_dispositions[0]
            else:
                # Match against facts in the same category or general facts
                best_overlap = 0.0
                for f in doc_facts:
                    f_val = str(f["value"]).lower()
                    f_norm = str(f["normalized_value"]).lower()
                    claim_low = raw_claim.lower()

                    # Exact entity presence in claim
                    if (f_norm in claim_low and len(f_norm) > 3) or (f_val in claim_low and len(f_val) > 4):
                        alignment_status = "SUPPORTED"
                        matched_fact = f
                        represented_fact_ids.add(f["fact_id"])
                        evidence_sens.append(f["source_sentence_id"])
                        break
                    
                    # Token overlap
                    f_tokens = set(re.findall(r'\w+', f_val))
                    c_tokens = set(re.findall(r'\w+', claim_low))
                    overlap = len(f_tokens & c_tokens) / max(1, len(f_tokens))
                    if overlap > best_overlap:
                        best_overlap = overlap
                        matched_fact = f

                if alignment_status != "SUPPORTED":
                    if best_overlap >= 0.40 and matched_fact:
                        alignment_status = "SUPPORTED"
                        represented_fact_ids.add(matched_fact["fact_id"])
                        evidence_sens.append(matched_fact["source_sentence_id"])
                    elif best_overlap >= 0.20 and matched_fact:
                        alignment_status = "PARTIALLY_SUPPORTED"
                        represented_fact_ids.add(matched_fact["fact_id"])
                    elif len(raw_claim.split()) > 15:
                        alignment_status = "AMBIGUOUS"
                    else:
                        alignment_status = "UNSUPPORTED"

            # Check repetition loop degeneracy
            words_list = raw_claim.lower().split()
            if len(words_list) > 6 and (len(set(words_list)) / len(words_list) < 0.40):
                alignment_status = "UNSUPPORTED"

            matched_fact_id = matched_fact["fact_id"] if matched_fact else None
            primary_sen_id = matched_fact["source_sentence_id"] if matched_fact else f"{doc_id}_P001_SEN001"

            # 1. Claim record
            claims_records.append({
                "claim_id": claim_id,
                "summary_id": run_id,
                "doc_id": doc_id,
                "language": lang,
                "text": raw_claim,
                "category": cat,
                "normalized_claim": norm_claim
            })

            # 2. Alignment record
            alignment_records.append({
                "claim_id": claim_id,
                "summary_id": run_id,
                "doc_id": doc_id,
                "language": lang,
                "fact_id": matched_fact_id,
                "claim_category": cat,
                "fact_category": matched_fact["category"] if matched_fact else "UNALIGNED",
                "alignment_status": alignment_status,
                "confidence": 0.95 if alignment_status in ["SUPPORTED", "CONTRADICTED"] else 0.80,
                "evidence_sentence_ids": evidence_sens
            })

            # 3. Provenance record
            provenance_records.append({
                "claim_id": claim_id,
                "summary_id": run_id,
                "doc_id": doc_id,
                "fact_id": matched_fact_id,
                "source_sentence_id": primary_sen_id,
                "page_number": matched_fact["page_number"] if matched_fact else 1,
                "source_sha256": sha256,
                "provenance_chain": f"{claim_id} -> {matched_fact_id} -> {primary_sen_id} -> {doc_id} -> SHA256:{sha256[:16]}"
            })

        # Track omitted critical facts
        for f in doc_facts:
            if f["fact_id"] not in represented_fact_ids:
                alignment_records.append({
                    "claim_id": f"OMIT_{run_id}_{f['fact_id']}",
                    "summary_id": run_id,
                    "doc_id": doc_id,
                    "language": lang,
                    "fact_id": f["fact_id"],
                    "claim_category": f["category"],
                    "fact_category": f["category"],
                    "alignment_status": "OMITTED",
                    "confidence": 0.95,
                    "evidence_sentence_ids": [f["source_sentence_id"]]
                })

    # Save parquets
    claims_df = pd.DataFrame(claims_records)
    claims_path = CLAIMS_DIR / "claims_v1.parquet"
    claims_df.to_parquet(claims_path, index=False)
    logger.info("Saved %d atomic claims to %s", len(claims_df), claims_path)

    align_df = pd.DataFrame(alignment_records)
    align_path = CLAIMS_DIR / "claim_fact_alignment_v1.parquet"
    align_df.to_parquet(align_path, index=False)
    logger.info("Saved %d claim-fact alignments to %s", len(align_df), align_path)

    prov_df = pd.DataFrame(provenance_records)
    prov_path = CLAIMS_DIR / "claim_provenance_v1.parquet"
    prov_df.to_parquet(prov_path, index=False)
    logger.info("Saved %d claim provenance records to %s", len(prov_df), prov_path)

    print("\nAlignment Status Breakdown:")
    print(align_df["alignment_status"].value_counts())


if __name__ == "__main__":
    run_claims_and_alignment()
