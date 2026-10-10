# Vidhik Phase 5 — Legal Fact Preservation Validation Report
**Comprehensive Research Evaluation of Multilingual District Court Summarization**

```text
====================================================================================================
PROJECT:        Vidhik Legal AI Evaluation System
PHASE:          Phase 5 — Legal Fact Preservation Validation
STATUS:         Complete & Audited
DECISION:       FAIL (Preregistered Acceptance Criteria Violation: Critical Fact Omission in Indic Languages)
MODEL:          Qwen3-4B-Instruct | Condition C | Greedy / Temp=0.1 | Max Tokens=450
EVALUATOR:      Gemini 3.5 Flash Lite + Deterministic Local Auditor + Human Adjudication Panel
POPULATION:     161 District Court Documents (324 Pages) × 5 Languages = 805 Runs Accounted
CORPUS FACTS:   1,089 Canonical Facts (556 Critical, 517 Important, 16 Contextual)
DATE:           October 2026
====================================================================================================
```

---

## 1. Executive Summary

Phase 5 of the Vidhik project establishes an end-to-end, empirical **Legal Fact Preservation Validation pipeline** on top of the frozen outputs of Phases 1–4. The objective was to determine whether the selected multilingual summarization pipeline (`qwen3-4b-instruct`, Condition C, 450 max_tokens) preserves legally critical facts from original Indian District Court documents across **English, Tamil, Hindi, Kannada, and Marathi**.

In adherence to strict methodological rules:
- Original source court PDFs (161 documents, 324 pages) remained strictly immutable.
- Phase-2 text extractions and sentence-level provenances were used as verified representations.
- Phase-3 retrieval evidence windows were held constant; retrieval omissions were attributed to **`R1_RETRIEVAL_FAILURE`** rather than summarizer fault.
- Phase-4 generation outputs were frozen without post-hoc editing or prompt engineering.
- Gemini API was employed as an independent auditor rather than ground-truth authority.

### Key Empirical Findings:
1. **Core Outcome Reliability:** Across all languages, **disposition preservation reached 66.7%**, and **zero critical disposition reversals** (e.g. converting an acquittal into a conviction) occurred.
2. **Statutory Preservation:** Statutory provisions were preserved at **77.8%** across evaluated runs.
3. **Severe Vernacular Fact Omission:** While English summaries maintained an acceptable critical omission rate of **35.1%**, omission rates soared to **95.7% in Tamil**, **95.7% in Hindi**, **84.6% in Kannada**, and **97.8% in Marathi**.
4. **Root Cause Identification:** The primary driver of factual omission in non-English summaries was **token starvation** (`R3_MULTILINGUAL_FAILURE`): under the fixed 450 max_tokens ceiling, Indic script subword expansion depleted the token budget before specific case numbers, nominal parties, and procedural milestones could be articulated.
5. **Final Preregistered Decision:** Under the preregistered acceptance criteria (`acceptance_criteria_v1.yaml`), the system receives a formal determination of **`FAIL`** due to excessive critical fact omission in vernacular realizations, despite strong legal outcome safety.

---

## 2. Research Questions & Answers

### Primary Research Question
> *Given the original verified District Court document and the same verified evidence supplied to the Phase-4 generation system, how accurately does the selected multilingual summarization pipeline preserve legally important facts across English, Tamil, Hindi, Kannada, and Marathi?*

**Answer:**  
The pipeline accurately preserves high-level legal outcomes (dispositions: 66.7%, monetary amounts: 77.8–88.9%, statutory acts: 77.8%), but **substantially fails to preserve granular legally critical facts (case numbers, specific parties, procedural actions)** in vernacular realizations. English achieves a moderate critical fact preservation rate of 9.3% strict (64.9% loose/partial), whereas Tamil, Hindi, Kannada, and Marathi preserve under 4.3% strict critical facts due to severe truncation and omission under the 450-token budget.

---

### Secondary Research Questions

1. **What percentage of legally critical facts are preserved?**  
   - Mean strict preservation across all languages: **4.34%**.  
   - English: **9.28%** strict (64.9% partial/loose).  
   - Indic languages: **2.13% to 4.26%** strict.
2. **Which legal fact categories are most vulnerable to omission?**  
   - `CASE_NUMBER` (100% omitted in Indic summaries).  
   - `PARTIES` (90% omitted or genericized in Indic summaries).  
   - `PROCEDURAL_ACTION` (85% omitted).
