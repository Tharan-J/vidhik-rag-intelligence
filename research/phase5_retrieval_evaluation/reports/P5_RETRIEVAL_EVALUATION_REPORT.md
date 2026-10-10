
# Phase 5.2: Source-Grounded Retrieval Evaluation Report
**Auditing Historical Evidence Sufficiency for the 9-Document Benchmark**

---

## 1. Executive Summary

This report delivers the **Source-Grounded Retrieval Evaluation** for Vidhik Phase 5.2. Following the establishment and certification of the 85-fact Source-Grounded Legal Fact Gold Set, this evaluation audits whether the legal facts established in Source Truth were actually retrieved and supplied to the summarization model in the Phase 4/5 pipeline.

```
============================================================
P5.2 RETRIEVAL EVALUATION SUMMARY AUDIT
============================================================

Total source-grounded gold facts:            85
Critical facts:                              38
Important facts:                             35
Contextual facts:                            12

Retrieved supported:                         47 (55.3%)
Retrieved partial:                            1 ( 1.2%)
Retrieved but insufficient:                   0 ( 0.0%)
Not retrieved (retrieval starvation):        37 (43.5%)
Absent in source:                             0 ( 0.0%)

Overall retrieval recall:                  55.3% (47/85)
Critical fact retrieval recall:            63.2% (24/38)
Substantive judicial outcome recall:        0.0% ( 0/7)

Benchmark documents evaluated:                9
Historical evidence units audited:           36 (4 units/doc)
Evidence hash reconciliation:             100.0% (36/36)

GATE DECISION FOR P5.3:
    REQUIRES_RETRIEVAL_REPAIR
============================================================
```

### Core Empirical Discovery:
The Phase 4 and Phase 5 summarization pipelines operated under an unacknowledged **upstream retrieval starvation defect**. For every document, the retrieval layer supplied only the first 4 contextual windows (`head(4)` from `phase4_evidence.parquet`). Because these windows were ordered by page and paragraph, the model received only header text from Page 1.
- In multi-page judgments (`DC_000006` [5 pages] and `DC_000011` [3 pages]), **0% of the substantive judicial outcomes** (the acquittal verdict under Sec. 248(1) Cr.P.C., committal under Sec. 209(a) Cr.P.C., judicial findings on reasonable doubt, relief of liberty, and custodial jail status) were supplied to the summarizer.
- In 1-page administrative orders (`DC_000001` through `DC_000005`, `07`, `08`), the 4-window truncation cut off after the case caption, dropping the substantive transfer or LPC register entry orders and dates located at the bottom of the page.

Consequently, previous claims of model "hallucination" or "failure to preserve facts" were severely confounded: models were being penalized for failing to preserve facts that had never been supplied in their retrieval context.

---

## 2. Objective

The objective of Phase 5.2 is to determine:
> **"For each of the 85 verified legal facts in the certified Gold Set, was sufficient supporting evidence actually supplied to the Phase 4/5 summarization pipeline?"**

This is an **independent retrieval audit**. It does NOT evaluate generated summary text, does NOT run new LLM inference, does NOT rerun retrievers (BM25 or BGE-M3), and does NOT modify the certified gold facts.

---

## 3. Authoritative Inputs

The evaluation strictly uses frozen, immutable artifacts:

1. **Certified Gold Fact Set**:
   - `phase5_source_grounded_gold/gold_facts.parquet` (85 facts, 100% human-verified, 100% sentence-level provenance).
   - `phase5_source_grounded_gold/benchmark_inventory.csv` (9 benchmark documents).
2. **Authoritative Phase 2 Provenance**:
   - `district_extraction/structure/v1/sentences_provenance_v1.parquet` (3,593 verified sentences).
   - `district_extraction/structure/v1/paragraphs_provenance_v1.parquet` (1,842 verified paragraphs).
   - `district_extraction/source_manifest/district_source_manifest_v1.parquet` (immutable source SHA-256 identities).
