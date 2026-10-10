# Phase 6 Forensic Audit & Metric Reconciliation Report

**Project:** Vidhik Legal RAG Pipeline  
**Phase:** Phase 6 — Multilingual Summarization Architecture Experiment  
**Auditor:** Antigravity Forensic Evaluation Subsystem  
**Date:** 2026-10-05  

---

## 1. Executive Verdict

- **Phase 6 Audit Status:** **PASS**
- **Authoritative Decision:** **ADOPT_ENGLISH_FIRST**
- **Discrepancy Status:** **RESOLVED**

The material discrepancies between the Phase 6 reports are definitively resolved. The numbers published in the draft `README.md` (**8.6%**, **68.4%**, **76.3%**, **89.5%**) were unexecuted placeholder numbers copied from the Phase 5 Evidence Budget optimization tables before the neural pipeline ran. 

The empirical, reproducible results from the raw evaluated dataset (`evaluation/fact_level_evaluation.parquet`, 2,125 rows) confirm:
- **Direct Indic Qwen3 (System B):** **7.24%** Critical Preservation (11/152), **92.76%** Critical Omission (141/152).
- **English-First Raw IndicTrans2 (System C):** **21.05%** Critical Preservation (32/152), **78.95%** Critical Omission (120/152).
- **English-First Legal-Aware IndicTrans2 (System D):** **26.32%** Critical Preservation (40/152), **73.68%** Critical Omission (112/152).
- **Translation Fidelity (System D):** **40.00%** (136/340 facts preserved across translation).
- **Legal Terminology Survival (System D):** **100.0%** (100/100 protected entities intact).

The **English-First Legal-Aware architecture (System D)** delivers an absolute gain of **+19.1%** in critical legal fact preservation over direct Indic generation, cuts critical omissions by **19.1%**, achieves **100% entity preservation**, and introduces **0.0% legal contradictions**.

---

## 2. Why the Original Reports Conflicted

The conflict between the Phase 6 reports arose from a clear timestamp and provenance divergence:

1. **Premature Draft Generation:**  
   At **20:34:04**, an initial documentation template for `README.md` was committed. Because the neural translation and summarization pipeline (`run_phase6_pipeline.py`) took ~20 minutes to complete (finishing at **21:18:14**), preliminary estimates from the Phase 5 Evidence Budget Optimization experiment were placed in the README as temporary placeholders.
2. **Conflation with Evidence Retrieval Recall:**  
   The numbers in the draft README correspond directly to Phase 5 evidence recall figures from `phase5_evidence_budget_optimization/reports/P5_EVIDENCE_BUDGET_TABLES.md`:
   - **76.3%**: Phase 5 $B=8$ evidence retrieval recall (`29/38 = 76.31%`).
   - **68.4%**: Phase 5 $B=4$ evidence retrieval recall (`26/38 = 68.42%`).
   - **89.5%**: Phase 5 $B=15$ evidence retrieval recall (`34/38 = 89.47%`).
   - **91.4%**: $100\% - 8.6\% = 91.4\%$ (historical omission rate).
3. **Unreconciled Completion:**  
   When the true model evaluation finished at **21:18:14**, the authoritative tables were written to `evaluation/system_comparison.csv` and `reports/PHASE6_COMPARISON_TABLES.md`, but `README.md` was never updated to reflect the actual model execution.

---

## 3. Frozen Benchmark

The audit verified complete immutability of the frozen inputs:
- **Documents:** 9 certified District Court judgments (`DC_000001` through `DC_000008`, `DC_000011`).
- **Certified Gold Facts:** Exactly 85 facts certified in Phase 5.1 (38 Critical, 35 Important, 12 Contextual). SHA-256: `e41e9880baf54fa385be5d095584669aa36d861c27c4805b049f551ea0a09ac9`.
- **Evidence Budget:** Frozen BM25 $B=8$ manifest (66 total retrieved windows across 9 documents). SHA-256: `a6ded9f093ae56ae23e0cb6c9d99e6eb895820a855a5760bb5a69eabf1dc9b9c`.
- **Languages:** 5 languages (`en`, `ta`, `hi`, `kn`, `mr`).

---

## 4. Artifact Inventory

