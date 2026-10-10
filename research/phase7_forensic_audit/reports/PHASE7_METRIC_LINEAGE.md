# Phase 7 Metric Lineage & Provenance Specification

**Project:** Vidhik Indian Legal AI  
**Phase:** Phase 7 Translation Layer Forensic Audit  

---

## 1. Metric Lineage & Recomputation Table

| Metric | Reported Value | Raw Artifact | Formula | Numerator | Denominator | Weighting | Recomputed Value | Lineage Status |
|---|---:|---|---|---:|---:|---|---:|---|
| **T0 Critical Strict** | **23.68%** | `fact_level_evaluation.parquet` | $\frac{\text{SUPPORTED}}{\text{Eligible Critical Units}}$ | 36 | 152 | Unweighted pooled | **23.68%** | **CONFIRMED** |
| **T0 Critical Partial** | **26.32%** | `fact_level_evaluation.parquet` | $\frac{\text{SUPPORTED} + \text{PARTIAL}}{\text{Eligible Critical Units}}$ | 40 | 152 | Unweighted pooled | **26.32%** | **CONFIRMED** |
| **T0 Critical Omission** | **73.68%** | `fact_level_evaluation.parquet` | $\frac{\text{OMITTED}}{\text{Eligible Critical Units}}$ | 112 | 152 | Unweighted pooled | **73.68%** | **CONFIRMED** |
| **T2 Critical Strict** | **23.68%** | `fact_level_evaluation.parquet` | $\frac{\text{SUPPORTED}}{\text{Eligible Critical Units}}$ | 36 | 152 | Unweighted pooled | **23.68%** | **CONFIRMED** |
| **T2 Critical Partial** | **44.74%** | `fact_level_evaluation.parquet` | $\frac{\text{SUPPORTED} + \text{PARTIAL}}{\text{Eligible Critical Units}}$ | 68 | 152 | Unweighted pooled | **44.74%** | **CONFIRMED** |
| **T2 Critical Omission** | **55.26%** | `fact_level_evaluation.parquet` | $\frac{\text{OMITTED}}{\text{Eligible Critical Units}}$ | 84 | 152 | Unweighted pooled | **55.26%** | **CONFIRMED** |
| **T5 Critical Partial** | **44.74%** | `fact_level_evaluation.parquet` | $\frac{\text{SUPPORTED} + \text{PARTIAL}}{\text{Eligible Critical Units}}$ | 68 | 152 | Unweighted pooled | **44.74%** | **CONFIRMED (Reuses T3/T4 text)** |
| **Translation Fidelity (T0)** | **40.00%** | `fact_level_evaluation.parquet` | $\frac{\text{FIDELITY\_PASS}}{\text{Total Units}}$ | 136 | 340 | Unweighted pooled | **40.00%** | **CONFIRMED** |
| **Translation Fidelity (T2/T5)**| **48.24%** | `fact_level_evaluation.parquet` | $\frac{\text{FIDELITY\_PASS}}{\text{Total Units}}$ | 164 | 340 | Unweighted pooled | **48.24%** | **CONFIRMED** |
| **Terminology Survival (All)** | **100.0%** | `entity_translation_results.parquet`| $\frac{\text{VERBATIM} + \text{RESTORED}}{\text{Registered Entities}}$ | 144 | 144 | Unweighted pooled | **100.0%** | **CONFIRMED** |
| **Contradictions (All)** | **0.00%** | `fact_level_evaluation.parquet` | $\frac{\text{CONTRADICTIONS}}{\text{Total Units}}$ | 0 | 340 | Unweighted pooled | **0.00%** | **CONFIRMED** |
| **Unsupported Additions (All)** | **0.00%** | `fact_level_evaluation.parquet` | $\frac{\text{HALLUCINATED}}{\text{Total Units}}$ | 0 | 340 | Unweighted pooled | **0.00%** | **CONFIRMED** |

---

## 2. Mathematical Definition of the +18.42% Delta
$$\Delta_{\text{crit, partial}} = \text{Rate}(T2) - \text{Rate}(T0) = \frac{68}{152} - \frac{40}{152} = \frac{28}{152} = +18.421\%$$

Where the 28 newly preserved units correspond to:
$$\mathcal{U}_{\text{delta}} = \{GF\text{-}DC\_00000X\text{-}0003 \mid X \in \{1, 2, 3, 4, 5, 7, 8\}\} \times \{ta, hi, kn, mr\}$$
Each unit shifted from `OMITTED` to `PARTIALLY_SUPPORTED` due to the enhanced regex pattern:
`"(?:State\s+of\s+[A-Z][a-z]+(?:\\s+[A-Z][a-z]+)*)"`
which successfully protected `State of Telangana` against neural translation loss.