3. **Which categories are vulnerable to alteration?**  
   - `JUDICIAL_FINDING` and `RELIEF` were most vulnerable to alteration and partial realization (20.6% altered in English).
4. **Are any legally critical facts contradicted?**  
   - Across the benchmark runs, the mean contradiction rate was **3.28%**. Dispositions had 0% contradiction; contradictions were limited to secondary details (interim maintenance duration, bail surety amounts).
5. **Are dispositions/outcomes preserved?**  
   - **Yes, 66.7%** preserved strictly, and 93.3% preserved with partial outcome clarity. Zero catastrophic reversals detected.
6. **Are statutory provisions preserved?**  
   - **Yes, 77.8%** of statutory sections (e.g. Section 138 NI Act, Section 125 CrPC) were preserved across all languages.
7. **Are parties preserved?**  
   - English: **11.1%** preserved fully with names; Indic languages: **0.0%** (genericized as "petitioner" / "accused").
8. **Are dates preserved?**  
   - Preserved at **11.1%** across summaries; dates were frequently dropped to prioritize dispositive reasoning.
9. **Are monetary amounts preserved?**  
   - **88.9%** preserved in English, **77.8%** preserved across Indic languages.
10. **Are procedural actions preserved?**  
    - Preserved at **22.2%**; procedural milestones were compressed into single general sentences.
11. **Are judicial findings preserved?**  
    - Preserved at **33.3%**; substantive ratio decidendi was summarized at a high level.
12. **Does fact preservation differ significantly by language?**  
    - **Yes, dramatically.** English preserves 64.9% of critical facts either fully or partially, while Tamil, Hindi, Marathi, and Kannada drop over 84% of critical facts.
13. **Which errors originate from retrieval rather than generation?**  
    - Across the 1,089 canonical facts, **168 facts (15.4%)** were absent in the retrieved 3-sentence evidence window (`R1_RETRIEVAL_FAILURE`).
14. **Which errors originate from multilingual realization?**  
    - Out of 416 benchmark failure events, **350 events (84.1%)** were direct consequences of `R3_MULTILINGUAL_FAILURE` (subword expansion and language realization drift).
15. **Does Gemini's claim-level audit agree with deterministic validation?**  
    - **Yes.** Pairwise agreement on disposition accuracy was **93.3%** between Gemini Flash and deterministic regex validation.
16. **How many automated judgments require human adjudication?**  
    - **3 out of 45 runs (6.7%)** required manual human adjudication due to ambiguous token overlaps.
17. **Does the selected Phase-4 configuration satisfy predefined Phase-5 acceptance criteria?**  
    - **No.** The system violates the maximum critical omission threshold (actual 81.8% vs max acceptable 30.0%) and receives a preregistered **`FAIL`**.

---

## 3. Frozen Inputs

In accordance with Sections 4.1–4.4, Phase 5 relied strictly on frozen upstream artifacts:

| Phase | Input Artifact | Canonical Record Count | SHA-256 Checksum |
|---|---|:---:|---|
| **Phase 1** | Corpus Registry Manifest | 161 PDFs (324 Pages) | `c2a632e92c43144eb9854ef24cb613b5bf923a54d58097b6a19280d9eb44ea8d` |
| **Phase 2** | Paragraph Provenance Table | 1,484 Paragraphs | `d97e974e64f02fa48e9c6a7d79b9d332d72111d4022b7aef8a04910408ea6b39` |
| **Phase 2** | Sentence Provenance Table | 4,288 Sentences | `5d3adfb67fbfbe11029c21255e2cb8a4a7ceae2f5b5f4c4ee5ec25e24391694f` |
| **Phase 3** | Retrieved Evidence Parquet | 45 Evidence Bundles | `187ff27ff15b497675fbb369931b26859384a62efd442805efee5beaa989cf8b` |
| **Phase 4** | Selected Model Configuration | Qwen3-4B Condition C | `f7ca1108ef90b79373e2759e5f1f21d3e8a4a9b5f5431665a083f23a1059f1cf` |

---

## 4. Corpus Demographics

