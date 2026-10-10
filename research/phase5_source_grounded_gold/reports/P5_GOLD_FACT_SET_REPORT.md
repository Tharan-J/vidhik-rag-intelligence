# Phase 5: Source-Grounded Legal Fact Gold Set Report
**Authoritative Reference Layer for the 9-Document Benchmark**

---

## 1. Executive Summary

This report establishes and certifies the **Source-Grounded Legal Fact Gold Set** for the 9-document Indian District Court summarization benchmark in Vidhik Phase 5.

Following the methodological audit of the initial Phase 5 baseline, which revealed that 1,089/1,089 machine candidate facts had not undergone human verification, suffered from 170 duplicate records, malformed currency prefixes (`rs,`), docket-header intrusions into party fields, and administrative transfer misclassifications, this new artifact establishes an auditable, source-grounded ground truth independently extracted from the original court documents and validated through the immutable Phase-2 provenance chain.

```
============================================================
P5 SOURCE-GROUNDED GOLD FACT SET CERTIFICATION
============================================================

Benchmark documents:                         9
Actual summaries:                           45 (9 docs × 5 languages)
Gold verified facts:                        85
Candidate facts audited:                    89
Promoted candidate facts:                   48
Rejected candidates:                        25
Duplicate candidates:                       16
Ambiguous facts:                             0
Newly discovered facts:                     37

Critical facts:                             38
Important facts:                            35
Contextual facts:                           12

Provenance resolution rate:              100.0% (85/85)
Sentence-level verification:             100.0% (85/85)
PDF SHA-256 integrity:                   100.0% (85/85)

Documents with complete independent coverage: 9 / 9
Documents requiring further review:           0 / 9

GOLD SET STATUS:
    CERTIFIED
============================================================
```

---

## 2. Mandatory Methodological Framework

> **Authoritative Definition:**
> The Source-Grounded Legal Fact Gold Set is the authoritative Phase 5 reference layer for the 9-document benchmark. Each verified fact is independently grounded in the original court PDF and traceable through the immutable Phase-2 provenance chain. Phase-3 retrieved evidence and Phase-4/5 model summaries are evaluated against this source-grounded reference rather than defining the reference themselves.

To maintain strict scientific validity and prevent circular reasoning, the pipeline explicitly distinguishes between four distinct operational layers:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SOURCE TRUTH                                             │
│    Original court PDF + SHA-256 + Immutable Phase 2        │
│    Extracted Sentences & Paragraphs                         │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Evaluated Against)
┌──────────────────────────────▼──────────────────────────────┐
│ 2. GOLD REFERENCE LAYER (This Artifact)                     │
│    85 Human-Audited Facts: Exact Substrings, Verified       │
│    Provenance, No Inferences, Explicit Rejections           │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Evaluation Standards)
┌──────────────────────────────▼──────────────────────────────┐
│ 3. RETRIEVAL EVIDENCE                                       │
│    Phase 3 retrieved chunks (What the model was allowed    │
│    to see; NOT ground truth)                                │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ 4. MODEL OUTPUT & EVALUATION                                │
│    Phase 4/5 Multilingual Summaries (en, ta, hi, kn, mr)    │
│    Preservation & Hallucination evaluated against Source    │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Benchmark Discovery & Inventory

The evaluation benchmark covers exactly 9 District Court documents that produced 45 real multilingual summaries across English (`en`), Tamil (`ta`), Hindi (`hi`), Kannada (`kn`), and Marathi (`mr`).

### Table 3.1: Benchmark Inventory Summary

| Document ID | Source PDF | Page Count | Summaries | Languages Present | Provenance Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `DC_000001` | `...orders_1994_202100001791998_1.pdf` | 1 | 5 | `en,hi,kn,mr,ta` | Complete (100%) |
| `DC_000002` | `...orders_1998_202100001651998_1.pdf` | 1 | 5 | `en,hi,kn,mr,ta` | Complete (100%) |
| `DC_000003` | `...orders_1998_202100001361998_1.pdf` | 1 | 5 | `en,hi,kn,mr,ta` | Complete (100%) |
| `DC_000004` | `...orders_1994_202100001351998_1.pdf` | 1 | 5 | `en,hi,kn,mr,ta` | Complete (100%) |
| `DC_000005` | `...orders_1996_202100001341998_1.pdf` | 1 | 5 | `en,hi,kn,mr,ta` | Complete (100%) |
| `DC_000006` | `...orders_1998_202100001321998_1.pdf` | 5 | 5 | `en,hi,kn,mr,ta` | Complete (100%) |
| `DC_000007` | `...orders_1991_203300000461998_1.pdf` | 1 | 5 | `en,hi,kn,mr,ta` | Complete (100%) |
| `DC_000008` | `...orders_1995_203300000441998_1.pdf` | 1 | 5 | `en,hi,kn,mr,ta` | Complete (100%) |
| `DC_000011` | `...orders_1998_203300000381998_1.pdf` | 3 | 5 | `en,hi,kn,mr,ta` | Complete (100%) |
| **Total**   | **9 Documents** | **15** | **45** | **5 Languages** | **100% Verified** |

---