3. **Historical Retrieval Evidence**:
   - `phase4_summarization/corpus/phase4_evidence.parquet` (the exact contextual windows generated in Phase 3/4).
   - `phase5_fact_preservation/generation/generation_manifest_v1.parquet` (verifying exact SHA-256 evidence hashes per document).

---

## 4. Benchmark Definition

The evaluation benchmark covers exactly 9 District Court documents that produced the 45 real multilingual summaries across English (`en`), Tamil (`ta`), Hindi (`hi`), Kannada (`kn`), and Marathi (`mr`).

Retrieval evidence is evaluated at the document/evidence level (36 supplied units across 9 documents), rather than duplicating retrieval evaluation across the 5 language summary runs.

---

## 5. Gold Fact Population

The 85 gold facts represent exhaustive legal ground truth across 3 criticality tiers:
- **CRITICAL (38 facts)**: `CASE_NUMBER` (9), `PARTIES` (19), `CHARGE` (3), `DISPOSITION` (3), `BAIL_STATUS` (2), `JUDICIAL_FINDING` (1), `RELIEF` (1).
- **IMPORTANT (35 facts)**: `PROCEDURAL_ACTION` (13), `DATE` (12), `COURT` (9), `AMOUNT` (1).
- **CONTEXTUAL (12 facts)**: `OFFICER` (12).

---

## 6. Retrieval Evidence Definition

In Phase 4 (`stage4_2_generation_ladder.py`) and Phase 5 (`stage5_3_frozen_generation.py`), the evidence supplied to the summarization prompt was constructed via:
```python
doc_evidence_map[doc_id] = p4_ev[p4_ev['document_id'] == doc_id].head(4)
```
Each evidence unit is a 3-sentence sliding window with sentence-level provenance, word counts, and character offsets. The exact concatenation was hashed (`evidence_hash`) and injected into the prompt under `VERIFIED EVIDENCE:`.

This evaluation audits the exact 36 evidence units captured in `retrieval_evidence_manifest.parquet`.

---

## 7. Retrieval Classification Rules

Every gold fact is assigned exactly one mutually exclusive label:

1. **`RETRIEVED_SUPPORTED`**: The retrieved evidence explicitly contains sufficient information to support the gold fact without unsupported extrapolation.
2. **`RETRIEVED_PARTIAL`**: The retrieved evidence contains part of the fact (e.g. office/title), but omits essential elements (e.g. personal name).
3. **`RETRIEVED_BUT_INSUFFICIENT`**: A passage touching the topic was retrieved, but the context is insufficient to establish the source-grounded fact (e.g. charge passage retrieved, but final verdict omitted).
4. **`NOT_RETRIEVED`**: The fact is present in Source Truth, but completely absent from the supplied retrieval evidence.
5. **`ABSENT_IN_SOURCE`**: The category is genuinely absent from the original court document (applied when an administrative order has no substantive trial disposition).

---

## 8. Overall Retrieval Results

### Table 8.1: Global Retrieval Performance

| Metric | Count | Percentage |
| :--- | :---: | :---: |
| **Total Gold Facts** | **85** | **100.0%** |
| `RETRIEVED_SUPPORTED` | 47 | 55.3% |
| `RETRIEVED_PARTIAL` | 1 | 1.2% |
| `RETRIEVED_BUT_INSUFFICIENT` | 0 | 0.0% |
| `NOT_RETRIEVED` | 37 | 43.5% |
| `ABSENT_IN_SOURCE` | 0 | 0.0% |
| **Overall Retrieval Recall** | **47 / 85** | **55.3%** |
| **Critical Fact Retrieval Recall** | **24 / 38** | **63.2%** |
| **Substantive Outcome Recall (Verdict/Finding/Relief/Bail)** | **0 / 7** | **0.0%** |

---

## 9. Critical Fact Retrieval Results

Critical facts represent the core legal identity, parties, charges, and outcomes of a case.

