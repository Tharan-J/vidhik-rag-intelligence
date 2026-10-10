# Phase 6 Forensic Audit: Artifact Inventory & Provenance

**Audit Date:** 2026-10-05  
**Subject:** Vidhik Phase 6 Multilingual Architecture Experiment  
**Status:** FORENSIC AUDIT COMPLETE — RECONCILED TO RAW DATA  

---

## 1. Input Benchmark Artifacts

| Artifact Name | File Path | Format | Rows / Units | SHA-256 Hash | Provenance & Role |
|---|---|---|---:|---|---|
| **Frozen Gold Facts** | `phase6_multilingual_architecture/inputs/frozen_gold_facts.parquet` | Parquet | 85 facts | `e41e9880baf54fa385be5d095584669aa36d861c27c4805b049f551ea0a09ac9` | Phase 5.1 certified ground truth (38 Critical, 35 Important, 12 Contextual). Immutable. |
| **Frozen Evidence Manifest** | `phase6_multilingual_architecture/inputs/frozen_evidence_manifest.parquet` | Parquet | 66 windows | `a6ded9f093ae56ae23e0cb6c9d99e6eb895820a855a5760bb5a69eabf1dc9b9c` | Phase 5.2 optimized BM25 B=8 contextual retrieval windows. Immutable. |
| **Benchmark Manifest** | `phase6_multilingual_architecture/inputs/frozen_benchmark_manifest.parquet` | Parquet | 9 docs | `2f9f1b206775d787042a98f45a05b1ee289d042cf8aafebe5a4855ad256ad6a7` | 9 certified District Court judgments (`DC_000001` - `DC_000008`, `DC_000011`). |
| **Input Hash Manifest** | `phase6_multilingual_architecture/inputs/input_hash_manifest.json` | JSON | 4 keys | `1b135b5e7d23d8c36b44a7f920253457a419eb9e9d6d3934f039d96c91a3c757` | Cryptographic seal of benchmark inputs. |

---

## 2. Model Generation Output Artifacts

| System | Output File | Format | Rows | Description | Execution Integrity |
|---|---|---|---:|---|---|
| **System A** | `outputs/english_summaries.parquet` | Parquet | 9 | English Qwen3 summaries with BM25 B=8 | Complete (9/9 docs) |
| **System B** | `outputs/direct_indic_summaries.parquet` | Parquet | 36 | Direct Indic Qwen3 summaries (`ta`, `hi`, `kn`, `mr`) | Complete (36/36 cells) |
| **System C** | `outputs/indictrans2_summaries.parquet` | Parquet | 36 | Raw IndicTrans2 translation of System A | Complete (36/36 cells) |
| **System D** | `outputs/legal_aware_summaries.parquet` | Parquet | 36 | Legal-aware protected IndicTrans2 translation | Complete (36/36 cells) |
| **System E** | `outputs/verified_summaries.parquet` | Parquet | 36 | System D translations with verification pass | Complete (36/36 cells) |
| **Cache** | `outputs/translation_cache.json` | JSON | 72 entries | Cached translation pairs for reproducibility | Complete |

---

## 3. Evaluation Artifacts

| Artifact | File Path | Format | Rows | Denominator / Universe | Description |
|---|---|---|---:|---|---|
| **Fact-Level Evaluation** | `evaluation/fact_level_evaluation.parquet` | Parquet | 2,125 | 5 systems × 425 fact-language units | Comprehensive primary fact status (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `OMITTED`) |
| **Translation Fidelity** | `evaluation/translation_fidelity.parquet` | Parquet | 1,700 | 4 systems × 425 fact-language units | Unit-level semantic preservation between English intermediate and Indic translation |
| **Terminology Evaluation** | `evaluation/terminology_evaluation.parquet` | Parquet | 100 | 25 entities × 4 Indic languages | Exact entity preservation (case numbers, statutes, sections, amounts) |
| **Failure Attribution** | `evaluation/failure_attribution.parquet` | Parquet | 2,125 | 5 systems × 425 fact-language units | Causal failure categorization (`R1` to `R8`) |
| **System Comparison CSV** | `evaluation/system_comparison.csv` | CSV | 5 systems | 340 Indic evaluation units per system | Recomputed aggregate empirical results |
| **Language Results CSV** | `evaluation/language_results.csv` | CSV | 25 rows | 5 systems × 5 languages (85 units each) | Per-language performance breakdown |
| **Document Results CSV** | `evaluation/document_results.csv` | CSV | 45 rows | 5 systems × 9 documents | Document-level aggregation |

---

## 4. Human Validation Artifacts

| Artifact | File Path | Format | Rows | Description |
|---|---|---|---:|---|
| **Validation Sample** | `human_validation/validation_sample.csv` | CSV | 25 | Stratified sample of fact evaluations across systems and languages |
| **Validation Results** | `human_validation/validation_results.csv` | CSV | 25 | Independent human validation showing 96.0% evaluator agreement (24/25) |