## 4. Gold Fact Counts and Distributions

### Table 4.1: Breakdown by Criticality and Document

| Document ID | Critical Facts | Important Facts | Contextual Facts | Total Gold Facts |
| :--- | :---: | :---: | :---: | :---: |
| `DC_000001` | 3 | 4 | 1 | **8** |
| `DC_000002` | 3 | 3 | 1 | **7** |
| `DC_000003` | 3 | 3 | 1 | **7** |
| `DC_000004` | 3 | 3 | 1 | **7** |
| `DC_000005` | 3 | 3 | 1 | **7** |
| `DC_000006` | 10 | 6 | 4 | **20** |
| `DC_000007` | 3 | 3 | 1 | **7** |
| `DC_000008` | 3 | 3 | 1 | **7** |
| `DC_000011` | 7 | 7 | 1 | **15** |
| **Total**   | **38** | **35** | **12** | **85** |

### Table 4.2: Distribution by Legal Category

| Category | Criticality | Count | Description / Role |
| :--- | :--- | :---: | :--- |
| `PARTIES` | CRITICAL | 19 | Verified complainants, accused persons, and hostile prosecution witnesses |
| `PROCEDURAL_ACTION` | IMPORTANT | 13 | Administrative transfers, LPC register entries, case splits, and warrant returns |
| `OFFICER` | CONTEXTUAL | 12 | Presiding Judicial Officers, Investigating Officers, and Defense Counsel |
| `DATE` | IMPORTANT | 12 | Judgment dates, order dates, incident dates, and FIR registration dates |
| `CASE_NUMBER` | CRITICAL | 9 | Primary case identifiers (CC and PRC numbers) verified on caption |
| `COURT` | IMPORTANT | 9 | Presiding District Courts (JCJ Chennur, JMFC Chennur) |
| `CHARGE` | CRITICAL | 3 | Substantive statutory penal charges (IPC 147, 148, 427, 302; Arms Act 25, 27) |
| `DISPOSITION` | CRITICAL | 3 | Substantive trial outcomes (Acquittal A-8, Acquittal A-4, Committal to Sessions) |
| `BAIL_STATUS` | CRITICAL | 2 | Custodial status (A-8 judicial custody / set at liberty; A-8 in Jail) |
| `AMOUNT` | IMPORTANT | 1 | Substantive property damage amount (Rs. 2,05,000 APSRTC bus damage) |
| `JUDICIAL_FINDING` | CRITICAL | 1 | Judicial determination that prosecution failed to prove guilt beyond reasonable doubt |
| `RELIEF` | CRITICAL | 1 | Judicial relief granted (Accused A-8 set at liberty forthwith) |
| **Total** | | **85** | |

---

## 5. Candidate Audit and Disposition

All 89 machine-extracted candidate records in `fact_ledger_v1.parquet` for the 9 benchmark documents were independently audited.

### Table 5.1: Candidate Fact Audit Disposition

| Candidate Status | Count | Percentage | Description |
| :--- | :---: | :---: | :--- |
| `GOLD_VERIFIED` (Promoted) | 48 | 53.9% | Candidate fact matched original source text, passed legal criteria, and promoted to gold |
| `REJECTED_CANDIDATE` | 25 | 28.1% | Candidate fact failed legal or technical quality gates (malformed, docket text, non-fact) |
| `DUPLICATE_OF_FACT` | 16 | 18.0% | Redundant multiple extractions of the identical legal event or section citation |
| **Total Candidates Audited** | **89** | **100.0%** | |

### Table 5.2: Categorization of Rejection Reasons

| Rejection Reason | Count | Concrete Examples from Candidates | Legal Impact |
| :--- | :---: | :--- | :--- |
| `NON_SUBSTANTIVE_OR_UNGROUNDED` | 17 | `Accused`, `Chennur, JCJ Court Complex` (vague) | Generic labels lacking entity identity |
| `REDUNDANT_DUPLICATE_EXTRACTION` | 16 | 3× `CHARGE_SHEET`, 2× `EXAMINED_UNDER_SECTION` | Artificial inflation of candidate counts |
| `MALFORMED_CURRENCY_PREFIX` | 2 | `rs,` in `DC_000006`, `rs,` in `DC_000011` | OCR artifacts with zero numeric value |
| `DOCKET_HEADER_NOT_PARTY` | 2 | `Accused\nDOCKET ORDER\nThis case is suo moto...` | OCR order header misclassified as party name |
| `ADMINISTRATIVE_TRANSFER_NOT_DISPOSITION`| 1 | `transferred` in `DC_000001` | Administrative transfer mislabeled as trial verdict |
| `JUDICIAL_OFFICER_NOT_PARTY` | 1 | `JAYARAM REDDY\nJUDL MAGISTRATE OF FIRST C...` | Magistrate name misclassified as litigant party |
| `MISCLASSIFIED_PROCEDURAL_TEXT` | 1 | `District and Sessions Judge, Adilabad vide...` | Administrative proceeding text misclassified as relief |
| `MALFORMED_STATUTE_FRAGMENT` | 1 | `ACT` in `DC_000011` | Truncated token from Arms Act citation |

---

