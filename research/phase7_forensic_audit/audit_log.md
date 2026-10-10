# Vidhik Phase 7 Forensic Audit Log

**Auditor:** Antigravity Forensic Evaluation Subsystem  
**Date:** 2026-10-06  
**Subject:** Phase 7 Translation Layer Discrepancy & Identity Audit  
**Classification:** AUDIT_PASS_WITH_CORRECTIONS  

---

## 1. Audit Initiation & Core Suspicions
The forensic audit was initiated to investigate two critical suspicions regarding the Phase 7 reports:
1. **Suspicion A:** Systems T2, T3, T4, and T5 reported identical evaluation numbers (44.74% critical partial preservation, 23.68% critical strict preservation, 55.26% critical omission, 48.24% fidelity, 100% terminology survival).
2. **Suspicion B:** All four Indic languages (Tamil, Hindi, Kannada, Marathi) reported identical preservation and fidelity rates (9/38 strict, 10/38 partial in T0; 9/38 strict, 17/38 partial in T5).

---

## 2. Forensic Findings & Root Cause Analysis

### Finding 1: Frozen Input Verification (PASS)
- `frozen_gold_facts.parquet`: SHA-256 `e41e9880baf54fa385be5d095584669aa36d861c27c4805b049f551ea0a09ac9`. Exactly 85 facts across 9 benchmark documents (38 Critical, 35 Important, 12 Contextual). Zero mutations detected.
- `frozen_english_summaries.parquet`: Exactly 9 documents. All 9 summary hashes match the Phase 6 intermediate summaries with zero modifications.

### Finding 2: Language Independence (PASS)
- Audited `output_hash_matrix.csv` and `language_hash_audit.csv`.
- For every document ($N=9$) and every system ($N=6$), the translations into Tamil, Hindi, Kannada, and Marathi have **100% distinct output hashes** and **100% distinct texts**.
- Target languages were preserved end-to-end (`tam_Taml`, `hin_Deva`, `kan_Knda`, `mar_Deva`). No cross-language leakage or cache collision occurred.

### Finding 3: Explanation of Suspicion B (Why Language Results Were Numerically Identical)
- The evaluation engine tests for exact match of normalized legal entities (case numbers, section digits, and protected party strings).
- Because English legal summaries contain standardized entity strings (e.g., `State of Telangana`, `Section 138 NI Act`), the enhanced entity restoration layer deterministically restored these verbatim into the text across all 4 target languages.
- As a result, the exact same 17 critical facts per document survived across Tamil, Hindi, Kannada, and Marathi. The identical metric values across languages reflect the **deterministic nature of the entity restoration layer**, not an aggregation or duplication bug.

### Finding 4: Explanation of Suspicion A (Why T2, T3, T4, and T5 Shared Headline Preservation)
- Inspected `phase7_translation/translation/run_phase7_pipeline.py` (lines 80-112).
- **T0 vs T1:** T1 assigned `t1_text = raw_d`, resulting in 36/36 identical hashes with T0 (0.0% incremental contribution).
- **T3 vs T4 vs T5:** Lines 94, 100, and 103 show that T3, T4, and T5 all restored `reg_t2` over `raw_d` because in T4's candidate selection, `sc_d >= sc_c` held across all 36 cells.
- Consequently, T3, T4, and T5 produced **36/36 identical output texts** (100.0% hash identity).
- **T2 vs T5:** T2 applied entity restoration over `raw_c` (raw IndicTrans2), whereas T5 applied entity restoration over `raw_d` (Phase 6 legal-aware translation). Their output texts are **100% distinct** (0/36 hash matches).
- However, their evaluated preservation score was identical (44.74%) because the specific facts that changed from T0 to T2/T5 were the 7 `PARTIES` facts (`State of Telangana`), which were restored equally in both T2 and T5.

### Finding 5: Forensic Provenance of the +28 Fact Units
- Investigated `t0_t2_fact_changes.csv`.
- The improvement from T0 (40/152 = 26.32%) to T2/T5 (68/152 = 44.74%) comes exclusively from **7 unique critical gold facts** changing from `OMITTED` to `PARTIALLY_SUPPORTED` across the 4 languages ($7 \times 4 = 28$ units):
  - `GF-DC_000001-0003`: `State of Telangana (SHO Srirampur)`
  - `GF-DC_000002-0003`: `State of Telangana (SHO Kotapally)`
  - `GF-DC_000003-0003`: `State of Telangana (SI Neelwai)`
  - `GF-DC_000004-0003`: `State of Telangana (SI Kotapally)`
  - `GF-DC_000005-0003`: `State of Telangana (SI Kotapally)`
  - `GF-DC_000007-0003`: `State of Telangana (SHO Chennur)`
  - `GF-DC_000008-0003`: `State of Telangana (SHO Kotapalli)`
- Enhanced entity protection successfully masked and restored `State of Telangana` across all documents, which baseline T0 failed to protect.
- **Scientific Verdict:** The empirical gain is genuine and driven exclusively by **Enhanced Legal Terminology & Entity Protection (T2)**. Systems T1, T3, T4, and T5 demonstrated **no incremental empirical contribution** on this benchmark.

---

## 3. Authoritative Audit Decision
- **Audit Status:** `AUDIT_PASS_WITH_CORRECTIONS`
- **Recommended Architectural Adoption:** **`ADOPT_ENHANCED_TERMINOLOGY_ENTITY_PROTECTION`** (System T2).