### Table 9.1: Comprehensive Audit of All 38 Critical Facts

| Document | Category | Gold Fact Value | Retrieval Status | Evidence Page | Evidence Sentence ID |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `DC_000001` | `CASE_NUMBER` | CC 179/1998 | **RETRIEVED_SUPPORTED** | p.1 | `DC_000001_P001_PAR001_SEN001` |
| `DC_000001` | `PARTIES` | State of Telangana (SHO Srirampur) | **NOT_RETRIEVED** | None | *(Omitted in top-4 truncation)* |
| `DC_000001` | `PARTIES` | Bodduna Rajamallu | **NOT_RETRIEVED** | None | *(Omitted in top-4 truncation)* |
| `DC_000002` | `CASE_NUMBER` | CC 165/1998 | **RETRIEVED_SUPPORTED** | p.1 | `DC_000002_P001_PAR001_SEN001` |
| `DC_000002` | `PARTIES` | State of Telangana (SHO Kotapally) | **RETRIEVED_SUPPORTED** | p.1 | `DC_000002_P001_PAR003_SEN001` |
| `DC_000002` | `PARTIES` | Tallapalli Sagar | **RETRIEVED_SUPPORTED** | p.1 | `DC_000002_P001_PAR003_SEN001` |
| `DC_000003` | `CASE_NUMBER` | CC 136/1998 | **RETRIEVED_SUPPORTED** | p.1 | `DC_000003_P001_PAR002_SEN001` |
| `DC_000003` | `PARTIES` | State of Telangana (SI Neelwai) | **RETRIEVED_SUPPORTED** | p.1 | `DC_000003_P001_PAR003_SEN001` |
| `DC_000003` | `PARTIES` | Satwaji @ Sudhakaranna (and others) | **RETRIEVED_SUPPORTED** | p.1 | `DC_000003_P001_PAR003_SEN001` |
| `DC_000004` | `CASE_NUMBER` | CC 135/1998 | **RETRIEVED_SUPPORTED** | p.1 | `DC_000004_P001_PAR002_SEN001` |
| `DC_000004` | `PARTIES` | State of Telangana (SI Kotapally) | **RETRIEVED_SUPPORTED** | p.1 | `DC_000004_P001_PAR003_SEN001` |
| `DC_000004` | `PARTIES` | Jangelli Ganganna @ Narayana | **RETRIEVED_SUPPORTED** | p.1 | `DC_000004_P001_PAR003_SEN001` |
| `DC_000005` | `CASE_NUMBER` | CC 134/1998 | **RETRIEVED_SUPPORTED** | p.1 | `DC_000005_P001_PAR001_SEN001` |
| `DC_000005` | `PARTIES` | State of Telangana (SI Kotapally) | **NOT_RETRIEVED** | None | *(Omitted in top-4 truncation)* |
| `DC_000005` | `PARTIES` | Golla Rajam | **NOT_RETRIEVED** | None | *(Omitted in top-4 truncation)* |
| `DC_000006` | `CASE_NUMBER` | CC 132/1998 | **RETRIEVED_SUPPORTED** | p.1 | `DC_000006_P001_PAR001_SEN001` |
| `DC_000006` | `PARTIES` | State (SI PS Jaipur) | **RETRIEVED_SUPPORTED** | p.1 | `DC_000006_P001_PAR001_SEN002` |
| `DC_000006` | `PARTIES` | Radhakka (A-8) | **RETRIEVED_SUPPORTED** | p.1 | `DC_000006_P001_PAR001_SEN004` |
| `DC_000006` | `PARTIES` | Smt. Lambu Anantha Devi (PW-1) | **NOT_RETRIEVED** | None | *(Omitted in top-4 truncation)* |
| `DC_000006` | `CHARGE` | IPC s.147, 148, 427 r/w 149 | **RETRIEVED_SUPPORTED** | p.1 | `DC_000006_P001_PAR002_SEN004` |
| `DC_000006` | `DISPOSITION` | A-4 acquitted on 08-Jan-1999 | **NOT_RETRIEVED** | None | *(Located on page 2)* |
| `DC_000006` | `JUDICIAL_FINDING` | Prosecution failed to prove guilt | **NOT_RETRIEVED** | None | *(Located on page 4)* |
| `DC_000006` | `DISPOSITION` | A-8 Acquitted under Sec. 248(1) | **NOT_RETRIEVED** | None | *(Located on page 5)* |
| `DC_000006` | `RELIEF` | A-8 set at liberty forthwith | **NOT_RETRIEVED** | None | *(Located on page 5)* |
| `DC_000006` | `BAIL_STATUS` | A-8 in judicial custody | **NOT_RETRIEVED** | None | *(Located on page 5)* |
| `DC_000007` | `CASE_NUMBER` | PRC 46/1998 | **RETRIEVED_SUPPORTED** | p.1 | `DC_000007_P001_PAR002_SEN001` |
| `DC_000007` | `PARTIES` | State of Telangana (SHO Chennur) | **RETRIEVED_SUPPORTED** | p.1 | `DC_000007_P001_PAR003_SEN001` |
| `DC_000007` | `PARTIES` | Jangili Ganganna (and 13 others) | **RETRIEVED_SUPPORTED** | p.1 | `DC_000007_P001_PAR003_SEN001` |
| `DC_000008` | `CASE_NUMBER` | PRC 44/1998 | **RETRIEVED_SUPPORTED** | p.1 | `DC_000008_P001_PAR002_SEN001` |
| `DC_000008` | `PARTIES` | State of Telangana (SHO Kotapalli) | **RETRIEVED_SUPPORTED** | p.1 | `DC_000008_P001_PAR003_SEN001` |
| `DC_000008` | `PARTIES` | Praboina Rajanna | **RETRIEVED_SUPPORTED** | p.1 | `DC_000008_P001_PAR003_SEN001` |
| `DC_000011` | `CASE_NUMBER` | PRC 38/1998 | **RETRIEVED_SUPPORTED** | p.1 | `DC_000011_P001_PAR001_SEN001` |
| `DC_000011` | `PARTIES` | State of A.P. (CI Chennur) | **RETRIEVED_SUPPORTED** | p.1 | `DC_000011_P001_PAR001_SEN002` |
| `DC_000011` | `PARTIES` | Radhakka @ Kursinga Mothu Bai | **RETRIEVED_SUPPORTED** | p.1 | `DC_000011_P001_PAR002_SEN001` |
| `DC_000011` | `CHARGE` | IPC s.147, 148, 302 r/w 149 | **NOT_RETRIEVED** | None | *(Located on page 2)* |
| `DC_000011` | `CHARGE` | Arms Act s.25(1)(a), 27 | **NOT_RETRIEVED** | None | *(Located on page 2)* |
| `DC_000011` | `DISPOSITION` | Committed to Sessions Court | **NOT_RETRIEVED** | None | *(Located on page 2)* |
| `DC_000011` | `BAIL_STATUS` | Accused is in Jail (Custody) | **NOT_RETRIEVED** | None | *(Located on page 2)* |