## 6. Independent Coverage Pass Results

To eliminate circular evaluation where the machine extractor defines ground truth, an independent human legal audit was conducted across 18 legal categories:

1. Case Number & Caption
2. Litigant Parties
3. Presiding Court
4. Decision / Order Date
5. Substantive Penal Charges
6. Statutory Provisions
7. Background Facts & Incidents
8. Arguments & Pleadings
9. Issues Framed
10. Judicial Findings & Reasoning
11. Procedural Actions & Transfers
12. Relief Requested
13. Relief Granted
14. Substantive Disposition
15. Sentence Imposed
16. Bail & Custody Status
17. Monetary Amounts & Damage
18. Connected Crimes & FIRs

### Key Discoveries from Independent Pass:
- **Property Damage Amount (`DC_000006`)**: Uncovered the true monetary claim (`Rs. 2,05,000/-` property damage to APSRTC bus) which the machine extractor had reduced to `rs,`.
- **Judicial Findings vs. Disposition (`DC_000006`)**: Separated the core judicial finding (*"prosecution has failed to prove the guilt of A-8 beyond all reasonable doubt"*) from the formal acquittal verdict under Section 248(1) Cr.P.C. and the relief granted (*"set at liberty forthwith"*).
- **Procedural Realities (`DC_000001` to `DC_000005`, `07`, `08`)**: Correctly identified that 7 of the 9 documents are administrative interlocutory/docket orders (transfer or LPC register entries for absconding accused) where substantive trial disposition on the merits is **`ABSENT_IN_SOURCE`**.
- **Crucial Officers & Witnesses (`DC_000006`, `DC_000011`)**: Recovered names of Presiding Magistrates (`Ms. Shaik Rehana`, `Sri K. Jayaram Reddy`), Investigating Officers (`Md. Mustafa`, `V. Sailu`), Defense Counsel (`Sri G. Ramesh Chander`), and key witnesses (`PW-1 Lambu Anantha Devi`).

---

## 7. Artifact Manifest and Quality Gates

All generated artifacts are immutable, versioned, and mirrored in the workspace:

```
phase5_source_grounded_gold/
├── benchmark_inventory.csv          # 9 benchmark docs, 45 summaries breakdown
├── source_inventory.csv             # Provenance paths, SHAs, page counts
├── candidate_facts.parquet          # 89 candidate rows preserved
├── rejected_candidates.parquet      # 41 rejected/duplicate candidates with audit reasons
├── ambiguous_facts.parquet          # Clean schema for ambiguous source tracking
├── gold_facts.parquet               # 85 Gold-verified facts (18-column schema)
├── gold_facts.csv                   # CSV version of gold fact ledger
├── human_review_queue.csv           # Human review table sorted by doc/criticality
├── source_fact_coverage.csv         # Category-level coverage matrix
├── tools/
│   └── p5_gold_fact_review.html     # Interactive search/filter reviewer interface
├── reports/
│   └── P5_GOLD_FACT_SET_REPORT.md   # This formal certification report
└── tests/
    └── test_p5_gold_fact_set.py     # 14/14 Automated pytest quality gates (PASSED)
```

### Table 7.1: Quality Gate Verification Results

| Quality Gate | Requirement | Test Function | Result |
| :--- | :--- | :--- | :---: |
| Gate 1 | Exactly 9 benchmark documents | `test_1_exactly_nine_benchmark_documents` | **PASSED** |
| Gate 2 | Exactly 45 actual summaries discovered | `test_2_exactly_45_actual_summaries_discovered` | **PASSED** |
| Gate 3 | Every benchmark document has 5 languages | `test_3_every_benchmark_document_has_five_languages` | **PASSED** |
| Gate 4 | Complete provenance for all gold facts | `test_4_every_gold_verified_fact_has_complete_provenance` | **PASSED** |
| Gate 5 | Real Phase-2 sentence IDs | `test_5_every_gold_fact_traces_to_real_phase2_sentence` | **PASSED** |
| Gate 6 | Sentences match parent document | `test_6_every_source_sentence_belongs_to_correct_document` | **PASSED** |
| Gate 7 | PDF SHA matches frozen source | `test_7_pdf_sha_matches_frozen_source` | **PASSED** |
| Gate 8 | No malformed AMOUNT facts | `test_8_no_malformed_amount_gold_facts` | **PASSED** |
| Gate 9 | No docket-header PARTIES facts | `test_9_no_docket_header_parties_gold_facts` | **PASSED** |
| Gate 10 | No administrative transfer as DISPOSITION | `test_10_no_unqualified_administrative_transfer_as_disposition` | **PASSED** |
| Gate 11 | No unmanaged duplicate facts | `test_11_no_duplicate_gold_facts_without_relationship_metadata` | **PASSED** |
| Gate 12 | No machine-only fact marked gold | `test_12_no_machine_only_fact_marked_gold_verified` | **PASSED** |
| Gate 13 | No invented values (exact substrings) | `test_13_no_source_grounded_fact_has_invented_value` | **PASSED** |
| Gate 14 | Independent coverage pass recorded | `test_14_independent_coverage_pass_recorded_for_every_document` | **PASSED** |
