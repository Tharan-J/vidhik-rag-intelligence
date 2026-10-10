# Phase 7 Human Validation Protocol & Annotation Schema

**Vidhik Indian Legal AI Research Pipeline**  
**Phase 7: English → Indian Language Legal Translation Layer**  

---

## 1. Objective & Guidelines
This protocol governs the blinded cross-lingual human verification of legal summaries translated from certified English summaries into **Tamil**, **Hindi**, **Kannada**, and **Marathi**.

The purpose is to validate:
1. Whether legally critical facts and entities (case numbers, statutes, sections, amounts, dates, dispositions) survived neural translation.
2. Whether the translated statements altered judicial outcomes or introduced legal contradictions.
3. Fluency and judicial appropriateness of legal phrasing.

---

## 2. Evaluation Dimensions

| Dimension | Values | Description |
|---|---|---|
| **Factual Preservation** | `YES` / `PARTIAL` / `NO` | Does the Indic translation contain the factual claim established in the English summary? |
| **Legal Meaning Equivalence** | `YES` / `DEGRADED` / `NO` | Is the judicial meaning, standard of review, or statutory scope identical? |
| **Contradiction Detected** | `NO` / `YES` | Did the translation invert any relief, finding, or disposition (e.g. acquitted vs convicted)? |
| **Terminology Correctness** | `YES` / `CORRUPTED` / `NO` | Are legal terms (e.g., anticipatory bail, Section 302 IPC) translated according to standard Indian judicial practice? |
| **Fluency Rating** | `1` to `5` | `5` = Natural judicial vernacular, `1` = Completely unintelligible translation artifact. |

---

## 3. Sampling Stratification
The validation set ([`validation_sample.csv`](file:///home/tharan/Seeds/vidhik/phase7_translation/human_validation/validation_sample.csv)) contains **32 stratified evaluation units**:
- 8 units each across **Tamil (`ta`)**, **Hindi (`hi`)**, **Kannada (`kn`)**, and **Marathi (`mr`)**.
- 20 units targeting `CRITICAL` legal facts (dispositions, charges, statutes, case numbers).
- 12 units targeting `IMPORTANT` contextual facts (amounts, dates, presiding officers).