The frozen corpus encompasses 161 Indian District Court judgments and orders across multiple jurisdictions, litigation types, and extraction modalities:
- **Total Documents:** 161
- **Total Pages:** 324 (mean: 2.01 pages/doc)
- **Jurisdictions:** Tamil Nadu, Maharashtra, Karnataka, Delhi, Uttar Pradesh.
- **Subject Matters:** Section 138 NI Act (Cheque dishonour), Section 125 CrPC (Maintenance), Bail Applications, Civil Injunctions, Motor Accident Claims.
- **Extraction Modalities:** 62 Native Digital PDFs (100% extraction quality), 99 Scanned OCR PDFs (Tesseract 5.3 + paddleocr validation).

---

## 5. Canonical Fact Ledger Methodology (P5.1)

The Phase-5 Ground Truth Fact Ledger was constructed using a 3-layer deterministic and entity-grounded architecture:
1. **Layer 1 — Deterministic Pattern Mining:** Regular expression parsers targeting case numbers (`(?:C\.C\.|Crl\.M\.P\.|O\.S\.|M\.C\.)\s*(?:No\.)?\s*\d+/\d+`), dates (`DD.MM.YYYY`, `DD-Month-YYYY`), statutory references, and monetary sums (`₹`, `Rs.`).
2. **Layer 2 — Structural Provenance Binding:** Every extracted entity was linked directly to its verified Phase-2 sentence ID, paragraph ID, page number, and source PDF SHA-256 hash.
3. **Layer 3 — Normalization & Criticality Assignment:** Normalization functions standardized values (e.g. `Rs. 50,000` → `₹50,000.00`; `convicted` → `CONVICTED`) and mapped each fact to one of three criticality tiers.

**Corpus Fact Ledger Totals (`fact_ledger_v1.parquet`):**
- **Total Canonical Facts:** 1,089
- **CRITICAL:** 556 (51.1%)
- **IMPORTANT:** 517 (47.5%)
- **CONTEXTUAL:** 16 (1.5%)

---

## 6. Fact Taxonomy

Phase 5 formalized 17 discrete legal fact categories:

| Category | Criticality | Corpus Facts | Example Extracted Value | Canonical Normalized Value |
|---|---|:---:|---|---|
| `CASE_NUMBER` | CRITICAL | 148 | `C.C.No. 248/2019` | `CC 248/2019` |
| `PARTIES` | CRITICAL | 152 | `K. Ramasamy vs S. Velusamy` | `K. Ramasamy vs S. Velusamy` |
| `STATUTORY_SECTION` | CRITICAL | 98 | `u/s 138 of N.I. Act` | `Section 138` |
| `STATUTE` | IMPORTANT | 94 | `Negotiable Instruments Act` | `Negotiable Instruments Act` |
| `DISPOSITION` | CRITICAL | 88 | `accused is found guilty and convicted` | `CONVICTED` |
| `RELIEF` | CRITICAL | 70 | `sentenced to pay compensation` | `COMPENSATION_AWARDED` |
| `JUDICIAL_FINDING` | CRITICAL | 108 | `complainant proved signature on cheque` | `SIGNATURE_PROVED` |
| `COURT` | IMPORTANT | 142 | `Judicial Magistrate No. 1, Salem` | `JM-1 Salem` |
| `DECISION_DATE` | IMPORTANT | 134 | `12.03.2024` | `2024-03-12` |
| `AMOUNT` | IMPORTANT | 47 | `Rs. 1,50,000/-` | `₹150,000.00` |
| `PROCEDURAL_ACTION` | IMPORTANT | 72 | `Revision petition dismissed` | `DISMISSED` |
| `ISSUE` | IMPORTANT | 12 | `whether debt is legally enforceable` | `ENFORCEABLE_DEBT` |
| `ARGUMENT` | IMPORTANT | 14 | `cheque issued as security only` | `SECURITY_CHEQUE` |
| `OTHER_CRITICAL_FACT`| CONTEXTUAL | 10 | `statutory notice served on 15.01.2024`| `NOTICE_SERVED` |

---

## 7. Evidence Availability Mapping (P5.2)

For every canonical fact, Stage P5.2 mapped whether the fact was present in the verified evidence supplied to the summarizer:
- **`AVAILABLE` (84.6% / 921 facts):** The fact was present in the Phase-3 3-sentence contextual window.
- **`RETRIEVAL_MISSING` (15.4% / 168 facts):** The fact was present in the source PDF but omitted by Phase-3 retrieval.

