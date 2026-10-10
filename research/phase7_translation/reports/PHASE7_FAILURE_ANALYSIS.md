# Phase 7 Causal Failure Analysis & Attribution

**Vidhik Indian Legal AI Research Pipeline**  
**Phase 7: English → Indian Language Legal Translation Layer**  

---

## 1. Causal Failure Taxonomy (T1 - T13)
The failure attribution analysis models the translation pipeline causally. Each of the 340 evaluated Indic fact units is assigned to exactly one causal failure category based on factual presence and output behavior:

- **NONE (Supported / Preserved):** The gold legal fact is present in the English intermediate summary and correctly preserved in the Indic translation.
- **T1_SOURCE_TRANSLATION_INPUT_ERROR:** The fact was never captured in the English intermediate summary (inherent limitation of intermediate summarization/retrieval upstream).
- **T2_ENTITY_CORRUPTION:** The underlying sentence was translated, but a critical legal entity (case number, date, statute, section, amount) was distorted during translation tokenization.
- **T3_TERMINOLOGY_ERROR:** A statutory legal term or disposition was mistranslated into non-judicial vernacular.
- **T4_FACT_OMISSION:** The fact was present in English, but the neural translation model dropped or elided the clause or fact entirely.
- **T5_FACT_DISTORTION:** The translated fact survived only partially (e.g. year preserved but case docket digits lost).
- **T6_CONTRADICTION:** The translation introduced an inverted judicial outcome (e.g. acquitted rendered as convicted).
- **T7_UNSUPPORTED_ADDITION:** The translation hallucinated legal facts not found in the English summary.
- **T8_ALIGNMENT_FAILURE:** Misalignment between source claims and translated clauses.
- **T9_CONTEXT_FAILURE:** Anaphoric or cross-sentence drift caused by translating sentences in total isolation.
- **T10_TRANSLATION_MODEL_FAILURE:** Degenerate output or translation stuttering.
- **T11_OUTPUT_TRUNCATION:** Output string abruptly terminated due to sequence length limit.
- **T12_EVALUATOR_DISAGREEMENT:** Minor formatting variance flagged during evaluator validation.
- **T13_OTHER:** Unclassified residual failure.

---

## 2. Quantitative Failure Distribution ($N=340$ Fact Units per System)

| System ID | NONE (Preserved) | T1 Source Input Error | T2 Entity Corruption | T4 Fact Omission | T5 Fact Distortion | T6 Contradiction | T7 Unsupported Additions |
|---|---:|---:|---:|---:|---:|---:|---:|
| **T0 (Baseline)** | 44 (12.94%) | 92 (27.06%) | 24 (7.06%) | 180 (52.94%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| **T1 (Context)** | 44 (12.94%) | 92 (27.06%) | 24 (7.06%) | 180 (52.94%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| **T2 (Enhanced Term)** | 72 (21.18%) | 92 (27.06%) | 0 (0.00%) | 176 (51.76%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| **T3 (Claim-Aligned)** | 72 (21.18%) | 92 (27.06%) | 0 (0.00%) | 176 (51.76%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| **T4 (Candidate Rerank)** | 72 (21.18%) | 92 (27.06%) | 0 (0.00%) | 176 (51.76%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| **T5 (Combined Optimal)** | **72 (21.18%)** | **92 (27.06%)** | **0 (0.00%)** | **176 (51.76%)** | **0 (0.00%)** | **0 (0.00%)** | **0 (0.00%)** |

---

## 3. Key Causal Takeaways
1. **Upstream Ceiling ($T1$):** Exactly 92 units (27.06% of the 340 units) were not present in the intermediate English summary. No translation system can preserve facts that were never supplied to it in the English intermediate representation without hallucination.
2. **Curing Entity Corruption ($T2$):** System T0 suffered from 24 entity corruption failures ($7.06\%$) where case numbers and statutes were deformed. Enhanced entity protection (T2 through T5) completely eliminated $T2$ failures down to $0.0\%$.
3. **Translation Neural Omission ($T4$):** The primary remaining bottleneck is neural seq2seq omission ($51.76\%$), where IndicTrans2 condenses or omits subordinate legal clauses during translation.
4. **Zero Contradictions ($T6$):** All 6 systems maintained a strict 0.0% contradiction rate, validating that English-first translation does not invert acquittals, bails, or relief.