---

## 10. Category-Level Results

### Table 10.1: Retrieval Performance by Legal Fact Category

| Legal Category | Criticality | Total Gold Facts | Supported | Partial | Not Retrieved | Retrieval Recall |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `CASE_NUMBER` | CRITICAL | 9 | 9 | 0 | 0 | **100.0%** |
| `COURT` | IMPORTANT | 9 | 9 | 0 | 0 | **100.0%** |
| `OFFICER` | CONTEXTUAL | 12 | 10 | 1 | 1 | **83.3%** |
| `PARTIES` | CRITICAL | 19 | 14 | 0 | 5 | **73.7%** |
| `CHARGE` | CRITICAL | 3 | 1 | 0 | 2 | **33.3%** |
| `DATE` | IMPORTANT | 12 | 3 | 0 | 9 | **25.0%** |
| `PROCEDURAL_ACTION` | IMPORTANT | 13 | 1 | 0 | 12 | **7.7%** |
| `DISPOSITION` | CRITICAL | 3 | 0 | 0 | 3 | **0.0%** |
| `BAIL_STATUS` | CRITICAL | 2 | 0 | 0 | 2 | **0.0%** |
| `AMOUNT` | IMPORTANT | 1 | 0 | 0 | 1 | **0.0%** |
| `JUDICIAL_FINDING` | CRITICAL | 1 | 0 | 0 | 1 | **0.0%** |
| `RELIEF` | CRITICAL | 1 | 0 | 0 | 1 | **0.0%** |
| **Total** | | **85** | **47** | **1** | **37** | **55.3%** |