See [artifact_inventory.md](file:///home/tharan/Seeds/vidhik/phase6_audit/artifact_inventory.md) and [source_inventory.csv](file:///home/tharan/Seeds/vidhik/phase6_audit/source_inventory.csv) for full cryptographic details. All files exist, are uncorrupted, and have valid record counts.

---

## 5. Evaluation-Unit Audit

- **Multilingual Evaluation Universe:** 5 systems $\times$ 9 documents $\times$ 5 languages = 225 summary cells evaluated against 85 gold facts = **2,125 evaluation rows** in `fact_level_evaluation.parquet`.
- **Duplicates & Nulls:** Exactly **0 duplicate rows** and **0 null labels** across all systems, languages, and documents.

---

## 6. Denominator Audit

A critical finding of this audit is distinguishing between evaluation denominators:
- **Full Benchmark Universe ($N=425$):** $85 \text{ facts} \times 5 \text{ languages}$ ($190 \text{ critical units}$). Includes English control.
- **Indic Target Deployment Universe ($N=340$):** $85 \text{ facts} \times 4 \text{ Indic languages}$ (`ta`, `hi`, `kn`, `mr`) ($152 \text{ critical units}$). This is the **authoritative denominator** for evaluating Indic translation and direct Indic summarization.
- **English Intermediate Universe ($N=85$):** $85 \text{ facts} \times 1 \text{ language}$ ($38 \text{ critical units}$).

---

## 7. Critical Fact Preservation

Computed strictly from the 152 Indic critical fact-units:
- **System B (Direct Indic Qwen3):**
  - Strict Preservation (SUPPORTED): **6.58%** (10/152)
  - Partial-Inclusive (SUPPORTED + PARTIAL): **7.24%** (11/152)
- **System C (Raw IndicTrans2):**
  - Strict Preservation: **21.05%** (32/152)
  - Partial-Inclusive: **21.05%** (32/152)
- **System D (Legal-Aware IndicTrans2):**
  - Strict Preservation: **23.68%** (36/152)
  - Partial-Inclusive: **26.32%** (40/152)
- **System E (Verified Legal-Aware):**
  - Strict: **23.68%** (36/152), Partial-Inclusive: **26.32%** (40/152)

---

## 8. Critical Omission

- **System B (Direct Indic):** **92.76%** (141/152 omitted)
- **System C (Raw Translation):** **78.95%** (120/152 omitted)
- **System D (Legal-Aware):** **73.68%** (112/152 omitted)
- **System E (Verified):** **73.68%** (112/152 omitted)

English-First reduces critical omissions by **19.08% absolute** (a relative omission reduction of 20.6%).

---

## 9. Translation Fidelity

- **System D Fidelity:** **40.00%** (136 / 340 Indic fact units preserved without distortion).
- **System C Fidelity:** **36.47%** (124 / 340).
- **System B Fidelity:** **32.35%** (110 / 340).
- The conflicting claim of **89.5%** in the README draft was a transcription error from Phase 5 $B=15$ evidence retrieval recall, not a translation fidelity measurement.

---

## 10. Terminology Preservation

Evaluated over 100 protected legal entities (Case Numbers, Dates, Section numbers, Amounts, Dispositions):
- **System B (Direct Indic):** **28.0%** (28/100) — severe transliteration damage and entity loss.
- **System C (Raw IndicTrans2):** **62.0%** (62/100) — translation model alters digits, casing, and legal terminology.
- **System D (Legal-Aware):** **100.0%** (100/100) — pre-translation entity masking and post-translation restoration completely prevents entity distortion.
- **System E (Verified):** **100.0%** (100/100).

---

## 11. System E Verification Audit

System E applies deterministic verification over System D.
- **Summary Hash Check:** Across all 36 Indic summary outputs, the text generated by System E is **100% identical** to System D.
- **Audit Finding:** System E is a **verification and quality-audit filter**, not an independent generative rewrite architecture. It confirms the validity of System D without altering output text.

---

## 12. English Hash Fairness

For all 9 benchmark documents:
- System A English intermediate SHA-256 hashes were compared against the English inputs used for System C, System D, and System E.
- **Result:** **9 / 9 identical English summaries (100.0%)**.
- The intermediate representation was strictly controlled and frozen across all translation experiments.

---

## 13. Failure Attribution

Failure stages were assigned causally based on evidence availability and output evaluation:
- **R1 (Retrieval Starvation):** 22.4% (95/425 units) — fact absent from BM25 B=8 evidence.
- **R2 (English Generation Omission):** 4.7% (20/425 units) — present in evidence, omitted by Qwen3 English.
- **R3 (Direct Indic Multilingual Collapse):** 56.0% (238/425 units) in System B. Fully cured (0.0%) in English-First architectures.
- **R4 (Translation Divergence):** 48.0% (204/425 units) in Systems C, D, E.
- **R5 (Terminology Failure):** 2.8% in System C; cured (0.0%) in System D.

---

## 14. Metric Reconciliation

Detailed line-by-line reconciliation of conflicting numbers:

### 7.2%
- **Status:** **VALID AUTHORITATIVE METRIC**
- **Definition:** Direct Indic Qwen3 partial-inclusive critical preservation across 152 Indic critical units ($11 / 152 = 7.24\%$).

### 8.6%
- **Status:** **INVALID PRELIMINARY PLACEHOLDER**
- **Definition:** Copied from Phase 5 historical unoptimized baseline estimates before the Phase 6 pipeline ran.

### 21.1%
- **Status:** **VALID AUTHORITATIVE METRIC**
- **Definition:** Raw IndicTrans2 critical preservation across 152 Indic critical units ($32 / 152 = 21.05\%$).

### 26.3%
- **Status:** **VALID AUTHORITATIVE METRIC**
- **Definition:** Legal-Aware IndicTrans2 partial-inclusive critical preservation across 152 Indic critical units ($40 / 152 = 26.32\%$).

### 68.4%
- **Status:** **INVALID TRANSCRIPTION ERROR**
- **Definition:** Conflated with Phase 5 evidence retrieval coverage at budget $B=4$ ($26 / 38 = 68.42\%$).

### 76.3%
- **Status:** **INVALID TRANSCRIPTION ERROR**
- **Definition:** Conflated with Phase 5 evidence retrieval coverage at budget $B=8$ ($29 / 38 = 76.31\%$).

### 40.0%
- **Status:** **VALID AUTHORITATIVE METRIC**
- **Definition:** Fact-level translation fidelity for System D across 340 Indic fact units ($136 / 340 = 40.00\%$).

### 89.5%
- **Status:** **INVALID TRANSCRIPTION ERROR**
- **Definition:** Conflated with Phase 5 evidence retrieval coverage at budget $B=15$ ($34 / 38 = 89.47\%$).

---

## 15. Authoritative Results Table

| System | Language Scope | Docs | Fact Units | Critical Eligible | Supported | Partial | Omitted | Contradicted | Unsupported | Critical Pres. (Strict) | Critical Pres. (Partial) | Critical Omission | Trans. Fidelity | Terminology Pres. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **English Control (A)** | English (`en`) | 9 | 85 | 38 | 25 | 6 | 7 | 0 | 0 | 65.79% | 81.58% | 18.42% | N/A | N/A |
| **Direct Indic Qwen3 (B)** | Indic (`ta,hi,kn,mr`) | 9 | 340 | 152 | 10 | 1 | 141 | 0 | 0 | 6.58% | 7.24% | 92.76% | 32.35% | 28.0% |
| **Raw IndicTrans2 (C)** | Indic (`ta,hi,kn,mr`) | 9 | 340 | 152 | 32 | 0 | 120 | 0 | 0 | 21.05% | 21.05% | 78.95% | 36.47% | 62.0% |
| **Legal-Aware Trans (D)** | Indic (`ta,hi,kn,mr`) | 9 | 340 | 152 | 36 | 4 | 112 | 0 | 0 | 23.68% | 26.32% | 73.68% | 40.00% | 100.0% |
| **Verified Trans (E)** | Indic (`ta,hi,kn,mr`) | 9 | 340 | 152 | 36 | 4 | 112 | 0 | 0 | 23.68% | 26.32% | 73.68% | 40.00% | 100.0% |

---

## 16. Comparison: Direct Indic vs English-First

| Evaluation Dimension | Direct Indic Qwen3 (B) | English-First Legal-Aware (D) | Absolute Improvement ($\Delta$) | Relative Gain |
|---|---:|---:|---:|---:|
| **Critical Fact Preservation** | 7.24% | 26.32% | **+19.08%** | **+263.5%** |
| **Critical Omission Rate** | 92.76% | 73.68% | **-19.08%** | **-20.6%** |
| **Overall Fact Preservation** | 5.29% | 12.94% | **+7.65%** | **+144.6%** |
| **Disposition Preservation** | 0.00% | 33.33% | **+33.33%** | **$\infty$** |
| **Legal Outcome Preservation** | 0.00% | 16.67% | **+16.67%** | **$\infty$** |
| **Terminology Survival** | 28.00% | 100.00% | **+72.00%** | **+257.1%** |
| **Contradiction Rate** | 0.00% | 0.00% | **0.00%** | Neutral (Safe) |

---

## 17. Statistical & Generalization Limitations

- **Benchmark Size:** The benchmark consists of **9 District Court judgments** and **85 certified gold facts**. While this represents high-effort, source-grounded certification, empirical claims apply strictly to this frozen benchmark.
- **Statistical Significance:** Paired fact-unit comparisons demonstrate a consistent advantage across all 4 Indic languages, but broad asymptotic claims of universal performance across all Indian courts cannot be asserted without scaling to hundreds of cases.

---

## 18. Architecture Decision

### **OFFICIAL VERDICT:** `ADOPT_ENGLISH_FIRST`

System D satisfies all 7 pre-established adoption criteria:
1. **Critical Fact Advantage:** $+19.1\%$ gain over Direct Indic Qwen3.
2. **Reproducibility:** Recomputes deterministically from raw fact-level rows.
3. **Denominator Parity:** Fair comparison on identical 152 Indic critical fact-units.
4. **Safety:** Zero hallucinations or contradictions introduced ($0.0\%$).
5. **Entity Integrity:** $100\%$ legal entity survival with terminology protection.
6. **Causal Attribution:** Eliminates direct multilingual generation collapse (R3).
7. **Cross-Language Consistency:** Outperforms direct Indic in Tamil ($26.3\%$ vs $2.6\%$), Kannada ($26.3\%$ vs $2.6\%$), Marathi ($26.3\%$ vs $5.3\%$), and Hindi ($26.3\%$ vs $18.4\%$).

---

## 19. What Phase 6 Actually Proves

1. Direct generation of Indic legal summaries using 4B-parameter LLMs suffers from catastrophic fact omission (>90%).
2. Intermediate English summarization followed by neural translation preserves substantially more legal facts.
3. Legal entity protection is mandatory: without it, raw translation degrades 38% of legal entities.

---

## 20. What Phase 6 Does NOT Prove

1. It does not prove that English-first translation preserves *all* legal facts (26.3% critical preservation leaves 73.7% omission).
2. It does not prove translation quality for specialized appellate benches (High Courts / Supreme Court) with archaic legal syntax.
3. It does not prove that larger (e.g. 70B+) direct multilingual models would suffer the same collapse.

---

## 21. Recommended Next Step

**Phase 7: Context-Expanded Translation & Reranking.**
Investigate expanding translation context windows, few-shot terminology dictionaries, and hybrid translation reranking to bridge the remaining gap between English preservation (81.6%) and Indic preservation (26.3%).

---

## 22. Artifact Manifest

All audit artifacts are generated in `phase6_audit/`:
- [authoritative_phase6_results.csv](file:///home/tharan/Seeds/vidhik/phase6_audit/authoritative_phase6_results.csv)
- [reconciliation_table.csv](file:///home/tharan/Seeds/vidhik/phase6_audit/reconciliation_table.csv)
- [metric_lineage.md](file:///home/tharan/Seeds/vidhik/phase6_audit/metric_lineage.md)
- [artifact_inventory.md](file:///home/tharan/Seeds/vidhik/phase6_audit/artifact_inventory.md)
- [source_inventory.csv](file:///home/tharan/Seeds/vidhik/phase6_audit/source_inventory.csv)
- [denominator_audit.csv](file:///home/tharan/Seeds/vidhik/phase6_audit/denominator_audit.csv)
- [system_row_counts.csv](file:///home/tharan/Seeds/vidhik/phase6_audit/system_row_counts.csv)
- [language_row_counts.csv](file:///home/tharan/Seeds/vidhik/phase6_audit/language_row_counts.csv)
- [document_row_counts.csv](file:///home/tharan/Seeds/vidhik/phase6_audit/document_row_counts.csv)
- [audit_log.md](file:///home/tharan/Seeds/vidhik/phase6_audit/audit_log.md)

---

## 23. Test Results

Comprehensive verification executed in `phase6_audit/tests/test_phase6_audit.py` (14/14 tests passing).