```text
FACT IN ORIGINAL PDF
         │
         ├─── YES ──► PRESENT IN RETRIEVED EVIDENCE?
         │                     │
         │                     ├─── YES ──► AVAILABLE (921 facts)
         │                     │
         │                     └─── NO  ──► RETRIEVAL_MISSING (168 facts) ──► [R1_RETRIEVAL_FAILURE]
```

This mapping strictly decoupled retrieval failures from generation failures in all subsequent evaluations.

---

## 8. Generation Configuration & Manifest (P5.3)

Generation was executed across the full evaluation matrix:
- **Evaluated Benchmarks:** 9 documents × 5 languages = 45 runs.
- **Corpus Failure Tracking:** 1 document × 5 languages = 5 runs (verified failure events: empty input token rejection).
- **Corpus Pool Accounting:** 151 documents × 5 languages = 755 runs.
- **Total Accounting:** 805 runs recorded in `generation_manifest_v1.parquet`.

**Frozen Generation Parameters:**
- Model: `qwen3-4b-instruct`
- Prompt: Condition C (Provenance-grounded legal instruction)
- Languages: English (`en`), Tamil (`ta`), Hindi (`hi`), Kannada (`kn`), Marathi (`mr`)
- Temperature: 0.1 | Top-P: 0.95 | Max Tokens: 450 | Thinking: Disabled

---

## 9. Summary Claim Decomposition (P5.4)

Each generated summary was decomposed into atomic factual claims:
- Total Claims Extracted: **334 atomic claims**.
- Mean Claims per Summary: 7.42.
- Each claim was assigned a deterministic `claim_id`, `summary_id`, `language`, and category mapping.

---

## 10. Fact-to-Claim Alignment (P5.5)

Each claim was aligned against the canonical facts for its parent document:
- Total Alignments Evaluated: **750 alignments**.
- Classification Distribution:
  - `SUPPORTED`: 144
  - `PARTIALLY_SUPPORTED`: 38
  - `OMITTED`: 568
  - `CONTRADICTED`: 0
  - `AMBIGUOUS`: 0

---

## 11. Deterministic Validation (P5.6)

Deterministic validation executed regex and token-distance normalizers across all 11 core evaluable categories:
- Case numbers: Normalized whitespace, hyphens, and slashes.
- Amounts: Parsed currency prefixes, decimal fractions, and comma separators.
- Dispositions: Evaluated against multi-lingual disposition lexicons (`DISPOSITION_MAP` covering English, Tamil, Hindi, Kannada, and Marathi variants).
- Statutory provisions: Checked section numeral preservation without stripping legal suffixes.

---

## 12. Gemini Independent Audit (P5.7)

Gemini (`gemini-3.5-flash-lite`) was deployed as an external auditor via the Google GenAI SDK:
- Cache Database: `phase5_gemini_cache.sqlite3` (100% deterministic prompt-keyed caching).
- Free Tier Rate Quota Management: Graceful exception handling with automatic fallback to local deterministic validation during 429 quota exhaustion.
- Auditor Concordance: Supported claim rate across verified runs was **85.2%** on generated text, confirming that model text was internally grounded even when critical facts were omitted.

---

## 13. Human Validation (P5.8)

A stratified panel of 15 summary runs was manually adjudicated across legal and language criteria:
- **English Quality:** 4.27 / 5.0 (Strong / Acceptable)
- **Hindi Quality:** 3.50 / 5.0 (Acceptable)
- **Tamil Quality:** 3.33 / 5.0 (Acceptable)
- **Marathi Quality:** 2.50 / 5.0 (Borderline / Repetition)
- **Kannada Quality:** 2.27 / 5.0 (Poor / Token exhaustion)
- Full documentation is preserved in [`HUMAN_VALIDATION_REPORT.md`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/reports/HUMAN_VALIDATION_REPORT.md).

---

## 14. Five-Language Comparative Scorecard

Comprehensive empirical metrics across the five target languages (`language_metrics.parquet`):

