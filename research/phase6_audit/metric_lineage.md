# Metric Lineage & Mathematical Formulations

**Project:** Vidhik Legal RAG — Phase 6 Forensic Audit  
**Scope:** Reconciling Evaluated Metric Lineage across Systems and Reports  

---

## 1. Lineage Table

| Metric | Reported Value | Raw Artifact | Formula | Numerator | Denominator | Unit of Analysis | Weighting | Reproducible? |
|---|---:|---|---|---:|---:|---|---|---|
| **System B Critical Preservation (Empirical)** | **7.2%** | `fact_level_evaluation.parquet` | $\frac{\text{SUPPORTED} + \text{PARTIAL}}{\text{Eligible Critical Units}}$ | 11 | 152 | Fact-language unit (Indic) | Pooled unweighted | **YES** (Exact: 7.24%) |
| **System B Critical Preservation (Draft README)** | **8.6%** | None (P5 Historical Estimate) | N/A (Unexecuted placeholder) | N/A | N/A | N/A | N/A | **NO** (Obsolete draft) |
| **System C Critical Preservation (Empirical)** | **21.1%** | `fact_level_evaluation.parquet` | $\frac{\text{SUPPORTED} + \text{PARTIAL}}{\text{Eligible Critical Units}}$ | 32 | 152 | Fact-language unit (Indic) | Pooled unweighted | **YES** (Exact: 21.05%) |
| **System C Critical Preservation (Draft README)** | **68.4%** | `P5_EVIDENCE_BUDGET_TABLES.md` | $\frac{\text{Evidence Retrieved Critical Facts}}{\text{Total Critical Facts}}$ | 26 | 38 | Benchmark fact (English Retrieval) | Unweighted facts | **NO** (Conflation with P5 $B=4$ evidence recall) |
| **System D Critical Preservation (Empirical)** | **26.3%** | `fact_level_evaluation.parquet` | $\frac{\text{SUPPORTED} + \text{PARTIAL}}{\text{Eligible Critical Units}}$ | 40 | 152 | Fact-language unit (Indic) | Pooled unweighted | **YES** (Exact: 26.32%) |
| **System D Critical Preservation (Draft README)** | **76.3%** | `P5_EVIDENCE_BUDGET_TABLES.md` | $\frac{\text{Evidence Retrieved Critical Facts}}{\text{Total Critical Facts}}$ | 29 | 38 | Benchmark fact (English Retrieval) | Unweighted facts | **NO** (Conflation with P5 $B=8$ evidence recall) |
| **System D Translation Fidelity (Empirical)** | **40.0%** | `translation_fidelity.parquet` | $\frac{\text{PASS Units}}{\text{Total Indic Units}}$ | 136 | 340 | Fact-language unit (Indic) | Pooled unweighted | **YES** (Exact: 40.00%) |
| **System D Translation Fidelity (Draft README)** | **89.5%** | `P5_EVIDENCE_BUDGET_TABLES.md` | $\frac{\text{Evidence Retrieved Critical Facts}}{\text{Total Critical Facts}}$ | 34 | 38 | Benchmark fact (English Retrieval) | Unweighted facts | **NO** (Conflation with P5 $B=15$ evidence recall) |
| **System A Critical Preservation (Intermediate)** | **81.6%** | `fact_level_evaluation.parquet` | $\frac{\text{SUPPORTED} + \text{PARTIAL}}{\text{Eligible Critical Units (en)}}$ | 31 | 38 | Fact-language unit (English) | Unweighted facts | **YES** (Exact: 81.58%) |
| **System D Terminology Survival** | **100.0%** | `terminology_evaluation.parquet` | $\frac{\text{PRESENT\_VERBATIM} + \text{RESTORED}}{\text{Total Evaluated Entities}}$ | 100 | 100 | Protected entity unit | Pooled unweighted | **YES** (Exact: 100.0%) |

---

## 2. Mathematical Definitions

### A. Critical Fact Preservation
Let $\mathcal{F}_{\text{crit}}$ be the subset of gold facts where $\text{criticality} = \text{CRITICAL}$ ($|\mathcal{F}_{\text{crit}}| = 38$).
Let $\mathcal{L}_{\text{indic}} = \{\text{ta}, \text{hi}, \text{kn}, \text{mr}\}$ ($|\mathcal{L}_{\text{indic}}| = 4$).
The Indic critical universe size is:
$$N_{\text{crit, indic}} = |\mathcal{F}_{\text{crit}}| \times |\mathcal{L}_{\text{indic}}| = 38 \times 4 = 152$$

- **Strict Critical Preservation:**
  $$\text{Preservation}_{\text{strict}} = \frac{\sum_{f \in \mathcal{F}_{\text{crit}}} \sum_{l \in \mathcal{L}_{\text{indic}}} \mathbb{I}(\text{status}(s, f, l) = \text{SUPPORTED})}{152}$$

- **Partial-Inclusive Critical Preservation:**
  $$\text{Preservation}_{\text{partial-incl}} = \frac{\sum_{f \in \mathcal{F}_{\text{crit}}} \sum_{l \in \mathcal{L}_{\text{indic}}} \mathbb{I}(\text{status}(s, f, l) \in \{\text{SUPPORTED}, \text{PARTIALLY\_SUPPORTED}\})}{152}$$

- **Critical Omission:**
  $$\text{Omission}_{\text{crit}} = \frac{\sum_{f \in \mathcal{F}_{\text{crit}}} \sum_{l \in \mathcal{L}_{\text{indic}}} \mathbb{I}(\text{status}(s, f, l) = \text{OMITTED})}{152}$$

### B. Translation Fidelity
Evaluated across all Indic fact units ($N = 85 \times 4 = 340$):
$$\text{Fidelity}(s) = \frac{\sum_{f \in \mathcal{F}} \sum_{l \in \mathcal{L}_{\text{indic}}} \mathbb{I}(\text{fidelity}(s, f, l) = \text{PASS})}{340}$$
Where $\text{fidelity}(s, f, l) = \text{PASS}$ indicates that the semantic legal meaning of fact $f$ present in the English intermediate summary was faithfully rendered in language $l$ without distortion or loss.

### C. Legal Terminology Preservation
Evaluated across 25 high-priority entities (Case Numbers, Statutes, Sections, Dates, Monetary Amounts) evaluated across the 4 Indic languages ($N = 25 \times 4 = 100$):
$$\text{Terminology Preservation} = \frac{\sum_{e=1}^{100} \mathbb{I}(\text{status}(e) \in \{\text{PRESENT\_VERBATIM}, \text{RESTORED\_APPENDED}\})}{100}$$
System D and System E achieve $100/100 = 100.0\%$, whereas System C degrades to $62.0\%$ due to aggressive subword transliteration/translation, and System B achieves only $28.0\%$.
