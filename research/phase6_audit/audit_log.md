# Vidhik Phase 6 Forensic Audit Log

**Auditor:** Antigravity Forensic Evaluation Subsystem  
**Date:** 2026-10-05  
**Subject:** Phase 6 Multilingual Architecture Discrepancy Reconciliation  

---

## 1. Audit Initiation & Objective
- **Problem Statement:** Conflicting metrics reported between Phase 6 markdown documentation:
  - Report A (`system_comparison.csv`, `language_results.csv`, `PHASE6_COMPARISON_TABLES.md`): Direct Indic Qwen3 **7.2%**, Raw IndicTrans2 **21.1%**, Legal-Aware **26.3%**, Translation Fidelity **40.0%**.
  - Report B (`README.md` draft): Direct Indic Qwen3 **8.6%**, Raw IndicTrans2 **68.4%**, Legal-Aware **76.3%**, Critical Omission **91.4% $\to$ 28.9% $\to$ 18.4%**, Translation Fidelity **89.5%**.
- **Audit Mandate:** Inspect all raw parquet files and code deterministically, establish denominator boundaries, identify root causes of conflicting claims, and deliver an authoritative reconciled result.

---

## 2. Forensic Steps & Verification
1. **Directory Inspection & Inventory:**
   - Checked `phase6_multilingual_architecture/`.
   - Verified existence of all raw inputs, outputs, evaluation parquets, CSVs, and reports.
2. **Benchmark Immutability Verification:**
   - Verified `inputs/frozen_gold_facts.parquet`: SHA-256 `e41e9880baf54fa385be5d095584669aa36d861c27c4805b049f551ea0a09ac9`. Exactly 85 facts across 9 documents (38 Critical, 35 Important, 12 Contextual). No modifications detected.
   - Verified `inputs/frozen_evidence_manifest.parquet`: SHA-256 `a6ded9f093ae56ae23e0cb6c9d99e6eb895820a855a5760bb5a69eabf1dc9b9c`. Exactly 66 retrieval windows.
3. **Execution Integrity & Hash Fairness Check:**
   - Inspected `outputs/english_summaries.parquet`, `outputs/indictrans2_summaries.parquet`, `outputs/legal_aware_summaries.parquet`, and `outputs/verified_summaries.parquet`.
   - Verified that all English intermediate summaries fed into Systems C, D, and E are 100% cryptographically identical for all 9 documents (`9/9 identical summaries`).
   - Verified that System E outputs are 100% text-identical to System D across all 36 document-language cells. System E functions strictly as a verification layer without text rewriting.
4. **Failure Attribution Audit:**
   - Inspected `evaluation/failure_attribution.parquet` and `run_phase6_pipeline.py`.
   - Confirmed failure attribution is determined causally by sequential fact checks (`is_in_evidence`, `is_in_english`, `translation_fidelity`, `primary_status`), rather than hardcoded mappings.
5. **Root Cause Analysis of Discrepancies:**
   - Discovered timestamp gap: `README.md` was authored at **20:34:04**, whereas the neural evaluation pipeline finished at **21:18:14**.
   - Proved that `README.md` contained preliminary draft placeholders copied directly from Phase 5 Evidence Budget Optimization tables:
     - `76.3%`: Copied from `P5_EVIDENCE_BUDGET_TABLES.md` line 36 (`E5_HYBRID_RRF_B8` Critical Evidence Recall $= 29/38 = 76.31\%$).
     - `68.4%`: Phase 5 $B=4$ critical evidence recall ($26/38 = 68.42\%$).
     - `89.5%`: Phase 5 $B=15$ critical evidence recall ($34/38 = 89.47\%$).
     - `91.4%`: Residual complement $100\% - 8.6\% = 91.4\%$.
   - Concluded that Report A (`system_comparison.csv`) is the sole empirical truth from the executed neural models.
6. **Deterministic Recomputation:**
   - Created `phase6_audit/recompute_authoritative_metrics.py`.
   - Recomputed all metrics directly from the 2,125 evaluated rows.

---

## 3. Audit Outcome
- **Authoritative Metrics Validated:**
  - Direct Indic Qwen3 (System B): **6.58%** Strict Critical Preservation (10/152), **7.24%** Partial-Inclusive Critical Preservation (11/152), **92.76%** Critical Omission (141/152).
  - Raw IndicTrans2 (System C): **21.05%** Strict/Partial-Inclusive Critical Preservation (32/152), **78.95%** Critical Omission (120/152).
  - Legal-Aware Translation (System D): **23.68%** Strict Critical Preservation (36/152), **26.32%** Partial-Inclusive Critical Preservation (40/152), **73.68%** Critical Omission (112/152).
  - Translation Fidelity: **40.00%** (136/340).
  - Terminology Preservation: **100.0%** (100/100).
- **Audit Status:** PASS. Reconciled and fully verified.