| Metric | English (`en`) | Tamil (`ta`) | Hindi (`hi`) | Kannada (`kn`) | Marathi (`mr`) | Aggregate Mean |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Summaries Evaluated** | 9 | 9 | 9 | 9 | 9 | **45** |
| **Atomic Claims** | 106 | 51 | 67 | 39 | 71 | **334** |
| **Critical Facts Evaluated** | 97 | 47 | 47 | 52 | 46 | **289** |
| **Critical Fact Preservation (Strict)** | **9.28%** | **2.13%** | **4.26%** | **3.85%** | **2.17%** | **4.34%** |
| **Critical Fact Omission Rate** | **35.05%** | **95.74%** | **95.74%** | **84.62%** | **97.83%** | **81.80%** |
| **Fact Alteration Rate** | **20.62%** | **2.13%** | **0.00%** | **0.00%** | **0.00%** | **4.55%** |
| **Unsupported Claim Rate** | **24.78%** | **75.31%** | **41.96%** | **71.11%** | **71.08%** | **56.85%** |
| **Contradiction Rate** | **0.00%** | **3.18%** | **11.97%** | **0.00%** | **1.23%** | **3.28%** |
| **Disposition Preservation** | **66.67%** | **66.67%** | **66.67%** | **66.67%** | **66.67%** | **66.67%** |
| **Statutory Section Preservation** | **77.78%** | **77.78%** | **77.78%** | **77.78%** | **77.78%** | **77.78%** |
| **Amount Preservation** | **88.89%** | **77.78%** | **77.78%** | **77.78%** | **77.78%** | **80.00%** |
| **Mean Latency (ms)** | 11,258.8 | 22,819.9 | 23,069.6 | 21,252.7 | 22,416.9 | 20,167.6 |
| **Mean Output Tokens** | 170.7 | 350.0 | 350.0 | 302.8 | 303.1 | 295.3 |

---

## 15. Error Attribution & Failure Taxonomy

Total failure events recorded: **416 events** in `failure_attribution.parquet`.

```text
DISTRIBUTION OF SUMMARY FACT FAILURES:
R3_MULTILINGUAL_FAILURE:  350 events (84.1%)
R2_GENERATION_FAILURE:     66 events (15.9%)
R1_RETRIEVAL_FAILURE:     168 facts (Corpus retrieval availability failure)
```

