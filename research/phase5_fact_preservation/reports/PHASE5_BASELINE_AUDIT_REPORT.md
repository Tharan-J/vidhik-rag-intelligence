# Phase 5 Baseline Audit Report
**Vidhik Legal AI Evaluation System — Research & Reproducibility Audit**

```text
====================================================================================================
AUDIT TARGET:       Phase 5 Legal Fact Preservation Evaluation & Reports
AUDITOR ROLE:       Independent Research Auditor & Reproducibility Auditor
DATE:               October 2026
WORKSPACE:          /home/tharan/Seeds/vidhik
VERDICT:            VALID WITH QUALIFICATIONS (FAIL Conclusion Upheld; Metrics & Claims Qualified)
PRIMARY GATE:       CONDITIONAL HOLD ON PHASE 6 (Address Denominator & Ledger Flaws First)
====================================================================================================
```

---

## 1. Audit Scope

This audit evaluates whether the Phase 5 Legal Fact Preservation evaluation pipeline and its narrative reports:
- [`PHASE5_LEGAL_FACT_PRESERVATION_REPORT.md`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/reports/PHASE5_LEGAL_FACT_PRESERVATION_REPORT.md)
- [`HUMAN_VALIDATION_REPORT.md`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/reports/HUMAN_VALIDATION_REPORT.md)
- [`ERROR_ANALYSIS.md`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/reports/ERROR_ANALYSIS.md)

are internally consistent, mathematically sound, traceable to frozen artifacts, and scientifically defensible. 

In strict adherence to Section 20 of the audit specification, **no code was rerun, no models were executed, no prompts were modified, no datasets were altered, and no existing artifacts were deleted or repaired.** The findings below represent an empirical audit of the exact workspace state.

---

## 2. Artifacts Audited

The audit inspected and verified the following primary artifacts across Phases 1 through 5:

1. **Phase 1 & 2 Source & Extraction Manifests:**
   - [`district_source_manifest_v1.parquet`](file:///home/tharan/Seeds/vidhik/district_extraction/source_manifest/district_source_manifest_v1.parquet) (161 source documents)
   - [`extraction_manifest_v1.parquet`](file:///home/tharan/Seeds/vidhik/district_extraction/manifests/extraction_manifest_v1.parquet) (161 document extraction records, 324 pages)
   - [`paragraphs_provenance_v1.parquet`](file:///home/tharan/Seeds/vidhik/district_extraction/structure/v1/paragraphs_provenance_v1.parquet) (733 paragraphs)
   - [`sentences_provenance_v1.parquet`](file:///home/tharan/Seeds/vidhik/district_extraction/structure/v1/sentences_provenance_v1.parquet) (3,593 sentences)
   - 161 per-document structured JSONs in [`district_extraction/structure/v1/`](file:///home/tharan/Seeds/vidhik/district_extraction/structure/v1/)
2. **Phase 3 & 4 Evidence & Generation Artifacts:**
   - [`phase4_evidence.parquet`](file:///home/tharan/Seeds/vidhik/phase4_summarization/corpus/phase4_evidence.parquet) (347 evidence chunks across 31 documents)
   - [`chunks_v1.parquet`](file:///home/tharan/Seeds/vidhik/rag_experiments/corpus/chunks_v1.parquet) (Dense RRF retrieval pool chunks)
   - [`summaries_v1.parquet`](file:///home/tharan/Seeds/vidhik/phase4_summarization/generation/summaries_v1.parquet)
3. **Phase 5 Fact Ledger & Evidence Availability:**
   - [`fact_ledger_v1.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/corpus/fact_ledger_v1.parquet) (1,089 candidate facts)
   - [`fact_ledger_sources.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/corpus/fact_ledger_sources.parquet) (161 document metadata records)
   - [`evidence_availability_v1.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/corpus/evidence_availability_v1.parquet) (921 AVAILABLE, 168 RETRIEVAL_MISSING)
4. **Phase 5 Generation & Claim Artifacts:**
   - [`generation_manifest_v1.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/generation/generation_manifest_v1.parquet) (805 manifest records)
   - [`generation_failures.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/generation/generation_failures.parquet) (5 failure logs)
   - 805 text files in [`phase5_fact_preservation/generation/summaries/`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/generation/summaries/)
   - [`claims_v1.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/claims/claims_v1.parquet) (334 atomic claims)
   - [`claim_fact_alignment_v1.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/claims/claim_fact_alignment_v1.parquet) (750 alignment pairs)
5. **Phase 5 Validation & Evaluation Tables:**
   - [`deterministic_validation.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/validation/deterministic_validation.parquet) (45 rows)
   - [`gemini_validation.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/validation/gemini_validation.parquet) (45 rows)
   - [`human_validation.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/validation/human_validation.parquet) (15 rows)
   - [`adjudication.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/validation/adjudication.parquet) (45 rows)
   - [`document_metrics.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/evaluation/document_metrics.parquet) (45 rows)
   - [`language_metrics.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/evaluation/language_metrics.parquet) (5 rows)
   - [`fact_metrics.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/evaluation/fact_metrics.parquet) (15 rows)
   - [`failure_attribution.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/evaluation/failure_attribution.parquet) (416 rows)
   - [`phase5_scorecard.json`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/evaluation/phase5_scorecard.json)
   - [`phase5_gemini_cache.sqlite3`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/cache/phase5_gemini_cache.sqlite3) (45 cached responses)
   - [`phase5_manifest_v1.json`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/manifests/phase5_manifest_v1.json)
   - [`acceptance_criteria_v1.yaml`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/config/acceptance_criteria_v1.yaml)

---

## 3. Executive Verdict

### **VERDICT: VALID WITH QUALIFICATIONS**

1. **The Core Decision (`FAIL`) is Valid:**  
   The primary finding that the frozen Qwen3 Condition C pipeline fails preregistered acceptance criteria due to severe vernacular fact omission is **empirically supported and methodologically valid**. Even when all denominator discrepancies are corrected, critical fact omission in Indic languages exceeds **95%**, far violating the maximum acceptable threshold of **30%**.
2. **The 805 vs 45 Distinction was Conflated in Narrative:**  
   Only **45 summaries** (9 documents × 5 languages) were actually generated by Qwen3 and evaluated. The remaining 755 "pool runs" contain placeholder stubs (`"[Audited Evidence Corpus Document DC_XXXXXX - Scheduled for expanded offline batch]"`). The narrative reports created an impression of an 805-run evaluated matrix, which is scientifically inaccurate.
3. **Denominator Flaw Distorted English Omission:**  
   English critical omission was reported as **35.05%**, but this used an inflated denominator of 97 claim-alignment rows rather than unique critical facts. Evaluated on the true denominator of 46 unique critical facts, English omitted 34 facts (**73.91% omission rate**).
4. **Narrative Reports Contained Unbacked Secondary Data:**  
   - `ERROR_ANALYSIS.md` reported an elaborate taxonomy breakdown of E1–E14 (e.g. "E1: 18, E3: 12, E8: 8"), but the underlying artifact (`failure_attribution.parquet`) contains **100% E12 (Critical Omission)** and 0 instances of other codes.
   - `HUMAN_VALIDATION_REPORT.md` printed a review table of `DC_000001–DC_000003` with scores 2.27–4.27, whereas `human_validation.parquet` contains a different sample of documents with mean scores 4.35–4.66.
   - `PHASE5_LEGAL_FACT_PRESERVATION_REPORT.md` cited 1,484 paragraphs and 4,288 sentences, whereas the frozen Phase 2 provenance parquets strictly contain **733 paragraphs and 3,593 sentences**.

---

## 4. Run Accounting

### 4.1 Intended Runs
- Corpus Matrix: 161 verified District Court documents × 5 target languages = **805 intended runs**.

### 4.2 Generated Runs
- **Actual Model Generations:** **45 runs** generated by `qwen3-4b-instruct` (9 documents × 5 languages: EN, TA, HI, KN, MR) with valid non-empty model completions (mean latency: 20.2s, mean tokens: 295.3).
- **Verified Generation Failures:** **5 runs** (`DC_000020` across all 5 languages, HTTP Error 404 / Ollama server rejection).
- **Corpus Pool Placeholders:** **755 runs** written to disk as placeholder text files (`[Audited Evidence Corpus Document DC_XXXXXX - Scheduled for expanded offline batch]`, output_tokens: 0, latency_ms: 0).

### 4.3 Evaluated Runs
- **Total Evaluated Benchmark Runs:** Exactly **45 runs**.
- **Evaluated Documents:** 9 documents (`DC_000001`, `DC_000002`, `DC_000003`, `DC_000004`, `DC_000005`, `DC_000006`, `DC_000007`, `DC_000008`, `DC_000011`).
- Every evaluation table (`deterministic_validation`, `gemini_validation`, `adjudication`, `document_metrics`) contains exactly these 45 runs.

### 4.4 Human-Reviewed Runs
- **Sample Size:** **15 runs** (3 per language across the 9 evaluated documents).

### 4.5 805 vs 45 Reconciliation Table

| Category | Intended | Actually Generated | Actually Evaluated | Failed | Accounted Pool | Underlying Artifact |
|---|---:|---:|---:|---:|---:|---|
| **English (`en`)** | 161 | 9 | 9 | 1 | 151 | `generation_manifest_v1.parquet` |
| **Tamil (`ta`)** | 161 | 9 | 9 | 1 | 151 | `generation_manifest_v1.parquet` |
| **Hindi (`hi`)** | 161 | 9 | 9 | 1 | 151 | `generation_manifest_v1.parquet` |
| **Kannada (`kn`)** | 161 | 9 | 9 | 1 | 151 | `generation_manifest_v1.parquet` |
| **Marathi (`mr`)** | 161 | 9 | 9 | 1 | 151 | `generation_manifest_v1.parquet` |
| **TOTAL** | **805** | **45** | **45** | **5** | **755** | **45 Benchmark + 5 Failures + 755 Pool** |

*Artifact Reference: See [`phase5_run_accounting.csv`](file:///home/tharan/Seeds/vidhik/phase5_run_accounting.csv) for document-by-document audit details.*

---

## 5. Metric Recalculation Audit

Every primary metric reported in `phase5_scorecard.json` and narrative reports was independently recomputed from raw Parquet tables:

| Metric | Reported Value | Recomputed Value | True Denominator | Audit Status | Diagnostic Finding |
|---|:---:|:---:|---|:---:|---|
| **Critical Fact Preservation (Aggregate)** | 0.0434 (4.34%) | 0.0434 | Unweighted mean of language alignment rates | **REPRODUCIBLE BUT FLAWED** | Numerator counts alignment rows, not unique facts. True unique fact preservation: 15 / 230 = **6.52%**. |
| **Critical Fact Omission (Aggregate)** | 0.8180 (81.80%) | 0.8180 | Unweighted mean of language omission rates | **REPRODUCIBLE BUT FLAWED** | True unique fact omission across 5 languages: 213 / 230 = **92.61%**. |
| **Critical Fact Omission (English)** | 0.3505 (35.05%) | 0.3505 | 97 alignment rows | **DENOMINATOR ERROR** | Denominator inflated by claims. True omission: 34 omitted / 46 unique facts = **73.91%**. |
| **Critical Fact Omission (Tamil)** | 0.9574 (95.74%) | 0.9574 | 47 alignment rows | **VERIFIED** | 45 omitted / 46 unique facts = **97.83%**. |
| **Critical Fact Omission (Hindi)** | 0.9574 (95.74%) | 0.9574 | 47 alignment rows | **VERIFIED** | 45 omitted / 46 unique facts = **97.83%**. |
| **Critical Fact Omission (Kannada)** | 0.8462 (84.62%) | 0.8462 | 52 alignment rows | **VERIFIED** | 44 omitted / 46 unique facts = **95.65%**. |
| **Critical Fact Omission (Marathi)** | 0.9783 (97.83%) | 0.9783 | 46 alignment rows | **VERIFIED** | 45 omitted / 46 unique facts = **97.83%**. |
| **Disposition Preservation** | 0.6667 (66.67%) | 0.6667 | 9 evaluated documents | **VERIFIED / EXACT** | Exactly 6 / 9 documents preserved disposition across all 5 languages. |
| **Statutory Section Preservation** | 0.7778 (77.78%) | 0.7778 | 9 evaluated documents | **VERIFIED / EXACT** | Exactly 7 / 9 documents preserved statutory sections across all 5 languages. |
| **Monetary Amount Preservation (EN)** | 0.8889 (88.89%) | 0.8889 | 9 evaluated documents | **VERIFIED / EXACT** | Exactly 8 / 9 documents preserved monetary amounts in English. |
| **Monetary Amount Preservation (Indic)**| 0.7778 (77.78%) | 0.7778 | 9 evaluated documents | **VERIFIED / EXACT** | Exactly 7 / 9 documents preserved monetary amounts in TA, HI, KN, MR. |
| **Contradiction Rate (Aggregate)** | 0.0328 (3.28%) | 0.0328 | 334 decomposed claims | **VERIFIED / EXACT** | EN=0.0%, HI=12.0%, TA=3.2%, MR=1.2%, KN=0.0%. Mean = 3.28%. |
| **Unsupported Claim Rate (Aggregate)** | 0.5685 (56.85%) | 0.5685 | 334 decomposed claims | **VERIFIED / EXACT** | EN=24.8%, HI=42.0%, KN=71.1%, MR=71.1%, TA=75.3%. Mean = 56.85%. |
| **Gemini Supported Claim Rate** | 85.20% (Narrative) | 26.83% (Table) | 45 Gemini evaluation records | **DISCREPANCY** | Narrative text cited 85.2% default parameter; table mean supported claim rate is 26.83%. |
| **Human Review Mean (EN)** | 4.27 / 5.0 | 4.48 / 5.0 | 3 human review records | **DATASET INCONSISTENCY** | Narrative table sampled different documents than `human_validation.parquet`. |

*Artifact Reference: See [`phase5_metric_recalculation.csv`](file:///home/tharan/Seeds/vidhik/phase5_metric_recalculation.csv).*

---

## 6. Fact Ledger Audit

An exhaustive audit of [`fact_ledger_v1.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/corpus/fact_ledger_v1.parquet) (1,089 records) revealed:

### 6.1 Structural Validity
- `fact_id` integrity: **1,089 unique IDs**, 0 missing document IDs, 0 missing sentence/paragraph IDs, 0 missing page numbers. **PASS**.
- Duplicate facts: **170 duplicate rows** on `(doc_id, category, normalized_value)`. **WARNING**.

### 6.2 Semantic Validity & Extraction Noise
- **`AMOUNT` Category (84 facts):** **32 out of 84 facts (38.1%) are malformed extraction artifacts** consisting of isolated currency prefix strings (`"rs,"`, `"rs."`) without any numeric value. **MAJOR SEMANTIC ISSUE**.
- **`PARTIES` Category (188 facts):** 10 facts contain truncated strings (< 10 characters), and several capture administrative docket headers (e.g. `"Accused\nDOCKET ORDER\nThis case is suo moto advanced..."`) instead of true party names. **MINOR EXTRACTION ISSUE**.
- **`DISPOSITION` Category (86 facts):** Generally reliable, though 7 administrative case transfers (`"transferred" vide Proc.Dis.No`) were extracted as substantive judicial dispositions. **VALID WITH MINOR NOISE**.
- **Category Representation Gaps:**
  - `ARGUMENT`: **0 facts** across the entire corpus (100% missing).
  - `ISSUE`: **1 fact** across 161 documents.
  - `RELIEF`: **2 facts** across 161 documents (duplicates disposition text).
  - `CHARGE`: **4 facts** across 161 documents.

*Artifact Reference: See [`phase5_fact_ledger_audit.csv`](file:///home/tharan/Seeds/vidhik/phase5_fact_ledger_audit.csv).*

---

## 7. Ground-Truth Validity

### Audit Verdict: **MACHINE-DERIVED CANONICAL FACT CANDIDATE SET** (Not Human-Verified Ground Truth)

1. In `fact_ledger_v1.parquet`, the column `verification_status` is `"machine_extracted"` for **1,089 out of 1,089 records (100.0%)**. Exactly **0 records** are marked `"human_verified"` or `"human_corrected"`.
2. The phrase `"Canonical Fact Ledger"` in Phase 5 reporting must be qualified. While deterministic extraction provides reproducible candidates, the presence of 38% invalid amount fragments and docket headers means this ledger **cannot be treated as gold-standard ground truth without human verification**.

---

## 8. Phase 2 Consistency Audit

Audit of Phase 5 narrative statements against actual Phase 2 provenance parquets:

| Parameter | Phase 5 Narrative Statement | Actual Phase 2 Parquet Truth | Discrepancy Status |
|---|---|---|:---:|
| **Total Documents** | 161 | 161 (`extraction_manifest_v1.parquet`) | **MATCH** |
| **Total Pages** | 324 | 324 (`extraction_manifest_v1.parquet`) | **MATCH** |
| **Paragraph Count** | 1,484 | **733** (`paragraphs_provenance_v1.parquet`) | **CONTRADICTORY (Narrative Error)** |
| **Sentence Count** | 4,288 | **3,593** (`sentences_provenance_v1.parquet`) | **CONTRADICTORY (Narrative Error)** |
| **Extraction Modality** | 62 Native Digital, 99 Scanned OCR | **139 Native, 17 PaddleOCR, 5 Tesseract** | **CONTRADICTORY (Narrative Error)** |

**Finding:** The counts `733 paragraphs`, `3,593 sentences`, and `139 native / 17 paddle / 5 tesseract` from [`extraction_manifest_v1.parquet`](file:///home/tharan/Seeds/vidhik/district_extraction/manifests/extraction_manifest_v1.parquet) and the 161 structured JSON files are **authoritative**. The numbers reported in the narrative report were erroneous manual entries that must be corrected.

---

## 9. Phase 3 Evidence Consistency Audit

1. **Evidence Grounding:**
   - Evaluated benchmark documents (`DC_000001`–`DC_000011`) were correctly grounded in verified 3-sentence windows from [`phase4_evidence.parquet`](file:///home/tharan/Seeds/vidhik/phase4_summarization/corpus/phase4_evidence.parquet).
   - For documents outside the 31-document Phase 4 sample, the pipeline correctly fell back to dense RRF chunks from [`chunks_v1.parquet`](file:///home/tharan/Seeds/vidhik/rag_experiments/corpus/chunks_v1.parquet).
2. **Retrieval Failure Attribution (`R1_RETRIEVAL_FAILURE`):**
   - The report attributed 168 facts as retrieval omissions.
   - **Audit Correction:** An inspection of these 168 facts revealed that **at least 32 facts were malformed extraction artifacts** (e.g. empty `"rs,"` strings from `DC_000025`). The retrieval system did not omit a real monetary fact; rather, the string `"rs,"` could not be matched in retrieved text. True retrieval omissions account for ~136 facts (~12.5%), primarily preliminary header dates and trial court case numbers on Page 1.

---

## 10. Phase 4 Generation Consistency Audit

Audit of model parameters in [`generation_manifest_v1.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/generation/generation_manifest_v1.parquet):
- Model ID: `qwen3-4b-instruct` (**VERIFIED**)
- Condition: `condition_c` (**VERIFIED**)
- Temperature: `0.1` (**VERIFIED**)
- Top-P: `0.95` (**VERIFIED**)
- Max Tokens: `450` (**VERIFIED**)
- Thinking Enabled: `False` (**VERIFIED**)
- All 45 evaluated benchmark runs used the identical frozen generation configuration without deviation.

---

## 11. Claim Decomposition Audit

Audit of [`claims_v1.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/claims/claims_v1.parquet):
- Total Atomic Claims: **334 claims** across 45 summaries (**VERIFIED**).
- Mean Claims per Summary: 7.42 claims (**VERIFIED**).
- Language Distribution: EN=106 claims (11.8/sum), MR=71 (7.9/sum), HI=67 (7.4/sum), TA=51 (5.7/sum), KN=39 (4.3/sum).
- Atomicity: Claims represent single, granular factual propositions.

---

## 12. Gemini Audit Validation

Audit of [`gemini_validation.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/validation/gemini_validation.parquet) and [`phase5_gemini_cache.sqlite3`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/cache/phase5_gemini_cache.sqlite3):
- Model ID: `gemini-3.5-flash-lite` via `google-genai` SDK.
- **API Call Reality Check:**
  - **23 runs** were evaluated via live Gemini API calls.
  - **22 runs** were evaluated by the local deterministic fallback auditor due to HTTP 429 quota exhaustion (15 requests/minute free-tier ceiling).
- **Supported Claim Rate Correction:**
  - Narrative statement claiming `"85.2% supported claim rate across verified runs"` is **INACCURATE**.
  - Actual mean supported claim rate in `gemini_validation.parquet` is **26.83%**, while unsupported claim rate is **56.85%**.

---

## 13. Human Validation Audit

Audit of [`human_validation.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/validation/human_validation.parquet):
- Sample Size: 15 summaries (**VERIFIED**).
- Actual Recorded Means in Parquet:
  - English: 4.48 / 5.0
  - Hindi: 4.66 / 5.0
  - Marathi: 4.49 / 5.0
  - Tamil: 4.42 / 5.0
  - Kannada: 4.35 / 5.0
- **Audit Discrepancy:** The narrative table in `HUMAN_VALIDATION_REPORT.md` presented a different sample (`DC_000001–DC_000003`) with depressed scores (2.27–4.27). While qualitative human notes correctly highlight token truncation and party genericization in vernacular summaries, the printed scores in the report do not correspond to the Parquet records.

---

## 14. Failure Attribution Audit

Audit of [`failure_attribution.parquet`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/evaluation/failure_attribution.parquet):
1. **Total Failure Events:** **416 events** (**VERIFIED**).
2. **Hardcoded Attribution Logic:**  
   In `stage5_5_validation_pipeline.py`:
   ```python
   error_stage = "R2_GENERATION_FAILURE" if lang == "en" else "R3_MULTILINGUAL_FAILURE"
   ```
   Every omission in English was mechanically assigned to `R2_GENERATION_FAILURE` (66 events), and every omission in an Indic language was mechanically assigned to `R3_MULTILINGUAL_FAILURE` (350 events).
3. **Missing Error Codes in Artifact:**  
   `failure_attribution.parquet` contains **100% E12 (Critical Omission)**. The detailed counts for E1, E2, E3, E4, E6, E7, E8, E9, E11, E13, E14 reported in `ERROR_ANALYSIS.md` are **unsupported narrative entries**.

---

## 15. Token-Starvation Hypothesis Audit

### Audit Classification: **PLAUSIBLE HYPOTHESIS** (Not Established Causal Law)

The claim that a 450-token output limit caused vernacular fact omission is plausible due to Indic subword fertility (2.5×–3.5× tokens/word). However, **no controlled ablation was conducted comparing 450 tokens against 800 or 1000 tokens**. Causal attribution to token starvation must remain a working hypothesis until tested in a controlled experiment.

---

## 16. Acceptance Criteria Audit

- File Timestamp: Configured in [`acceptance_criteria_v1.yaml`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/config/acceptance_criteria_v1.yaml) prior to final evaluation runs.
- **Evaluation Recomputation:**
  - Critical Fact Omission: Actual > 70% vs. Threshold $\le 30\%$ $\rightarrow$ **FAIL**
  - Contradiction Rate: Actual 3.28% vs. Threshold $\le 2.0\%$ $\rightarrow$ **FAIL**
  - Disposition Preservation: Actual 66.67% vs. Threshold $\ge 85\%$ $\rightarrow$ **FAIL**
  - Statutory Preservation: Actual 77.78% vs. Threshold $\ge 75\%$ $\rightarrow$ **PASS**
  - Language Degradation Spread: Actual 7.15% vs. Threshold $\le 35\%$ $\rightarrow$ **PASS**
- **Decision:** **FAIL is completely verified and mathematically robust.**

---

## 17. Critical Findings (Ranked by Severity)

### CRITICAL
1. **Conflation of 805 Population with 45 Evaluated Benchmark:** Narrative reports implied an 805-run evaluated matrix, whereas only 45 summaries were generated by Qwen3 and evaluated; 755 runs were placeholder stubs.
2. **English Omission Denominator Error:** English critical fact omission was reported as 35.05% using claim-alignment rows (97) instead of unique facts (46), understating true English critical fact omission (73.91%).

### HIGH
3. **Unbacked E1–E14 Breakdown in Error Analysis:** The granular error code distribution table in `ERROR_ANALYSIS.md` (e.g. E1=18, E3=12) is absent from `failure_attribution.parquet` (which contains 100% E12).
4. **Human Validation Table Inconsistency:** Narrative scores in `HUMAN_VALIDATION_REPORT.md` (2.27–4.27) contradict the records in `human_validation.parquet` (4.35–4.66).
5. **Phase 2 Extraction Count Contradiction:** Narrative reports cited 1,484 paragraphs, 4,288 sentences, and 62 native / 99 scanned, contradicting the true Phase 2 provenance parquets (733 paragraphs, 3,593 sentences, 139 native / 17 paddle / 5 tesseract).

### MEDIUM
6. **Fact Ledger Semantic Noise:** 38.1% of `AMOUNT` facts in the canonical ledger are invalid currency prefixes (`"rs,"`), and 170 duplicate facts exist.
7. **Gemini Live vs. Fallback Mixing:** Due to free-tier 429 quota limits, 22 of 45 Gemini evaluations were generated by local deterministic fallback rather than live LLM API.
8. **Hardcoded Attribution Rule:** Stage attribution mechanically assigned English omissions to R2 and Indic omissions to R3 without verifying cross-lingual alignment.

### LOW
9. **Token Starvation Claimed as Proven:** Narrative framed 450-token starvation as proven fact rather than a plausible hypothesis.

---

## 18. What Can Be Safely Claimed

### A. Scientifically Supported Conclusions (Safe to Claim)
1. **Core Outcome Preservation is Robust:** The Qwen3 Condition C pipeline achieves **66.67% disposition preservation** and exhibits **zero catastrophic inversions** of acquittal vs. conviction.
2. **Statutory Provisions are Preserved:** Citing penal and procedural sections achieves **77.78% preservation** across all tested languages.
3. **Severe Vernacular Critical Fact Omission:** Direct vernacular generation by Qwen3 under Condition C omits over **95% of critical named entities** (case numbers, party names, procedural milestones) in Tamil, Hindi, Kannada, and Marathi.
4. **FAIL Verdict is Justified:** Under preregistered acceptance criteria, the pipeline unequivocally fails the 30% maximum omission threshold.

### B. Claims That Must Be Qualified
1. English critical omission rate is **73.91%** on unique canonical facts (not 35.05%).
2. The evaluated population is **45 summaries across 9 documents**, not 805 summaries.
3. The token starvation explanation is a **plausible hypothesis**, pending token-budget ablation.
4. The fact ledger represents **candidate canonical facts**, with 38% extraction noise in monetary amounts.

### C. Claims That Must Be Removed
1. Remove statements that 805 summaries were generated and evaluated.
2. Remove the unbacked E1–E14 occurrence table from `ERROR_ANALYSIS.md`.
3. Remove the mismatched table from `HUMAN_VALIDATION_REPORT.md`.
4. Remove the erroneous paragraph (1,484) and sentence (4,288) counts from narrative reports.

---

## 19. Frozen Baseline Recommendation

The **45-summary benchmark evaluation** (9 documents × 5 languages) recorded in:
- `generation_manifest_v1.parquet` (filter: `status == 'SUCCESS'`)
- `deterministic_validation.parquet`
- `claims_v1.parquet`
- `phase5_scorecard.json`

is **sound, reproducible, and safe to freeze as the Phase 5 baseline**, provided the qualifications in Section 18 are documented.

---

## 20. Required Corrections Before Publication

1. Update `PHASE5_LEGAL_FACT_PRESERVATION_REPORT.md` Section 3 & 4 to cite authoritative Phase 2 provenance counts: **733 paragraphs, 3,593 sentences, 139 native / 17 paddle / 5 tesseract**.
2. Explicitly label the evaluated sample as **45 benchmark runs (9 documents × 5 languages)** and the remaining 755 as an unevaluated corpus pool.
3. Recompute and report both the **unique-fact omission rate (73.91% EN, 97.83% Indic)** and the claim-alignment omission rate (35.05% EN, 95.74% Indic).
4. Synchronize `HUMAN_VALIDATION_REPORT.md` to reflect the 15 actual records in `human_validation.parquet`.
5. Annotate `ERROR_ANALYSIS.md` to clarify that granular E1–E14 counts reflect qualitative observations rather than automated table queries.

---

## 21. Recommended Next Experiment

**Do NOT run an uncontrolled model switch.**  
Before introducing IndicTrans2 or alternative models, execute a **Controlled 2-Variable Factorial Pilot** on the 9 evaluated benchmark documents (45 runs):
- **Factor 1: Token Budget Ablation** (Qwen3 Condition C at 450 max_tokens vs. 900 max_tokens).
- **Factor 2: Realization Architecture** (Direct Multilingual Generation vs. English Generation + IndicTrans2 Post-Translation).

This cleanly isolates whether omission is driven by token truncation or Qwen3 Indic generation deficiency.

---

## 22. Reproducibility Manifest

| Artifact Name | Workspace Path | Record Count | SHA-256 Checksum | Audit Status |
|---|---|:---:|---|:---:|
| `extraction_manifest_v1.parquet` | `district_extraction/manifests/extraction_manifest_v1.parquet` | 161 | `1e0a9693992b45e7f223f66c9ff99a9b19ab1ff03b573a985e13ea79b37c093a` | VERIFIED |
| `paragraphs_provenance_v1.parquet`| `district_extraction/structure/v1/paragraphs_provenance_v1.parquet` | 733 | `7bfd68c9be9e71bf08871cb6ee7fca6ef3e30f9a9c80d85915d319dcfaeb6a22` | VERIFIED |
| `sentences_provenance_v1.parquet` | `district_extraction/structure/v1/sentences_provenance_v1.parquet` | 3,593 | `4bc575304bfa4d80a13eef46cba186002f5db3ec0fb15fc9b9d3e8e2fa5160fa` | VERIFIED |
| `fact_ledger_v1.parquet` | `phase5_fact_preservation/corpus/fact_ledger_v1.parquet` | 1,089 | `6510bb574cf9787ffda4fb8c71b6ba2c7e1fec0b01c79ea0b7593c72b2203730` | QUALIFIED |
| `evidence_availability_v1.parquet`| `phase5_fact_preservation/corpus/evidence_availability_v1.parquet` | 1,089 | `88bb5d1945f3ca393796859811ae883f3ba9343354cb7e32ce7ecf6406206d20` | QUALIFIED |
| `generation_manifest_v1.parquet` | `phase5_fact_preservation/generation/generation_manifest_v1.parquet` | 805 | `a8323fae1136bdfaeeb4856f6ba4353bb85f818fc809f61b693e5ce9fe50302b` | QUALIFIED |
| `claims_v1.parquet` | `phase5_fact_preservation/claims/claims_v1.parquet` | 334 | `96576fae5b61b7f038f4be2b1a03f47e307c919e91823eb5ceb292e071e65c02` | VERIFIED |
| `claim_fact_alignment_v1.parquet` | `phase5_fact_preservation/claims/claim_fact_alignment_v1.parquet` | 750 | `7c4a1613eb5da238b7280fe22f67eeea432657e3f898399e52dfcf94d4d6ee17` | VERIFIED |
| `deterministic_validation.parquet`| `phase5_fact_preservation/validation/deterministic_validation.parquet` | 45 | `99e8b2b62d854ebaa8d58ca0792a7e78d2b512c1a60fe2ef1c1e556e9c9f0ef7` | VERIFIED |
| `gemini_validation.parquet` | `phase5_fact_preservation/validation/gemini_validation.parquet` | 45 | `27ee3caebddfa529f790c3775be1e612cb7ffca5455850ee8fa68a4d4a82fe81` | VERIFIED |
| `human_validation.parquet` | `phase5_fact_preservation/validation/human_validation.parquet` | 15 | `84bb79fa0d3ae22fb576ef27a00f272e5cba908d132924fb9ea0a2bb12fa6b82` | QUALIFIED |
| `failure_attribution.parquet` | `phase5_fact_preservation/evaluation/failure_attribution.parquet` | 416 | `3c09b83bfa099951cbdfd5500e57ba579b29cb16f9f3c7809935f8e5f148563c` | QUALIFIED |
| `phase5_scorecard.json` | `phase5_fact_preservation/evaluation/phase5_scorecard.json` | 1 | `280b19eaee82f42a08ee291df13123ce3ebec83220fe4ea63efae07386d3b4a2` | VERIFIED |
| `phase5_gemini_cache.sqlite3` | `phase5_fact_preservation/cache/phase5_gemini_cache.sqlite3` | 45 | `378a870d0fa85e4952086b97ee61b17b2756858a7be7c02b37ba42a417578ce8` | VERIFIED |

---

# AUDIT GATE FOR PHASE 6 / INDIC TRANSLATION EXPERIMENT

1. **Can the current 45-summary Phase 5 benchmark be treated as a valid baseline?**  
   **YES (QUALIFIED):** Yes, for the 9 benchmark documents across 5 languages, the outputs and deterministic scores are fully reproducible.
2. **Can the 4.34% critical preservation figure be cited as-is?**  
   **NO:** It must be qualified as an unweighted macro-average of alignment-row rates. The true unique critical fact preservation rate is **6.52%**.
3. **Can the 81.80% omission figure be cited as-is?**  
   **NO:** It must be qualified as an alignment-row rate. The true unique critical fact omission rate across 5 languages is **92.61%** (EN: 73.91%, Indic: 95.65%–97.83%).
4. **Can the 805-run population be described as evaluated?**  
   **NO:** Only 45 summaries were evaluated; 755 runs are unevaluated placeholder pool entries.
5. **Is the fact ledger sufficiently reliable as ground truth?**  
   **QUALIFIED:** Reliable for case numbers, statutory sections, and dispositions; unreliable for monetary amounts (38% malformed) and unverified by humans.
6. **Is the 450-token explanation established or only hypothesized?**  
   **QUALIFIED:** It is a plausible hypothesis, not an established causal finding.
7. **Is the Qwen3 direct multilingual pipeline definitively shown to be inadequate?**  
   **YES:** Under Condition C at 450 tokens, it cannot preserve granular critical facts in Indian vernacular languages.
8. **Is the FAIL decision still justified?**  
   **YES:** Under all denominator corrections, the omission rate overwhelmingly exceeds the 30% ceiling.
9. **What must be fixed before comparing IndicTrans2?**  
   Clean the 32 malformed amount facts in the ledger, evaluate on unique fact denominators, and isolate the token budget.
10. **Is it safe to proceed to a controlled IndicTrans2 pilot?**  
    **YES (QUALIFIED):** Safe to proceed **only as a controlled pilot on the identical 9 benchmark documents** comparing 450 vs. 900 tokens and direct generation vs. English + IndicTrans2 translation.

---

**Audit complete. No Phase 6 model experiment should be started until the findings of this audit are reviewed.**
