# Vidhik Phase 5 — Comprehensive Error Analysis & Failure Attribution
**Document Ref:** VIDHIK-P5-ERR-V1  
**Target Architecture:** Qwen3-4B-Instruct | Condition C | 450 Max Tokens  
**Corpus Population:** 161 District Court Documents (324 Pages)  
**Evaluation Scope:** 805 Runs (45 Evaluated Benchmarks, 760 Accounted Pool Runs)  
**Date:** October 2026  

---

## 1. Executive Summary

Phase 5 of the Vidhik project conducts an exhaustive, multi-layered error audit of multilingual legal fact preservation across Indian District Court documents. Every identified factual gap or discrepancy is attributed to an explicit stage in the legal intelligence pipeline:
- **`R1_RETRIEVAL_FAILURE`**: Fact present in the verified source document but omitted by the Phase-3 RRF fusion retrieval system.
- **`R2_GENERATION_FAILURE`**: Fact retrieved and provided in the context window, but omitted, altered, or hallucinated by the summarization generator in English.
- **`R3_MULTILINGUAL_FAILURE`**: Fact captured in English generation, but omitted, degraded, or distorted during multilingual target language realization (Tamil, Hindi, Kannada, Marathi).
- **`R4_SOURCE_AMBIGUITY`**: Fact inherently ambiguous, contradictory, or illegible in the original court judgment text.
- **`R5_EVALUATOR_DISAGREEMENT`**: Automated evaluator conflict between deterministic regex patterns and neural evaluator audits.

---

## 2. Global Error Attribution Distribution

From the complete attribution dataset (`failure_attribution.parquet` and `evidence_availability_v1.parquet`):

| Failure Stage | Event Count | Percentage of Failures | Primary Root Cause |
|---|:---:|:---:|---|
| **`R1_RETRIEVAL_FAILURE`** | 168 facts | 28.8% of corpus facts | Lexical/semantic BM25+BGE-M3 3-sentence window cutoff |
| **`R2_GENERATION_FAILURE`** | 66 events | 11.3% of summary errors | Information density tradeoff under 450 max_tokens |
| **`R3_MULTILINGUAL_FAILURE`** | 350 events | 59.9% of summary errors | Subword expansion, vocabulary limits, vernacular omissions |
| **`R4_SOURCE_AMBIGUITY`** | 0 events | 0.0% | Provenance verification removed ambiguous cases |
| **`R5_EVALUATOR_DISAGREEMENT`** | 3 events | 0.5% | Minor threshold differences between token overlap and regex |

```text
CORPUS FACTS (1,089)
  ├── RETRIEVAL AVAILABLE: 921 (84.6%)
  └── RETRIEVAL MISSING:   168 (15.4%) ──► [R1_RETRIEVAL_FAILURE]

BENCHMARK SUMMARY FACT-ALIGNMENT FAILURES (416 Events)
  ├── MULTILINGUAL REALIZATION: 350 (84.1%) ──► [R3_MULTILINGUAL_FAILURE]
  └── GENERATION OMISSION:       66 (15.9%) ──► [R2_GENERATION_FAILURE]
```

---

## 3. Detailed Taxonomy Breakdown (E1–E14)

| Error Code | Taxonomy Name | Occurrences | Severity | Primary Responsible Stage | Description & Impact |
|---|---|:---:|:---:|:---:|---|
| **E1** | Unsupported factual claim | 18 | Medium | `R2` / `R3` | Model introduces procedural inferences not directly stated in evidence. |
| **E2** | Contradicted factual claim | 4 | Severe | `R2` / `R3` | Model states an outcome contrary to evidence (e.g. minor maintenance terms). |
| **E3** | Wrong date | 12 | Medium | `R2` | Misattributes hearing date for judgment delivery date. |
| **E4** | Wrong amount | 2 | High | `R2` | Numeric alteration during currency generation. |
| **E5** | Wrong case number | 0 | Severe | `R2` | Zero hallucinations; case numbers are omitted rather than falsified. |
| **E6** | Wrong party | 3 | Severe | `R3` | Inversion of petitioner/respondent roles in vernacular translation. |
| **E7** | Wrong statutory section | 2 | Severe | `R2` / `R3` | Section number transposed (e.g. citing general IPC instead of specific act). |
| **E8** | Wrong procedural action | 8 | Medium | `R2` | Describing a criminal revision as an original trial. |
| **E9** | Wrong judicial finding | 5 | High | `R2` | Summarizing respondent's argument as a judicial finding. |
| **E10** | Wrong disposition | 0 | Critical | — | **Zero critical disposition errors** on tested judgments. |
| **E11** | Wrong relief | 4 | High | `R2` | Omitting quantum of interim relief or interest rate. |
| **E12** | Critical omission | 416 | High | `R1` / `R2` / `R3` | Omission of party names, case numbers, and procedural milestones. |
| **E13** | Translation meaning change | 14 | Severe | `R3` | Vernacular legal term drifts (e.g., using "குற்றம்" for "வழக்கு"). |
| **E14** | Unsupported inference | 9 | Low | `R2` | Extrapolating that parties complied with prior bail conditions. |

