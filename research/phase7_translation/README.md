# Phase 7: English → Indian Language Translation Layer

**Vidhik Indian Legal AI Research Pipeline**  
**Phase 7: Controlled Legal Translation Engineering & Evaluation**  

---

## 1. Overview & Objective
Following the authoritative Phase 6 decision (`ADOPT_ENGLISH_FIRST`), the production architecture of Vidhik is frozen:

```text
District Court PDF ──> Verified Extraction ──> Evidence Retrieval (BM25 B=8)
      ──> English Legal Summarization (Qwen3) ──> FIXED ENGLISH SUMMARY
      ──> English → Indian Language Translation ──> Tamil / Hindi / Kannada / Marathi
```

Phase 7 evaluates how the validated English legal summary can be translated into **Tamil**, **Hindi**, **Kannada**, and **Marathi** while preserving legally important facts, entities, terminology, and judicial outcomes without hallucinations or semantic drift.

---

## 2. Experimental Systems
- **T0 — Baseline Legal-Aware Translation:** Replicates the Phase 6 System D baseline.
- **T1 — Context-Aware Translation:** Sentence translation with surrounding contextual prefix cues.
- **T2 — Enhanced Legal Terminology & Entity Protection:** Comprehensive regex + glossary masking for case numbers, statutory sections, dates, currency amounts, parties, and dispositions.
- **T3 — Claim & Sentence Aligned Translation:** Enforces 1-to-1 English claim-to-Indic sentence boundary alignment.
- **T4 — Candidate Generation & Legal Reranking:** Multi-candidate beam decoding reranked via deterministic entity, terminology, and contradiction scoring.
- **T5 — Combined Optimal Translation Pipeline:** Integrates Enhanced Protection (T2) + Claim Alignment (T3) + Legal Reranking (T4).

---

## 3. Frozen Benchmark
- **Documents:** 9 certified District Court judgments.
- **Gold Facts:** Exactly 85 certified, human-verified facts (38 Critical, 35 Important, 12 Contextual). SHA-256: `e41e9880baf54fa385be5d095584669aa36d861c27c4805b049f551ea0a09ac9`.
- **Target Indic Languages:** 4 languages (`ta`, `hi`, `kn`, `mr`).
- **Evaluation Universes:**
  - Critical Fact-Language Units: **152 units** ($38 \times 4$).
  - Total Indic Fact-Language Units: **340 units** ($85 \times 4$).
- **Fixed English Input:** 100% byte-identical hashes across all runs.

---

## 4. Key Results & Official Decision

### **OFFICIAL VERDICT:** `ADOPT_IMPROVED_TRANSLATION`

| Metric | Phase 6 Baseline (T0) | Phase 7 Optimal (T5) | Absolute Delta ($\Delta$) | Relative Improvement |
|---|---:|---:|---:|---:|
| **Critical Strict Preservation** | 23.68% (36/152) | 23.68% (36/152) | +0.00% | Preserved |
| **Critical Partial-Inclusive Preservation** | 26.32% (40/152) | **44.74%** (68/152) | **+18.42%** | **+70.0%** |
| **Critical Omission Rate** | 73.68% (112/152) | **55.26%** (84/152) | **-18.42%** | **-25.0%** |
| **Overall Fact Preservation** | 12.94% (44/340) | **21.18%** (72/340) | **+8.24%** | **+63.7%** |
| **Translation Fidelity** | 40.00% (136/340) | **48.24%** (164/340) | **+8.24%** | **+20.6%** |
| **Legal Terminology Survival** | 100.0% (100/100) | **100.0%** (144/144) | 0.00% | Flawless |
| **Contradiction Rate** | 0.00% | **0.00%** | 0.00% | Safe |
| **Unsupported Additions** | 0.00% | **0.00%** | 0.00% | Safe |

---

## 5. Directory Layout
```text
phase7_translation/
├── README.md
├── config/
│   ├── translation_config.yaml
│   ├── model_registry.yaml
│   └── terminology_registry.yaml
├── inputs/
│   ├── frozen_english_summaries.parquet
│   ├── frozen_gold_facts.parquet
│   ├── frozen_benchmark_manifest.parquet
│   └── frozen_evidence_manifest.parquet
├── translation/
│   ├── translation_systems.py
│   ├── translation_runner.py
│   └── run_phase7_pipeline.py
├── outputs/
│   ├── translations.parquet
│   ├── translations.csv
│   ├── sentence_alignment.parquet
│   ├── entity_translation_results.parquet
│   └── fact_level_evaluation.parquet
├── evaluation/
│   └── evaluate_translation.py
├── human_validation/
│   ├── generate_sample.py
│   ├── validation_sample.csv
│   └── annotation_schema.md
├── results/
│   ├── system_comparison.csv
│   ├── language_results.csv
│   ├── document_results.csv
│   ├── failure_attribution.csv
│   └── ablation_results.csv
├── reports/
│   ├── PHASE7_TRANSLATION_REPORT.md
│   ├── PHASE7_TRANSLATION_TABLES.md
│   └── PHASE7_FAILURE_ANALYSIS.md
└── tests/
    └── test_phase7_translation.py
```

---

## 6. Regression Testing
Run the complete automated test suite:
```bash
pytest phase7_translation/tests/test_phase7_translation.py -v
```
All **20/20 tests** pass.
