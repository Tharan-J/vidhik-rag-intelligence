"""
Phase 7 Translation Pipeline Runner
Executes:
- T0 (Baseline Legal-Aware)
- T1 (Context-Aware)
- T2 (Stronger Legal Terminology)
- T3 (Claim-Aligned)
- T4 (Candidate Generation + Legal Reranking)
- T5 (Combined Optimal)
Across 9 frozen District Court documents and 4 Indic languages (ta, hi, kn, mr).
Total = 6 systems * 36 cells = 216 summary translations.
Uses caching to guarantee exact reproducibility and speed.
"""

import os
import sys
import json
import time
import hashlib
import pandas as pd
import yaml

sys.path.append(os.path.abspath("phase7_translation"))
from translation.translation_systems import (
    SharedIndicTrans2Engine,
    BaselineTranslator,
    ContextTranslator,
    TerminologyProtectedTranslator,
    AlignedTranslator,
    CandidateRerankTranslator,
    CombinedTranslator,
    EnhancedLegalEntityProtector
)

BASE_DIR = "phase7_translation"

def run_translation_experiments():
    print("=" * 70)
    print("VIDHIK PHASE 7: TRANSLATION LAYER EXPERIMENTAL RUNNER")
    print("=" * 70)

    # 1. Load config
    with open(os.path.join(BASE_DIR, "config", "translation_config.yaml"), "r") as f:
        cfg = yaml.safe_load(f)

    # 2. Load frozen English summaries
    df_en = pd.read_parquet(os.path.join(BASE_DIR, "inputs", "frozen_english_summaries.parquet"))
    docs = sorted(df_en["doc_id"].unique())
    print(f"Loaded {len(df_en)} frozen English summaries across docs: {docs}")

    # Verify input hashes
    en_hash_map = dict(zip(df_en["doc_id"], df_en["output_hash"]))
    for doc_id, h in en_hash_map.items():
        print(f"  {doc_id}: {h[:16]}...")

    target_languages = ["ta", "hi", "kn", "mr"]

    # 3. Initialize Shared Engine
    engine = SharedIndicTrans2Engine.get_instance(
        model_id=cfg["indictrans2"]["model_id"],
        device=cfg["indictrans2"].get("device_preference")
    )

    # 4. Initialize Translators
    enhanced_protector = EnhancedLegalEntityProtector()
    translators = {
        "T0": BaselineTranslator(engine),
        "T1": ContextTranslator(engine, baseline_protector=translators_t0 if 'translators_t0' in locals() else BaselineTranslator(engine)),
        "T2": TerminologyProtectedTranslator(engine),
        "T3": AlignedTranslator(engine, enhanced_protector),
        "T4": CandidateRerankTranslator(engine, enhanced_protector),
        "T5": CombinedTranslator(engine, enhanced_protector)
    }

    # Cache file
    cache_path = os.path.join(BASE_DIR, "outputs", "translation_cache.json")
    cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
            print(f"Loaded existing translation cache ({len(cache)} entries).")
        except Exception as e:
            print(f"Cache notice: {e}")

    def save_cache():
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)

    all_translations = []
    sentence_alignments = []
    entity_results = []
    terminology_results = []

    system_order = [
        ("T0", "T0_BASELINE_LEGAL_AWARE", "Phase 6 Legal-Aware Baseline"),
        ("T1", "T1_CONTEXT_AWARE", "Context-Aware Translation"),
        ("T2", "T2_STRONGER_TERMINOLOGY", "Enhanced Legal Terminology & Entity Protection"),
        ("T3", "T3_CLAIM_ALIGNED", "Claim & Sentence Aligned Translation"),
        ("T4", "T4_CANDIDATE_RERANKING", "Candidate Generation & Legal Reranking"),
        ("T5", "T5_COMBINED_OPTIMAL", "Combined Optimal Translation Pipeline")
    ]

    for sys_key, sys_id, sys_name in system_order:
        print(f"\n>>> Running System: {sys_name} ({sys_id})")
        translator = translators[sys_key]

        for doc_id in docs:
            en_row = df_en[df_en["doc_id"] == doc_id].iloc[0]
            en_text = en_row["summary_text"]
            en_hash = en_hash_map[doc_id]

            for lang in target_languages:
                cache_key = f"{sys_id}_{doc_id}_{lang}_{en_hash}"
                if cache_key in cache:
                    res = cache[cache_key]
                else:
                    res = translator.translate(en_text, lang)
                    cache[cache_key] = res
                    save_cache()

                indic_text = res.get("translated_text") or res.get("summary_text", "")
                out_hash = res.get("output_hash", hashlib.sha256(indic_text.encode("utf-8")).hexdigest())

                all_translations.append({
                    "run_id": f"phase7_{sys_key}_{doc_id}_{lang}",
                    "system_id": sys_id,
                    "system_name": sys_name,
                    "doc_id": doc_id,
                    "source_language": "en",
                    "target_language": lang,
                    "english_summary_sha256": en_hash,
                    "source_text": en_text,
                    "translated_text": indic_text,
                    "output_hash": out_hash,
                    "latency_seconds": res.get("latency_seconds", 0.0),
                    "model_name": cfg["indictrans2"]["model_id"],
                    "model_version": "v1.0-distilled",
                    "status": "SUCCESS"
                })

                # Record sentence alignments if present
                for sent_item in res.get("sentences", []):
                    sentence_alignments.append({
                        "system_id": sys_id,
                        "doc_id": doc_id,
                        "language": lang,
                        "source_sentence_id": sent_item.get("source_sentence_id", "sent_unknown"),
                        "source_text": sent_item.get("source_text", ""),
                        "translated_text": sent_item.get("translated_text", ""),
                        "alignment_status": sent_item.get("alignment_status", "ALIGNED")
                    })

                # Record audit records if present
                for rec in res.get("audit_records", []):
                    entity_results.append({
                        "system_id": sys_id,
                        "doc_id": doc_id,
                        "language": lang,
                        "category": rec["category"],
                        "source_text": rec["source_text"],
                        "target_text": rec["target_text"],
                        "status": rec["status"]
                    })

    df_trans = pd.DataFrame(all_translations)
    df_trans.to_parquet(os.path.join(BASE_DIR, "outputs", "translations.parquet"), index=False)
    df_trans.to_csv(os.path.join(BASE_DIR, "outputs", "translations.csv"), index=False)
    print(f"\nSaved {len(df_trans)} total translation outputs to outputs/translations.parquet & csv")

    df_align = pd.DataFrame(sentence_alignments)
    df_align.to_parquet(os.path.join(BASE_DIR, "outputs", "sentence_alignment.parquet"), index=False)
    print(f"Saved {len(df_align)} sentence alignment records to outputs/sentence_alignment.parquet")

    df_ent = pd.DataFrame(entity_results)
    df_ent.to_parquet(os.path.join(BASE_DIR, "outputs", "entity_translation_results.parquet"), index=False)
    print(f"Saved {len(df_ent)} entity audit records to outputs/entity_translation_results.parquet")

if __name__ == "__main__":
    run_translation_experiments()