---

## 4. Deep-Dive: Retrieval vs. Generation vs. Multilingual Failures

### 4.1 Retrieval Availability Failures (`R1_RETRIEVAL_FAILURE`)
Across the 161 frozen documents, **168 out of 1,089 canonical facts (15.4%)** were absent from the retrieved Phase-3 evidence:
- **Cause:** Phase 3 used a frozen 3-sentence contextual window with BM25 + BGE-M3 RRF fusion. While effective for dispositive paragraphs, standard District Court judgments often spread preliminary facts (the trial court case number, magistrate name, original complaint date) across the header and footer on Page 1, which dense retrieval ranked lower than the operational final orders on Page 2 or Page 3.
- **Methodological Distinction:** Under Section 4.3, these omissions are strictly tagged as **`R1_RETRIEVAL_FAILURE`**. The summarizer is never penalized for facts it was never given.

### 4.2 Generation Failures (`R2_GENERATION_FAILURE`)
In English generation under Condition C:
- English preserved 66.7% of dispositions, 77.8% of statutory sections, and 88.9% of monetary amounts.
- However, English omitted 35.1% of available critical facts. The primary driver was the **450 max_tokens limit**: when constrained to concise prose, Qwen3 prioritized the substantive legal reasoning over repeating the formal case caption (`C.C. No. 248/2019`) and full names of four co-accused.

### 4.3 Multilingual Realization Failures (`R3_MULTILINGUAL_FAILURE`)
Multilingual realization proved to be the most vulnerable stage in the pipeline:
- **Token Inflation:** Indic scripts require 2.5× to 3.5× more byte-pair tokens per word than English. Under a fixed 450-token ceiling, an Indic summary can express only 80–120 words compared to 250–300 words in English.
- **Omission Cascades:** To reach the dispositive sentence before the token limit is reached, the model aggressively pruned named entities, statutory clauses, and procedural context in Tamil, Hindi, Kannada, and Marathi.
- **Language Degradation Gap:** While English critical fact omission was 35.1%, omission soared to **95.7% in Tamil**, **95.7% in Hindi**, **84.6% in Kannada**, and **97.8% in Marathi**.

---

## 5. Concrete Failure Case Studies

### Case Study 1: Statutory Number Preservation vs. Omission
- **Document:** `DC_000001` (Negotiable Instruments Act dispute)
- **Canonical Fact:** `STATUTORY_SECTION`: "Section 138"
- **Retrieved Evidence:** Contains `"offence under Section 138 of N.I. Act"`.
- **English Summary (`P5_RUN_DC_000001_EN`):** Preserved — `"convicted under Section 138 of the Negotiable Instruments Act"`.
- **Tamil Summary (`P5_RUN_DC_000001_TA`):** Preserved — `"செக் மோசடி வழக்கு (பிரிவு 138)"`.
- **Kannada Summary (`P5_RUN_DC_000001_KN`):** Degraded — Mentions cheque dishonour but omits the explicit number "138", triggering **E12** and **R3_MULTILINGUAL_FAILURE**.

### Case Study 2: Party Name Dropping Under Token Budget
- **Document:** `DC_000002` (Criminal Revision)
- **Canonical Fact:** `PARTIES`: "Murugan vs State"
- **Retrieved Evidence:** Header contains `"Murugan ... Petitioner / Accused"`.
- **English Summary:** Preserved as `"The revision petitioner Murugan challenged the order..."`.
- **Marathi Summary:** Rendered as `"अर्जदाराने दाखल केलेला पुनरिक्षण अर्ज..."` ("The applicant filed revision application...").
- **Attribution:** The proper name "Murugan" is substituted with the generic noun "applicant". Classified as **E12 (Critical Fact Omission)** under **R3_MULTILINGUAL_FAILURE**.

---

## 6. Recommendations for Phase 6

1. **Dynamic Language-Aware Token Budgets:** Allow Indic languages 800–1000 tokens to achieve parity with English information density.
2. **Explicit Fact-Preservation Prompt Slots:** Condition C should be augmented in Phase 6 with dedicated entity placeholders (`[Case Number]`, `[Parties]`, `[Statutes]`) to prevent vernacular realization pruning.
3. **Hybrid Header Injection in Retrieval:** Add a mandatory deterministic header-extraction pass to guarantee Page 1 metadata is never lost in RRF dense retrieval.
