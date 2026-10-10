"""
Repaired Multilingual Summarization Generator for Vidhik Phase 5
Executes the frozen Qwen3 pipeline across the 9 benchmark documents x 5 languages (45 summaries)
using the experimentally selected BM25 B=8 evidence condition.

Zero changes to model, parameters, prompt condition, or languages.
Resumable execution with per-cell raw JSON caching.
"""

import os
import re
import json
import time
import hashlib
import logging
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Repaired_Summarization")

ROOT_DIR = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT_DIR / "phase5_repaired_summarization"
CONFIG_PATH = EXP_DIR / "config" / "repaired_run_config.yaml"
EVIDENCE_PATH = EXP_DIR / "evidence" / "repaired_bm25_b8_evidence.parquet"
OUTPUTS_DIR = EXP_DIR / "outputs"
RAW_DIR = OUTPUTS_DIR / "raw"
AUDIT_DIR = EXP_DIR / "audit"

RAW_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def call_ollama(
    model_name: str,
    prompt: str,
    system: str = "",
    temperature: float = 0.1,
    top_p: float = 0.95,
    max_tokens: int = 450,
    endpoint: str = "http://localhost:11434/api/generate"
) -> Dict[str, Any]:
    """Call Ollama with strictly frozen parameters and thinking explicitly disabled."""
    payload = {
        "model": model_name,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "think": False,
        "options": {
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens
        }
    }
    t0 = time.time()
    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - t0
            raw_text = data.get("response", "")
            cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
            return {
                "text": cleaned,
                "raw_response": raw_text,
                "latency_ms": int(elapsed * 1000),
                "input_tokens": data.get("prompt_eval_count", len(prompt.split())),
                "output_tokens": data.get("eval_count", len(cleaned.split())),
                "status": "SUCCESS",
                "error": None
            }
    except Exception as e:
        elapsed = time.time() - t0
        return {
            "text": "",
            "raw_response": "",
            "latency_ms": int(elapsed * 1000),
            "input_tokens": len(prompt.split()),
            "output_tokens": 0,
            "status": "FAILURE",
            "error": str(e)
        }