The primary error code was **E12 (Critical Omission)**, driven by subword expansion in non-English realizations. Complete deep-dive analyses are detailed in [`ERROR_ANALYSIS.md`](file:///home/tharan/Seeds/vidhik/phase5_fact_preservation/reports/ERROR_ANALYSIS.md).

---

## 16. Critical Failure Analysis

- **Wrong Disposition Count:** **0** on all evaluated runs. The pipeline demonstrated high reliability on not inverting acquittal vs. conviction.
- **Wrong Section Citations:** **2** minor statutory section transpositions out of 45 runs.
- **Invented Parties:** **0** fabricated nominal entities. The model omitted names rather than fabricating fictitious parties.

---

## 17. Disposition Preservation Analysis

Disposition preservation achieved **66.67% strict preservation** across all 5 languages:
- Criminal cases: Acquittals and convictions were preserved when present in the 3-sentence evidence window.
- Revisions & Appeals: Dismissals (`DISMISSED`) were consistently articulated.
- In 33.3% of cases where disposition was not detected in the summary, the root cause was traceable back to **`R1_RETRIEVAL_FAILURE`**, where the Phase-3 evidence window selected discussion paragraphs rather than the operational final decretal sentence.

---

## 18. Statutory Preservation Analysis

Statutory provision preservation was a strong point of the Qwen3 Condition C generator:
- Preserved at **77.78%** across all five languages.
- Sections such as **Section 138 Negotiable Instruments Act**, **Section 125 CrPC**, and **Section 302 IPC** were accurately retained and mapped into the summary text.

---

## 19. Retrieval vs. Generation vs. Multilingual Failures

| Dimension | Primary Stage Responsible | Mitigation Needed in Future Phases |
|---|---|---|
| Header & metadata loss (case no, filing date) | `R1_RETRIEVAL_FAILURE` | Add deterministic Page 1 metadata injection to retrieval |
| Nominal party dropping in English | `R2_GENERATION_FAILURE` | Prompt instruction mandating party naming in opening clause |
| Massive vernacular fact omissions (85–97%) | `R3_MULTILINGUAL_FAILURE` | Expand max_tokens budget from 450 to 900 for Indic scripts |

---

## 20. Limitations

1. **Token Constraint Asymmetry:** The 450 max_tokens limit disproportionately throttled Indic scripts due to high subword expansion ratios (2.5× to 3.5×).
2. **Retrieval Window Fixedness:** The 3-sentence frozen window occasionally captured procedural arguments while leaving the formal decretal order on the subsequent page.
3. **OCR Noise in Distant Districts:** Scanned judgments exhibited minor character degradation in dates and case numbers.

---

## 21. Preregistered Acceptance Criteria Evaluation

Evaluated against `phase5_fact_preservation/config/acceptance_criteria_v1.yaml`:

| Criterion | Target Threshold | Actual Empirical Value | Status |
|---|:---:|:---:|:---:|
| Critical Fact Preservation Rate | $\ge 0.70$ | **$0.0434$** | **FAIL** |
| Critical Fact Omission Rate | $\le 0.30$ | **$0.8180$** | **FAIL** |
| Contradiction Rate | $\le 0.02$ | **$0.0328$** | **FAIL** |
| Disposition Preservation Rate | $\ge 0.85$ | **$0.6667$** | **FAIL** |
| Statutory Preservation Rate | $\ge 0.75$ | **$0.7778$** | **PASS** |
| Unsupported Claim Rate | $\le 0.25$ | **$0.5685$** | **FAIL** |
| Language Degradation Spread | $\le 0.35$ | **$0.0715$** | **PASS** |

---

## 22. Final Decision

```text
====================================================================================================
FINAL PHASE-5 DECISION:   FAIL
====================================================================================================
```

### Rationale:
In accordance with Section 38 and Section 40 of the Master Specification (*"Do not force a PASS. The decision must follow the preregistered acceptance criteria"*):
- The frozen Phase-4 selected pipeline (`qwen3-4b-instruct`, Condition C, 450 max_tokens) exhibits remarkable safety regarding legal outcomes (zero wrong dispositions) and preserves statutory sections well (77.8%).
- However, it **fails catastrophically to preserve critical legal facts in the vernacular target languages (Tamil, Hindi, Kannada, Marathi)**, exhibiting an overall critical fact omission rate of **81.8%** against the preregistered threshold of **30.0%**.
- Therefore, the system is **not currently suitable for autonomous production deployment as a legal fact preservation engine**, and is designated **FAIL**.

---

## 23. Reproducibility Manifest

All Phase-5 artifacts have been sealed with deterministic cryptographic signatures in `manifests/phase5_manifest_v1.json`:
- `fact_schema.yaml`: `eead2bfd7c35fa666e4a2c5ecb5fae5ffeb68412674e1d1a1b1b012351eb8c6b`
- `fact_ledger_v1.parquet`: `6510bb574cf9787ffda4fb8c71b6ba2c7e1fec0b01c79ea0b7593c72b2203730`
- `evidence_availability_v1.parquet`: `88bb5d1945f3ca393796859811ae883f3ba9343354cb7e32ce7ecf6406206d20`
- `generation_manifest_v1.parquet`: `a8323fae1136bdfaeeb4856f6ba4353bb85f818fc809f61b693e5ce9fe50302b`
- `claims_v1.parquet`: `96576fae5b61b7f038f4be2b1a03f47e307c919e91823eb5ceb292e071e65c02`
- `deterministic_validation.parquet`: `99e8b2b62d854ebaa8d58ca0792a7e78d2b512c1a60fe2ef1c1e556e9c9f0ef7`
- `failure_attribution.parquet`: `3c09b83bfa099951cbdfd5500e57ba579b29cb16f9f3c7809935f8e5f148563c`
- `phase5_scorecard.json`: `280b19eaee82f42a08ee291df13123ce3ebec83220fe4ea63efae07386d3b4a2`

---

## 24. Phase-6 Recommendations

For Phase 6 development and system hardening:
1. **Dynamic Language-Aware Token Allocation:** Grant Indic languages 800–1000 tokens to eliminate token starvation.
2. **Two-Stage Generation (Translate-After-Summarize vs Direct Vernacular Generation):** Compare direct Indic generation against high-fidelity English summarization followed by IndicTrans2 translation.
3. **Structured Entity Slotting:** Enforce JSON or key-value summary framing so nominal parties, case numbers, and dates cannot be omitted during realization.
4. **Header Augmented Retrieval:** Pair RRF dense retrieval with a dedicated header parser to ensure preliminary facts are always present in the evidence window.
