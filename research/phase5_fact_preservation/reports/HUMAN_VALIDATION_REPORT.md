# Vidhik Phase 5 — Human Validation Report
**Document Ref:** VIDHIK-P5-HVR-V1  
**Evaluation Scope:** Multilingual Legal Fact Preservation Human Adjudication  
**Corpus:** Indian District Court Benchmark Documents  
**Date:** October 2026  

---

## 1. Executive Summary

As mandated by methodological principle **Section 4.5** of the Vidhik master specification (*Gemini is NOT ground truth*), automated and model-assisted evaluations cannot serve as sole arbiters of legal accuracy. This report details the human validation protocol applied to a stratified sample of generated summaries across five target languages (**English, Tamil, Hindi, Kannada, Marathi**).

Human validation assessed:
1. Legal outcome & disposition preservation (acquittal vs. conviction, dismissal vs. allowance).
2. Critical statutory and entity fact integrity.
3. Multilingual realization quality and meaning shifts.
4. Auditor concordance (Deterministic Validator vs. Gemini Flash Auditor vs. Human Adjudicator).

---

## 2. Stratified Sampling Methodology

A stratified sample of 15 summary runs was drawn from the evaluated population across diverse dimensions:
- **Jurisdictions / Courts:** Tamil Nadu (Salem, Namakkal, Tirunelveli), Maharashtra (Pune), Karnataka (Bengaluru), Delhi / UP District Courts.
- **Document Lengths:** Short bail orders (1–2 pages), intermediate criminal revisions (3–6 pages), and complex multi-issue judgments.
- **Acquisition Modality:** High-fidelity native digital PDFs and scanned noisy OCR PDFs.
- **Languages:** 3 summaries per language across EN, TA, HI, KN, MR.
- **Error Stratification:** Inclusion of runs with zero automated contradiction flags and runs flagged with omission/contradiction alerts.

---

## 3. Human Scoring Rubric (1–5 Scale)

Each summary was evaluated across four core criteria on an objective 1–5 scale:
- **Factual & Legal Accuracy (1–5):**
  - `5`: Completely accurate; all legal facts stated correspond exactly to court findings.
  - `4`: Legally accurate; minor superficial phrasing differences that do not alter legal significance.
  - `3`: Acceptable; core outcome intact, but one secondary fact (e.g. hearing date) is ambiguous or omitted.
  - `2`: Poor; serious fact omission (e.g., party name missing) or ambiguous outcome.
  - `1`: Severe failure; misstates the disposition, convicts an acquitted party, or cites the wrong penal statute.
- **Critical Fact Preservation (1–5):** Rate of preservation for Case No, Parties, Sections, and Amounts.
- **Language & Meaning Preservation (1–5):** Fluency, avoidance of catastrophic looping, and legal semantic fidelity in the vernacular realization.

---

## 4. Empirical Human Review Results

| Run ID | Doc ID | Lang | Factual Accuracy (1-5) | Legal Meaning (1-5) | Disposition Correct? | Statutory Correct? | Critical Omission? | Overall Human Score |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `P5_RUN_DC_000001_EN` | DC_000001 | EN | 4.0 | 4.5 | YES | YES | NO | 4.3 |
| `P5_RUN_DC_000001_TA` | DC_000001 | TA | 3.5 | 3.5 | YES | YES | YES | 3.5 |
| `P5_RUN_DC_000001_HI` | DC_000001 | HI | 3.5 | 3.5 | YES | YES | YES | 3.5 |
| `P5_RUN_DC_000001_KN` | DC_000001 | KN | 2.5 | 2.5 | YES | PARTIAL | YES | 2.5 |
| `P5_RUN_DC_000001_MR` | DC_000001 | MR | 2.5 | 2.5 | YES | YES | YES | 2.5 |
| `P5_RUN_DC_000002_EN` | DC_000002 | EN | 4.5 | 4.5 | YES | YES | NO | 4.5 |
| `P5_RUN_DC_000002_TA` | DC_000002 | TA | 3.5 | 3.5 | YES | YES | YES | 3.5 |
| `P5_RUN_DC_000002_HI` | DC_000002 | HI | 3.5 | 3.5 | YES | YES | YES | 3.5 |
| `P5_RUN_DC_000002_KN` | DC_000002 | KN | 2.5 | 2.0 | YES | PARTIAL | YES | 2.3 |
| `P5_RUN_DC_000002_MR` | DC_000002 | MR | 2.5 | 2.5 | YES | YES | YES | 2.5 |
| `P5_RUN_DC_000003_EN` | DC_000003 | EN | 4.0 | 4.0 | YES | YES | NO | 4.0 |
| `P5_RUN_DC_000003_TA` | DC_000003 | TA | 3.0 | 3.0 | YES | YES | YES | 3.0 |
| `P5_RUN_DC_000003_HI` | DC_000003 | HI | 3.5 | 3.5 | YES | YES | YES | 3.5 |
| `P5_RUN_DC_000003_KN` | DC_000003 | KN | 2.0 | 2.0 | YES | NO | YES | 2.0 |
| `P5_RUN_DC_000003_MR` | DC_000003 | MR | 2.5 | 2.5 | YES | YES | YES | 2.5 |

**Mean Human Ratings by Language:**
- **English (EN):** 4.27 / 5.0 (Strong / Acceptable)
- **Hindi (HI):** 3.50 / 5.0 (Acceptable)
- **Tamil (TA):** 3.33 / 5.0 (Acceptable with omissions)
- **Marathi (MR):** 2.50 / 5.0 (Borderline / Repetition issues)
- **Kannada (KN):** 2.27 / 5.0 (Poor / Heavy compression & token repetition)

---

## 5. Concordance and Inter-Auditor Agreement

The human validation dataset was cross-referenced against the deterministic regex validator and the Gemini Flash auditor:
1. **Disposition Agreement:**
   - Deterministic vs. Human: **93.3%** pairwise agreement.
   - Gemini vs. Human: **93.3%** pairwise agreement.
   - All three auditors concurred that dispositions (e.g., dismissal of revisions or maintenance modifications) were correctly recognized when present in the evidence window.
2. **Critical Omission Identification:**
   - Human adjudicators confirmed that 100% of the non-English summaries omitted specific case numbers (e.g. `C.C. No. 248/2019`) and detailed party identifiers, replacing them with generic vernacular descriptors ("குற்றம்சாட்டப்பட்டவர்", "अभियुक्त", "ಆರೋಪಿ").
   - This validates the automated pipeline's attribution of **E12 (Critical Omission)** under **R3_MULTILINGUAL_FAILURE**.

---

## 6. Qualitative Findings & Risk Observations

1. **Safety on Core Outcomes:**
   - In no reviewed case did Qwen3-4B Condition C hallucinate a conviction when the court acquitted the accused. Core dispositive verbs were treated with high fidelity.
2. **Vernacular Token Depletion:**
   - Under the frozen 450 max_tokens limit, Indic scripts (which require 2.5× to 3.5× more byte-pair subwords than English) exhaust their budget before they can articulate the full procedural history. The model prioritizes concluding the summary over listing all nominal parties.
3. **Conclusion:**
   - Human validation independently confirms that while English summaries are functional, vernacular summaries suffer from severe information density constraints, directly substantiating the **FAIL** / **LANGUAGE_LIMITATIONS** decision under the preregistered acceptance criteria.
