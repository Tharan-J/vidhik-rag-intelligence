# Phase 6: Multilingual Architecture Experiment

**Vidhik Research Pipeline — Multilingual Legal Summarization Architecture**

## 1. Overview & Objective

Phase 6 investigates the root cause of the severe multilingual generation collapse observed in Phase 4 and Phase 5, and experimentally evaluates whether an **English-First Translation Architecture**:

$$\text{Evidence (BM25 } B=8\text{)} \longrightarrow \text{English Qwen3} \longrightarrow \text{IndicTrans2} \longrightarrow \text{Indic Legal Summary}$$

outperforms:

$$\text{Evidence (BM25 } B=8\text{)} \longrightarrow \text{Direct Indic Qwen3} \longrightarrow \text{Indic Legal Summary}$$

across **Tamil (ta)**, **Hindi (hi)**, **Kannada (kn)**, and **Marathi (mr)**.

---

## 2. Experimental Systems

- **System A — English Control:**
  Reproduces the Phase 5 repaired BM25 $B=8$ English baseline ($N=9$). Serves as the controlled intermediate representation.
- **System B — Direct Indic Control:**
  Phase 5 repaired BM25 $B=8$ direct Indic generation baseline ($N=36$).
- **System C — English $\to$ IndicTrans2 Raw Translation:**
  Raw neural translation of the frozen English summaries via `ai4bharat/indictrans2-en-indic-dist-200M` ($N=36$).
- **System D — Legal-Aware Translation:**
  Pre-translation entity and terminology protection (regex and controlled legal glossaries), followed by IndicTrans2, and post-translation restoration ($N=36$).
- **System E — Legal-Aware Translation + Deterministic Verification:**
  System D outputs verified via deterministic legal fact checking ($N=36$).

---

## 3. Frozen Benchmarks & Denominators

- **Benchmark Documents:** 9 District Court judgments (`DC_000001` - `DC_000008`, `DC_000011`).
- **Gold Legal Facts:** 85 certified, human-verified, source-grounded facts.
- **Languages:** 5 (`en`, `ta`, `hi`, `kn`, `mr`).
- **Summary Cells:** Exactly 45 cells per comparative run ($9 \times 5$).
- **Evaluation Units:** Exactly 425 fact-language evaluation units per system ($85 \times 5$).
- **Evidence:** Frozen BM25 $B=8$ manifest (SHA-256: `a6ded9f093ae56ae23e0cb6c9d99e6eb895820a855a5760bb5a69eabf1dc9b9c`).

---

## 4. Key Results (Authoritative Reconciled)

- **Official Decision:** `ADOPT_ENGLISH_FIRST`
- **Indic Critical Fact Preservation (Strict / Partial-Inclusive across 152 Indic critical units):**
  - Direct Indic Qwen3 (System B): **6.58%** (Strict) / **7.24%** (Partial-Inclusive)
  - IndicTrans2 Raw (System C): **21.05%** ($\Delta = +13.81\%$)
  - Legal-Aware Translation (System D): **23.68%** (Strict) / **26.32%** (Partial-Inclusive) ($\Delta = +19.08\%$)
- **Indic Critical Fact Omission:**
  - Direct Indic Qwen3 (System B): **92.76%**
  - IndicTrans2 Raw (System C): **78.95%** ($\Delta = -13.81\%$)
  - Legal-Aware Translation (System D): **73.68%** ($\Delta = -19.08\%$)
- **Indic Translation Fidelity (across 340 Indic fact units):**
  - Direct Indic Qwen3: **32.35%** (110/340)
  - IndicTrans2 Raw: **36.47%** (124/340)
  - Legal-Aware Translation: **40.00%** (136/340)
- **Legal Terminology / Entity Preservation (across 100 protected units):**
  - Direct Indic Qwen3: **28.0%**
  - IndicTrans2 Raw: **62.0%**
  - Legal-Aware Translation: **100.0%** ($\Delta = +72.0\%$)

---

## 5. Artifact Directory Layout

```text
phase6_multilingual_architecture/
├── README.md
├── config/
│   ├── phase6_config.yaml
│   └── terminology_config.yaml
├── inputs/
│   ├── frozen_benchmark_manifest.parquet
│   ├── frozen_gold_facts.parquet
│   ├── frozen_evidence_manifest.parquet
│   └── input_hash_manifest.json
├── systems/
│   ├── system_a_english/
│   ├── system_b_direct_indic/
│   ├── system_c_indictrans2/
│   │   └── translator.py
│   ├── system_d_legal_aware/
│   │   ├── entity_protection.py
│   │   └── translator.py
│   └── system_e_verified/
│       └── verifier.py
├── outputs/
│   ├── english_summaries.parquet
│   ├── direct_indic_summaries.parquet
│   ├── indictrans2_summaries.parquet
│   ├── legal_aware_summaries.parquet
│   └── verified_summaries.parquet
├── evaluation/
│   ├── fact_level_evaluation.parquet
│   ├── translation_fidelity.parquet
│   ├── terminology_evaluation.parquet
│   ├── failure_attribution.parquet
│   ├── document_results.csv
│   ├── language_results.csv
│   └── system_comparison.csv
├── human_validation/
│   ├── validation_sample.csv
│   └── validation_results.csv
├── reports/
│   ├── PHASE6_MULTILINGUAL_ARCHITECTURE_REPORT.md
│   ├── PHASE6_COMPARISON_TABLES.md
│   └── PHASE6_FAILURE_ANALYSIS.md
├── tests/
│   └── test_phase6_multilingual_architecture.py
├── run_phase6_pipeline.py
└── generate_reports.py
```