---

## 11. Document-Level Results

### Table 11.1: Retrieval Breakdown by Benchmark Document

| Document ID | Document Type | Total Facts | Critical | Important | Contextual | Supported | Partial | Not Retrieved | Recall |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `DC_000001` | Interlocutory Transfer (1p) | 8 | 3 | 4 | 1 | 3 | 0 | 5 | **37.5%** |
| `DC_000005` | Interlocutory LPC Order (1p) | 7 | 3 | 3 | 1 | 3 | 0 | 4 | **42.9%** |
| `DC_000006` | Substantive Acquittal (5p) | 20 | 10 | 6 | 4 | 9 | 1 | 10 | **45.0%** |
| `DC_000011` | Committal Order (3p) | 15 | 7 | 7 | 1 | 7 | 0 | 8 | **46.7%** |
| `DC_000002` | Interlocutory LPC Order (1p) | 7 | 3 | 3 | 1 | 5 | 0 | 2 | **71.4%** |
| `DC_000003` | Interlocutory LPC Order (1p) | 7 | 3 | 3 | 1 | 5 | 0 | 2 | **71.4%** |
| `DC_000004` | Interlocutory LPC Order (1p) | 7 | 3 | 3 | 1 | 5 | 0 | 2 | **71.4%** |
| `DC_000007` | Interlocutory LPC Order (1p) | 7 | 3 | 3 | 1 | 5 | 0 | 2 | **71.4%** |
| `DC_000008` | Interlocutory LPC Order (1p) | 7 | 3 | 3 | 1 | 5 | 0 | 2 | **71.4%** |
| **Total** | | **85** | **38** | **35** | **12** | **47** | **1** | **37** | **55.3%** |

### Lowest-Coverage Documents:
1. `DC_000001` (37.5%): Header windows truncated before complainant, accused, transfer order, and date.
2. `DC_000005` (42.9%): Header windows truncated before complainant, accused, LPC order, and date.
3. `DC_000006` (45.0%): Multi-page judgment starved of pages 2–5 (acquittal, findings, relief, bail, property damage).
4. `DC_000011` (46.7%): Multi-page committal starved of pages 2–3 (committal order, murder charges, jail custody).

---

## 12. Evidence Sufficiency Analysis

For the 47 facts classified as `RETRIEVED_SUPPORTED`:
- All 47 facts trace to exact, unambiguous text strings in the supplied evidence windows.
- Case numbers and courts were preserved across all 9 documents because they appear on Page 1 line 1.
- In 7 documents (`DC_000002`, `03`, `04`, `06`, `07`, `08`, `11`), the primary complainant and primary facing accused were captured within the first 4 windows.

For the 1 fact classified as `RETRIEVED_PARTIAL`:
- `GF-DC_000006-0019` (`OFFICER: V Sailu, CI Mancherial`): Window 4 retrieved *"The Circle Inspector of police, Mancherial filed the charge sheet"*, identifying the official capacity, but the personal identity (*"V Sailu"*) was only stated on Page 4.

---

## 13. Retrieval Failure Analysis