def run_generation():
    logger.info("Initializing Phase 5 Repaired Multilingual Summarization Experiment...")
    cfg = load_config()

    doc_ids = cfg["benchmark"]["benchmark_doc_ids"]
    languages = cfg["languages"]
    model_cfg = cfg["model"]
    prompt_template = cfg["prompt_template"]

    # Load BM25 B=8 evidence
    ev_df = pd.read_parquet(EVIDENCE_PATH)
    logger.info("Loaded %d BM25 B=8 evidence windows across %d documents.", len(ev_df), ev_df["doc_id"].nunique())

    # Build formatted evidence text per document
    doc_evidence_map = {}
    for doc_id, grp in ev_df.groupby("doc_id"):
        grp_sorted = grp.sort_values(by="rank").reset_index(drop=True)
        chunks = []
        for i, row in grp_sorted.iterrows():
            chunks.append(
                f"[Evidence {i+1} | Page {row['page_number']} | Window {row['window_id']}]: {row['text']}"
            )
        combined_text = "\n\n".join(chunks)
        doc_evidence_map[doc_id] = {
            "text": combined_text,
            "window_ids": grp_sorted["window_id"].tolist(),
            "sha256": hashlib.sha256(combined_text.encode("utf-8")).hexdigest()
        }

    summary_records = []
    manifest_records = []
    total_cells = len(doc_ids) * len(languages)
    completed = 0

    logger.info("Executing generation matrix: %d documents x %d languages = %d summary cells.", len(doc_ids), len(languages), total_cells)

    for doc_id in doc_ids:
        doc_ev = doc_evidence_map[doc_id]
        evidence_text = doc_ev["text"]
        ev_window_ids = doc_ev["window_ids"]
        ev_hash = doc_ev["sha256"]

        for lang_code, lang_meta in languages.items():
            completed += 1
            lang_name = lang_meta["name"]
            run_id = f"REPAIRED_SUM_{doc_id}_{lang_code.upper()}"
            raw_file = RAW_DIR / f"{run_id}.json"

            # Check cache
            if raw_file.exists():
                with open(raw_file, "r", encoding="utf-8") as f:
                    cached_record = json.load(f)
                if cached_record.get("status") == "SUCCESS" and cached_record.get("summary_text"):
                    logger.info("[%d/%d] CACHED: %s (%s - %s)", completed, total_cells, run_id, doc_id, lang_name)
                    summary_records.append(cached_record)
                    manifest_records.append({
                        "run_id": run_id,
                        "doc_id": doc_id,
                        "language": lang_code,
                        "status": cached_record["status"],
                        "latency_ms": cached_record["latency_ms"],
                        "input_tokens": cached_record["input_tokens"],
                        "output_tokens": cached_record["output_tokens"],
                        "output_hash": cached_record["output_hash"],
                        "cached": True
                    })
                    continue

            # Format Condition C prompt
            prompt = prompt_template.format(
                language=lang_name,
                evidence_text=evidence_text
            )

            logger.info("[%d/%d] GENERATING: %s (%s - %s)...", completed, total_cells, run_id, doc_id, lang_name)
            res = call_ollama(
                model_name=model_cfg["ollama_tag"],
                prompt=prompt,
                system="You are a professional legal summarizer adhering strictly to facts.",
                temperature=model_cfg["temperature"],
                top_p=model_cfg["top_p"],
                max_tokens=model_cfg["max_tokens"],
                endpoint=model_cfg["endpoint"]
            )

            now_iso = datetime.now(timezone.utc).isoformat()
            out_hash = hashlib.sha256(res["text"].encode("utf-8")).hexdigest() if res["text"] else ""

            record = {
                "run_id": run_id,
                "doc_id": doc_id,
                "language": lang_code,
                "language_name": lang_name,
                "model": model_cfg["name"],
                "model_version": model_cfg["ollama_tag"],
                "prompt_version": "condition_c_v1",
                "generation_condition": model_cfg["generation_condition"],
                "temperature": model_cfg["temperature"],
                "top_p": model_cfg["top_p"],
                "max_tokens": model_cfg["max_tokens"],
                "thinking_enabled": model_cfg["thinking_enabled"],
                "evidence_strategy": cfg["evidence_condition"]["strategy"],
                "evidence_budget": cfg["evidence_condition"]["budget"],
                "evidence_window_ids": ev_window_ids,
                "evidence_hash": ev_hash,
                "summary_text": res["text"],
                "output_hash": out_hash,
                "input_tokens": res["input_tokens"],
                "output_tokens": res["output_tokens"],
                "latency_ms": res["latency_ms"],
                "timestamp": now_iso,
                "status": res["status"],
                "error": res["error"],
                "raw_response": res["raw_response"]
            }

            # Save raw JSON cache
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)

            summary_records.append(record)
            manifest_records.append({
                "run_id": run_id,
                "doc_id": doc_id,
                "language": lang_code,
                "status": res["status"],
                "latency_ms": res["latency_ms"],
                "input_tokens": res["input_tokens"],
                "output_tokens": res["output_tokens"],
                "output_hash": out_hash,
                "cached": False
            })

    # Save structured summaries
    sums_df = pd.DataFrame(summary_records)
    sums_parquet = OUTPUTS_DIR / "summaries.parquet"
    sums_csv = OUTPUTS_DIR / "summaries.csv"
    sums_df.to_parquet(sums_parquet, index=False)
    sums_df.to_csv(sums_csv, index=False)
    logger.info("Saved %d summaries to %s and %s", len(sums_df), sums_parquet, sums_csv)

    # Save generation manifest
    man_df = pd.DataFrame(manifest_records)
    man_csv = AUDIT_DIR / "generation_manifest.csv"
    man_df.to_csv(man_csv, index=False)
    logger.info("Saved generation manifest to %s", man_csv)

    # Build top-level run manifest
    run_manifest = {
        "experiment_id": cfg["experiment_id"],
        "pipeline_version": cfg["pipeline_version"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "benchmark_documents": doc_ids,
        "languages": list(languages.keys()),
        "total_summaries_expected": total_cells,
        "total_summaries_generated": len(sums_df[sums_df["status"] == "SUCCESS"]),
        "total_failures": len(sums_df[sums_df["status"] != "SUCCESS"]),
        "model": model_cfg["name"],
        "model_version": model_cfg["ollama_tag"],
        "prompt_condition": model_cfg["generation_condition"],
        "temperature": model_cfg["temperature"],
        "top_p": model_cfg["top_p"],
        "max_tokens": model_cfg["max_tokens"],
        "thinking_enabled": model_cfg["thinking_enabled"],
        "evidence_strategy": cfg["evidence_condition"]["strategy"],
        "evidence_budget": cfg["evidence_condition"]["budget"],
        "evidence_manifest_sha256": hashlib.sha256(open(EVIDENCE_PATH, "rb").read()).hexdigest(),
        "summaries_parquet_sha256": hashlib.sha256(open(sums_parquet, "rb").read()).hexdigest()
    }
    with open(AUDIT_DIR / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(run_manifest, f, indent=2)
    logger.info("Saved run manifest to %s", AUDIT_DIR / "run_manifest.json")

    return sums_df, man_df, run_manifest


if __name__ == "__main__":
    run_generation()
