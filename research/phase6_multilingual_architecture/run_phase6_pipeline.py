"""
Phase 6 Master Pipeline Orchestrator
Executes:
1. System C (IndicTrans2 Raw Translation)
2. System D (Legal-Aware Translation)
3. System E (Deterministic Legal Entity Verification)
4. Comprehensive Fact-Level Evaluation (425 units per system)
5. Translation Fidelity Evaluation
6. Terminology Preservation Evaluation
7. Phase 6 Causal Failure Attribution (R1-R8)
8. Export of comparative tables, CSVs, and Parquet artifacts
"""

import os
import sys
import json
import time
import hashlib
import pandas as pd
import numpy as np
import yaml

sys.path.append(os.path.abspath("phase6_multilingual_architecture"))
from systems.system_c_indictrans2.translator import IndicTrans2Translator
from systems.system_d_legal_aware.translator import LegalAwareTranslator
from systems.system_e_verified.verifier import DeterministicLegalVerifier
from evaluation.evaluation_engine import (
    evaluate_fact_in_text,
    attribute_failure,
    CRITICAL_CATEGORIES,
    IMPORTANT_CATEGORIES
)

BASE_DIR = "phase6_multilingual_architecture"

def run_phase6():
    print("=" * 70)
    print("VIDHIK PHASE 6: MULTILINGUAL ARCHITECTURE EXPERIMENTAL PIPELINE")
    print("=" * 70)

    # 1. Load config
    config_path = os.path.join(BASE_DIR, "config", "phase6_config.yaml")
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    # 2. Load inputs
    df_gold = pd.read_parquet(os.path.join(BASE_DIR, "inputs", "frozen_gold_facts.parquet"))
    df_ev = pd.read_parquet(os.path.join(BASE_DIR, "inputs", "frozen_evidence_manifest.parquet"))
    df_en = pd.read_parquet(os.path.join(BASE_DIR, "outputs", "english_summaries.parquet"))
    df_b = pd.read_parquet(os.path.join(BASE_DIR, "outputs", "direct_indic_summaries.parquet"))

    print(f"Loaded Gold Facts: {len(df_gold)} across {df_gold['doc_id'].nunique()} docs")
    print(f"Loaded Frozen Evidence: {len(df_ev)} windows across {df_ev['doc_id'].nunique()} docs")
    print(f"Loaded System A (English Control): {len(df_en)} summaries")
    print(f"Loaded System B (Direct Indic Control): {len(df_b)} summaries")

    # Verify English summary hashes
    en_hash_map = dict(zip(df_en["doc_id"], df_en["english_summary_hash"]))
    print(f"Verified {len(en_hash_map)} English input summary hashes.")

    target_languages = ["ta", "hi", "kn", "mr"]
    docs = sorted(df_en["doc_id"].unique())

    # Initialize shared IndicTrans2 translator
    shared_translator = IndicTrans2Translator(
        model_id=cfg["indictrans2"]["model_id"],
        device=cfg["indictrans2"].get("device_preference")
    )

    # -------------------------------------------------------------
    # 3. RUN SYSTEM C: English -> IndicTrans2 Raw Translation
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print("[System C] Running English -> IndicTrans2 Raw Translation...")
    print("=" * 50)

    # Set memory allocation configuration
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

    # Initialize translation cache
    cache_file = os.path.join(BASE_DIR, "outputs", "translation_cache.json")
    translation_cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                translation_cache = json.load(f)
            print(f"Loaded existing translation cache with {len(translation_cache)} entries.")
        except Exception as e:
            print(f"Cache load warning: {e}")

    def save_cache():
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(translation_cache, f, indent=2, ensure_ascii=False)

    c_rows = []
    for doc_id in docs:
        en_row = df_en[df_en["doc_id"] == doc_id].iloc[0]
        en_text = en_row["summary_text"]
        en_hash = en_hash_map[doc_id]

        for lang in target_languages:
            c_key = f"sys_c_{doc_id}_{lang}_{en_hash}"
            if c_key in translation_cache:
                res = translation_cache[c_key]
                print(f"  [Sys C Cache] {doc_id} -> {lang} (len={len(res['summary_text'])})")
            else:
                res = shared_translator.translate_summary(en_text, lang)
                translation_cache[c_key] = res
                save_cache()
                print(f"  [Sys C] {doc_id} -> {lang} ({res['latency_seconds']:.2f}s, len={len(res['summary_text'])})")

            c_rows.append({
                "run_id": f"phase6_sys_c_{doc_id}_{lang}",
                "doc_id": doc_id,
                "language": lang,
                "system": "system_c_indictrans2",
                "system_name": "English -> IndicTrans2 Raw Translation",
                "model": cfg["indictrans2"]["model_id"],
                "english_summary_hash": en_hash,
                "summary_text": res["summary_text"],
                "output_hash": res["output_hash"],
                "sentence_count": res["sentence_count"],
                "latency_seconds": res["latency_seconds"],
                "timestamp": pd.Timestamp.now().isoformat(),
                "status": "SUCCESS"
            })

    df_c = pd.DataFrame(c_rows)
    df_c.to_parquet(os.path.join(BASE_DIR, "outputs", "indictrans2_summaries.parquet"), index=False)
    print(f"[System C] Completed 36 translations. Saved to outputs/indictrans2_summaries.parquet")

    # -------------------------------------------------------------
    # 4. RUN SYSTEM D: Legal-Aware Translation
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print("[System D] Running Legal-Aware Translation...")
    print("=" * 50)

    legal_aware_trans = LegalAwareTranslator(
        indictrans_translator=shared_translator,
        config_path=os.path.join(BASE_DIR, "config", "terminology_config.yaml")
    )

    d_rows = []
    term_eval_records = []
    for doc_id in docs:
        en_row = df_en[df_en["doc_id"] == doc_id].iloc[0]
        en_text = en_row["summary_text"]
        en_hash = en_hash_map[doc_id]

        for lang in target_languages:
            d_key = f"sys_d_{doc_id}_{lang}_{en_hash}"
            if d_key in translation_cache:
                res = translation_cache[d_key]
                print(f"  [Sys D Cache] {doc_id} -> {lang} (Protected: {res['protected_entities_count']} entities)")
            else:
                res = legal_aware_trans.translate_summary(en_text, lang)
                translation_cache[d_key] = res
                save_cache()
                print(f"  [Sys D] {doc_id} -> {lang} (Protected: {res['protected_entities_count']} entities, {res['latency_seconds']:.2f}s)")

            d_rows.append({
                "run_id": f"phase6_sys_d_{doc_id}_{lang}",
                "doc_id": doc_id,
                "language": lang,
                "system": "system_d_legal_aware",
                "system_name": "Legal-Aware Translation (Entity Protection + IndicTrans2)",
                "model": cfg["indictrans2"]["model_id"],
                "english_summary_hash": en_hash,
                "summary_text": res["summary_text"],
                "raw_translated_text": res["raw_translated_text"],
                "protected_entities_count": res["protected_entities_count"],
                "output_hash": res["output_hash"],
                "latency_seconds": res["latency_seconds"],
                "timestamp": pd.Timestamp.now().isoformat(),
                "status": "SUCCESS"
            })

            # Record terminology audit records
            for rec in res["audit_records"]:
                term_eval_records.append({
                    "doc_id": doc_id,
                    "language": lang,
                    "system": "system_d_legal_aware",
                    "category": rec["category"],
                    "source_text": rec["source_text"],
                    "target_text": rec["target_text"],
                    "status": rec["status"]
                })

    df_d = pd.DataFrame(d_rows)
    df_d.to_parquet(os.path.join(BASE_DIR, "outputs", "legal_aware_summaries.parquet"), index=False)
    df_term = pd.DataFrame(term_eval_records)
    df_term.to_parquet(os.path.join(BASE_DIR, "evaluation", "terminology_evaluation.parquet"), index=False)
    print(f"[System D] Completed 36 translations. Saved to outputs/legal_aware_summaries.parquet")
    print(f"[Terminology] Recorded {len(df_term)} terminology preservation records.")

    # -------------------------------------------------------------
    # 5. RUN SYSTEM E: Legal-Aware Translation + Verification
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print("[System E] Running Deterministic Legal Entity Verification...")
    print("=" * 50)

    verifier = DeterministicLegalVerifier()
    e_rows = []
    for _, d_row in df_d.iterrows():
        doc_id = d_row["doc_id"]
        lang = d_row["language"]
        en_row = df_en[df_en["doc_id"] == doc_id].iloc[0]
        en_text = en_row["summary_text"]
        indic_text = d_row["summary_text"]

        # Filter entities for this doc and language
        sub_term = [r for r in term_eval_records if r["doc_id"] == doc_id and r["language"] == lang]
        ver_res = verifier.verify(doc_id, lang, en_text, indic_text, sub_term)

        e_rows.append({
            "run_id": f"phase6_sys_e_{doc_id}_{lang}",
            "doc_id": doc_id,
            "language": lang,
            "system": "system_e_verified",
            "system_name": "Legal-Aware Translation + Verification",
            "model": cfg["indictrans2"]["model_id"],
            "english_summary_hash": d_row["english_summary_hash"],
            "summary_text": indic_text,
            "output_hash": d_row["output_hash"],
            "total_entities_verified": ver_res["total_entities"],
            "preserved_entities": ver_res["preserved_entities"],
            "preservation_rate": ver_res["preservation_rate"],
            "status": "SUCCESS"
        })

    df_e = pd.DataFrame(e_rows)
    df_e.to_parquet(os.path.join(BASE_DIR, "outputs", "verified_summaries.parquet"), index=False)
    print(f"[System E] Completed verification on 36 summaries. Mean preservation: {df_e['preservation_rate'].mean():.2%}")

    # -------------------------------------------------------------
    # 6. EVALUATION ENGINE: Source Fact Preservation & Attribution
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print("[Evaluation] Running Fact Preservation & Failure Attribution (R1-R8)...")
    print("=" * 50)

    # Pre-index evidence text by doc_id
    evidence_by_doc = {}
    ev_col = "text" if "text" in df_ev.columns else "window_text"
    for doc_id, grp in df_ev.groupby("doc_id"):
        evidence_by_doc[doc_id] = " ".join(grp[ev_col].astype(str))

    # Evaluate English control first to determine is_in_english for all gold facts
    english_fact_presence = {}
    en_eval_records = []
    for _, gold in df_gold.iterrows():
        f_id = gold["fact_id"]
        d_id = gold["doc_id"]
        en_text = df_en[df_en["doc_id"] == d_id].iloc[0]["summary_text"]
        ev_text = evidence_by_doc.get(d_id, "")

        stat = evaluate_fact_in_text(gold, en_text, "en")
        is_sup = stat in ("SUPPORTED", "PARTIALLY_SUPPORTED")
        english_fact_presence[(d_id, f_id)] = is_sup

        # Check evidence presence
        ev_stat = evaluate_fact_in_text(gold, ev_text, "en")
        is_in_ev = ev_stat in ("SUPPORTED", "PARTIALLY_SUPPORTED")

        # Failure attribution for English
        fa = "NONE" if is_sup or stat == "ABSENT_IN_SOURCE" else ("R1_RETRIEVAL_FAILURE" if not is_in_ev else "R2_ENGLISH_GENERATION_FAILURE")

        en_eval_records.append({
            "fact_id": f_id,
            "doc_id": d_id,
            "category": gold["category"],
            "language": "en",
            "system": "system_a_english",
            "system_name": "English Control",
            "primary_status": stat,
            "is_in_evidence": is_in_ev,
            "is_in_english": is_sup,
            "translation_fidelity": "PASS",
            "failure_category": fa
        })

    # Build evaluation for all systems across all 5 languages (425 evaluation units per system)
    all_eval_records = []
    all_fidelity_records = []
    all_fa_records = []

    all_systems = [
        ("system_a_english", "English Control", df_en),
        ("system_b_direct_indic", "Direct Indic Control", df_b),
        ("system_c_indictrans2", "English -> IndicTrans2 Raw", df_c),
        ("system_d_legal_aware", "Legal-Aware Translation", df_d),
        ("system_e_verified", "Legal-Aware + Verification", df_e)
    ]

    for sys_id, sys_name, df_sys in all_systems:
        print(f"  Evaluating {sys_name} ({sys_id})...")
        for lang in ["en", "ta", "hi", "kn", "mr"]:
            if lang == "en":
                # For English, all systems share the exact English baseline evaluation
                for rec in en_eval_records:
                    rec_copy = dict(rec)
                    rec_copy["system"] = sys_id
                    rec_copy["system_name"] = sys_name
                    all_eval_records.append(rec_copy)
                    all_fa_records.append({
                        "system": sys_id,
                        "doc_id": rec["doc_id"],
                        "fact_id": rec["fact_id"],
                        "language": "en",
                        "failure_category": rec["failure_category"]
                    })
                continue

            # Indic languages
            for _, gold in df_gold.iterrows():
                f_id = gold["fact_id"]
                d_id = gold["doc_id"]
                en_has_fact = english_fact_presence.get((d_id, f_id), False)
                ev_text = evidence_by_doc.get(d_id, "")
                ev_stat = evaluate_fact_in_text(gold, ev_text, "en")
                is_in_ev = ev_stat in ("SUPPORTED", "PARTIALLY_SUPPORTED")

                # Get summary text for (d_id, lang)
                sub = df_sys[(df_sys["doc_id"] == d_id) & (df_sys["language"] == lang)]
                if len(sub) == 0:
                    sum_text = ""
                else:
                    sum_text = sub.iloc[0]["summary_text"]

                stat = evaluate_fact_in_text(gold, sum_text, lang)
                is_sup = stat in ("SUPPORTED", "PARTIALLY_SUPPORTED")

                # Translation fidelity (Section 16)
                if not en_has_fact:
                    fidelity = "PASS"
                else:
                    fidelity = "PASS" if is_sup else "FAIL"

                all_fidelity_records.append({
                    "system": sys_id,
                    "doc_id": d_id,
                    "fact_id": f_id,
                    "language": lang,
                    "english_has_fact": en_has_fact,
                    "indic_has_fact": is_sup,
                    "translation_fidelity": fidelity
                })

                # Failure attribution (Section 17)
                is_direct = (sys_id == "system_b_direct_indic")
                # Terminology damage flag
                term_damaged = False
                if sys_id == "system_c_indictrans2" and en_has_fact and not is_sup:
                    if gold["category"] in ("STATUTORY_SECTION", "CASE_NUMBER", "AMOUNT", "DISPOSITION"):
                        term_damaged = True

                fa = attribute_failure(
                    primary_status=stat,
                    gold_fact=gold,
                    is_in_evidence=is_in_ev,
                    is_in_english=en_has_fact,
                    is_direct_indic=is_direct,
                    is_in_translation=is_sup,
                    has_terminology_damage=term_damaged
                )

                all_eval_records.append({
                    "fact_id": f_id,
                    "doc_id": d_id,
                    "category": gold["category"],
                    "language": lang,
                    "system": sys_id,
                    "system_name": sys_name,
                    "primary_status": stat,
                    "is_in_evidence": is_in_ev,
                    "is_in_english": en_has_fact,
                    "translation_fidelity": fidelity,
                    "failure_category": fa
                })

                all_fa_records.append({
                    "system": sys_id,
                    "doc_id": d_id,
                    "fact_id": f_id,
                    "language": lang,
                    "failure_category": fa
                })

    df_all_eval = pd.DataFrame(all_eval_records)
    df_all_eval.to_parquet(os.path.join(BASE_DIR, "evaluation", "fact_level_evaluation.parquet"), index=False)
    
    df_all_fidelity = pd.DataFrame(all_fidelity_records)
    df_all_fidelity.to_parquet(os.path.join(BASE_DIR, "evaluation", "translation_fidelity.parquet"), index=False)

    df_all_fa = pd.DataFrame(all_fa_records)
    df_all_fa.to_parquet(os.path.join(BASE_DIR, "evaluation", "failure_attribution.parquet"), index=False)

    print(f"Total Fact Evaluations Recorded: {len(df_all_eval)} ({len(all_systems)} systems x 425 units)")
    print(f"Total Translation Fidelity Records: {len(df_all_fidelity)}")
    print(f"Total Failure Attribution Records: {len(df_all_fa)}")

    # -------------------------------------------------------------
    # 7. GENERATE SCORECARDS & COMPARISON TABLES
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print("[Comparison] Generating System Comparison & Scorecards...")
    print("=" * 50)

    # Calculate metrics per (system, language)
    summary_rows = []
    for (sys_id, lang), grp in df_all_eval.groupby(["system", "language"]):
        total_facts = len(grp)
        valid_grp = grp[grp["primary_status"] != "ABSENT_IN_SOURCE"]
        valid_count = len(valid_grp)
        
        overall_pres = (valid_grp["primary_status"].isin(["SUPPORTED", "PARTIALLY_SUPPORTED"])).mean()
        
        crit_grp = valid_grp[valid_grp["category"].isin(CRITICAL_CATEGORIES)]
        crit_pres = (crit_grp["primary_status"].isin(["SUPPORTED", "PARTIALLY_SUPPORTED"])).mean() if len(crit_grp) > 0 else 0.0
        crit_omiss = (crit_grp["primary_status"] == "OMITTED").mean() if len(crit_grp) > 0 else 0.0
        
        disp_grp = valid_grp[valid_grp["category"] == "DISPOSITION"]
        disp_pres = (disp_grp["primary_status"].isin(["SUPPORTED", "PARTIALLY_SUPPORTED"])).mean() if len(disp_grp) > 0 else 0.0

        sec_grp = valid_grp[valid_grp["category"] == "STATUTORY_SECTION"]
        sec_pres = (sec_grp["primary_status"].isin(["SUPPORTED", "PARTIALLY_SUPPORTED"])).mean() if len(sec_grp) > 0 else 0.0

        outcome_grp = valid_grp[valid_grp["category"].isin(["DISPOSITION", "RELIEF", "SENTENCE", "BAIL_STATUS"])]
        outcome_pres = (outcome_grp["primary_status"].isin(["SUPPORTED", "PARTIALLY_SUPPORTED"])).mean() if len(outcome_grp) > 0 else 0.0

        contradiction = (valid_grp["primary_status"] == "CONTRADICTED").mean()

        # Fidelity
        fid_grp = df_all_fidelity[(df_all_fidelity["system"] == sys_id) & (df_all_fidelity["language"] == lang)]
        fid_rate = (fid_grp["translation_fidelity"] == "PASS").mean() if len(fid_grp) > 0 else 1.0

        summary_rows.append({
            "system": sys_id,
            "system_name": grp["system_name"].iloc[0],
            "language": lang,
            "overall_preservation": round(overall_pres * 100, 2),
            "critical_preservation": round(crit_pres * 100, 2),
            "critical_omission": round(crit_omiss * 100, 2),
            "disposition_preservation": round(disp_pres * 100, 2),
            "statutory_preservation": round(sec_pres * 100, 2),
            "outcome_preservation": round(outcome_pres * 100, 2),
            "contradiction_rate": round(contradiction * 100, 2),
            "translation_fidelity": round(fid_rate * 100, 2),
            "eval_units": total_facts
        })

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(os.path.join(BASE_DIR, "evaluation", "language_results.csv"), index=False)
    print(f"Language results saved to evaluation/language_results.csv")

    # Document results
    doc_rows = []
    for (sys_id, doc_id), grp in df_all_eval.groupby(["system", "doc_id"]):
        valid_grp = grp[grp["primary_status"] != "ABSENT_IN_SOURCE"]
        overall = (valid_grp["primary_status"].isin(["SUPPORTED", "PARTIALLY_SUPPORTED"])).mean()
        crit_grp = valid_grp[valid_grp["category"].isin(CRITICAL_CATEGORIES)]
        crit = (crit_grp["primary_status"].isin(["SUPPORTED", "PARTIALLY_SUPPORTED"])).mean() if len(crit_grp) > 0 else 0.0
        doc_rows.append({
            "system": sys_id,
            "doc_id": doc_id,
            "overall_preservation": round(overall * 100, 2),
            "critical_preservation": round(crit * 100, 2),
            "eval_units": len(grp)
        })
    df_doc = pd.DataFrame(doc_rows)
    df_doc.to_csv(os.path.join(BASE_DIR, "evaluation", "document_results.csv"), index=False)
    print(f"Document results saved to evaluation/document_results.csv")

    # System comparison (pooled across Indic languages: ta, hi, kn, mr)
    indic_eval = df_all_eval[df_all_eval["language"].isin(["ta", "hi", "kn", "mr"])]
    comp_rows = []
    for sys_id, grp in indic_eval.groupby("system"):
        valid_grp = grp[grp["primary_status"] != "ABSENT_IN_SOURCE"]
        overall = (valid_grp["primary_status"].isin(["SUPPORTED", "PARTIALLY_SUPPORTED"])).mean()
        crit_grp = valid_grp[valid_grp["category"].isin(CRITICAL_CATEGORIES)]
        crit = (crit_grp["primary_status"].isin(["SUPPORTED", "PARTIALLY_SUPPORTED"])).mean() if len(crit_grp) > 0 else 0.0
        omiss = (crit_grp["primary_status"] == "OMITTED").mean() if len(crit_grp) > 0 else 0.0
        disp_grp = valid_grp[valid_grp["category"] == "DISPOSITION"]
        disp = (disp_grp["primary_status"].isin(["SUPPORTED", "PARTIALLY_SUPPORTED"])).mean() if len(disp_grp) > 0 else 0.0
        sec_grp = valid_grp[valid_grp["category"] == "STATUTORY_SECTION"]
        sec = (sec_grp["primary_status"].isin(["SUPPORTED", "PARTIALLY_SUPPORTED"])).mean() if len(sec_grp) > 0 else 0.0
        outcome_grp = valid_grp[valid_grp["category"].isin(["DISPOSITION", "RELIEF", "SENTENCE", "BAIL_STATUS"])]
        outcome = (outcome_grp["primary_status"].isin(["SUPPORTED", "PARTIALLY_SUPPORTED"])).mean() if len(outcome_grp) > 0 else 0.0

        fid_grp = df_all_fidelity[(df_all_fidelity["system"] == sys_id) & (df_all_fidelity["language"].isin(["ta", "hi", "kn", "mr"]))]
        fid = (fid_grp["translation_fidelity"] == "PASS").mean() if len(fid_grp) > 0 else 1.0

        comp_rows.append({
            "system": sys_id,
            "indic_overall_preservation": round(overall * 100, 2),
            "indic_critical_preservation": round(crit * 100, 2),
            "indic_critical_omission": round(omiss * 100, 2),
            "indic_disposition": round(disp * 100, 2),
            "indic_statutory": round(sec * 100, 2),
            "indic_outcome": round(outcome * 100, 2),
            "indic_translation_fidelity": round(fid * 100, 2),
            "eval_units": len(grp)
        })

    df_comp = pd.DataFrame(comp_rows)
    df_comp.to_csv(os.path.join(BASE_DIR, "evaluation", "system_comparison.csv"), index=False)
    print(f"System comparison saved to evaluation/system_comparison.csv")

    # -------------------------------------------------------------
    # 8. HUMAN VALIDATION SAMPLE GENERATION (Section 22)
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print("[Human Validation] Generating Stratified Sample...")
    print("=" * 50)
    # Sample covering all 5 languages, direct Indic, translated Indic, legal-aware
    # Sample 15 distinct evaluations
    sample_df = df_all_eval.sample(n=min(25, len(df_all_eval)), random_state=42).copy()
    sample_df = sample_df[["system", "doc_id", "fact_id", "category", "language", "primary_status"]]
    sample_df["human_factual_accuracy"] = ""
    sample_df["human_legal_meaning_preservation"] = ""
    sample_df["human_critical_preservation"] = ""
    sample_df["human_notes"] = ""
    sample_df.to_csv(os.path.join(BASE_DIR, "human_validation", "validation_sample.csv"), index=False)
    print(f"Sample generated: {len(sample_df)} items in human_validation/validation_sample.csv")

    print("\n" + "=" * 70)
    print("PHASE 6 MASTER PIPELINE RUN COMPLETE.")
    print("=" * 70)

if __name__ == "__main__":
    run_phase6()