All 37 unretrieved facts represent **genuine retrieval failures** resulting from an upstream system limitation:
- **Mechanical Window Truncation**: The retriever took `head(4)` from a sequential window generator rather than executing semantic or category-aware retrieval.
- **Multi-page Blindness**: For documents longer than 1 page, windows on pages 2–5 had zero probability of inclusion under a rigid `head(4)` rule.
- **Bottom-of-page Dropoff**: In 1-page documents with multiple short paragraphs, windows 1–4 consumed only the top 40% of the page, cutting off the operative order and date at the bottom.

---

## 14. Administrative / Interlocutory Document Handling

In accordance with the certified Gold Set, 7 of the 9 benchmark documents (`DC_000001` to `DC_000005`, `07`, `08`) are administrative docket orders (transferring files or entering absconding cases into the LPC register) rather than substantive trials.

Substantive disposition facts were **not created** for these documents, avoiding false retrieval failure counts. However, their procedural actions (e.g. *"Permission to enter LPC Register"*) were genuine legal facts that were starved of retrieval due to bottom-of-page cutoff.

---

## 15. Provenance Validation

Every row in `retrieval_fact_evaluation.parquet` maintains complete provenance:
- Non-retrieved facts retain their Phase-2 source sentence ID, paragraph ID, page number, and source SHA-256 hash.
- Retrieved facts link their exact evidence sentence IDs, paragraph IDs, page numbers, and verbatim evidence text.
- Reconciles 100% with `sentences_provenance_v1.parquet` and `district_source_manifest_v1.parquet`.

---

## 16. Limitations

1. This evaluation audits the historical evidence supplied to the Phase 4/5 pipeline. It does not measure the theoretical maximum recall of BM25 or BGE-M3 if more chunks had been allowed.
2. The evaluation reflects the strict constraint of a 4-window prompt budget (`head(4)`).

---

## 17. Conclusions & Core Answers

### QUESTION 1: How many of the 85 source-grounded facts were actually available in the evidence supplied to the summarizer?
> **Answer**: Exactly **47 out of 85 facts (55.3%)** were fully available in the supplied evidence. 1 fact (1.2%) was partially available. **37 facts (43.5%) were completely unavailable** to the summarizer.

### QUESTION 2: How many critical facts were retrievable?
> **Answer**: Exactly **24 out of 38 critical facts (63.2%)** were retrievable. Most alarmingly, **0 out of 7 substantive judicial outcome facts (0.0%)** (acquittal verdicts, committal orders, judicial findings, relief of liberty, and custody status) were retrievable.

### QUESTION 3: Which failures are genuine retrieval failures?
> **Answer**: All 37 unretrieved facts are genuine retrieval failures caused by upstream window truncation (`head(4)`), which completely starved the summarizer of multi-page content and bottom-of-page operative orders.

### QUESTION 4: Which facts were technically retrieved but had insufficient context?
> **Answer**: 1 fact (`GF-DC_000006-0019`: CI Mancherial) was partially retrieved with office title present but personal name (*V. Sailu*) omitted.

### QUESTION 5: Is the retrieval layer strong enough to proceed to summary-level fact preservation evaluation?
> **Answer**: **NO.** The retrieval layer is fundamentally inadequate for causal attribution. When a summarizer fails to report an acquittal verdict that was on Page 5 of a judgment, penalizing the model for a "summarization hallucination" or "translation failure" is scientifically invalid when the model was never provided the verdict in its evidence prompt.

---

## 18. Gate Decision for P5.3

```
============================================================
FINAL GATE DECISION
============================================================

GATE CLASSIFICATION:
    REQUIRES_RETRIEVAL_REPAIR

JUSTIFICATION:
The current retrieval layer achieves only 55.3% overall recall
and 0.0% recall on substantive judicial dispositions, findings,
relief, and bail status.

Proceeding directly to P5.3 (summary fact preservation) with
this evidence layer would measure retrieval starvation rather
than generation capability. Retrieval repair (or whole-document
evidence budgeting) must precede causal summarization claims.
============================================================
```
