# District Court Corpus Forensic Audit & RAG Readiness Report

**Date:** 2026-10-02 07:48:42  
**Corpus Level:** District Court  
**Evaluated Frozen Population:** 161 documents  
**Audit Methodology:** Non-destructive forensic analysis of fixed research artifacts.  

---

## 1. Executive Summary & Inventory

The fixed District Court dataset comprises **161 documents** frozen under a documented corpus-construction pipeline. Every document has been verified on disk for PDF bit integrity, text extraction completeness, structural markers, citations, legal reasoning indicators, and metadata reliability.

### Inventory Verification Table

| Metric | Verified Count | Integrity Status |
| :--- | ---: | :---: |
| Total Documents | 161 | 100.0% Verified |
| Valid Text PDFs | 133 | 82.6% |
| Page-Aligned Texts | 161 | 100.0% |
| Documents with Citations | 2 | 1.2% |
| Mean Metadata Completeness | 46.0% | Empirical Score |

## 2. Feature Distribution Summary

Below are the exact continuous feature distributions calculated across all documents:

| feature                                | N   | mean    | std     | min  | P10   | P25   | median | P75    | P90    | P95     | P99     | max     |
| -------------------------------------- | --- | ------- | ------- | ---- | ----- | ----- | ------ | ------ | ------ | ------- | ------- | ------- |
| page_count                             | 161 | 2.01    | 2.57    | 1.0  | 1.0   | 1.0   | 1.0    | 2.0    | 4.0    | 8.0     | 12.8    | 15.0    |
| word_count                             | 161 | 344.0   | 637.29  | 4.0  | 28.0  | 79.0  | 122.0  | 290.0  | 697.0  | 1369.0  | 3318.0  | 3440.0  |
| character_count                        | 161 | 2263.53 | 3932.37 | 17.0 | 204.0 | 507.0 | 807.0  | 2059.0 | 4899.0 | 10438.0 | 19542.0 | 21282.0 |
| paragraph_count                        | 161 | 9.86    | 25.95   | 1.0  | 2.0   | 2.0   | 3.0    | 8.0    | 19.0   | 32.0    | 95.4    | 282.0   |
| numbered_paragraph_count               | 161 | 0.04    | 0.36    | 0.0  | 0.0   | 0.0   | 0.0    | 0.0    | 0.0    | 0.0     | 1.4     | 4.0     |
| numbered_paragraph_percentage          | 161 | 0.28    | 2.38    | 0.0  | 0.0   | 0.0   | 0.0    | 0.0    | 0.0    | 0.0     | 9.17    | 25.0    |
| citation_occurrence_count              | 161 | 0.04    | 0.35    | 0.0  | 0.0   | 0.0   | 0.0    | 0.0    | 0.0    | 0.0     | 0.8     | 4.0     |
| unique_citation_count                  | 161 | 0.03    | 0.32    | 0.0  | 0.0   | 0.0   | 0.0    | 0.0    | 0.0    | 0.0     | 0.4     | 4.0     |
| legal_reference_count                  | 161 | 1.19    | 4.04    | 0.0  | 0.0   | 0.0   | 0.0    | 0.0    | 3.0    | 8.0     | 20.4    | 32.0    |
| precedent_relationship_count           | 161 | 0.37    | 1.22    | 0.0  | 0.0   | 0.0   | 0.0    | 0.0    | 1.0    | 2.0     | 7.0     | 9.0     |
| issue_indicator_total                  | 161 | 0.22    | 1.25    | 0.0  | 0.0   | 0.0   | 0.0    | 0.0    | 0.0    | 0.0     | 7.0     | 11.0    |
| citations_per_1000_words               | 161 | 0.02    | 0.17    | 0.0  | 0.0   | 0.0   | 0.0    | 0.0    | 0.0    | 0.0     | 0.26    | 2.05    |
| legal_references_per_1000_words        | 161 | 2.03    | 6.13    | 0.0  | 0.0   | 0.0   | 0.0    | 0.0    | 6.58   | 12.71   | 37.74   | 40.32   |
| precedent_relationships_per_1000_words | 161 | 1.03    | 3.35    | 0.0  | 0.0   | 0.0   | 0.0    | 0.0    | 2.2    | 9.26    | 17.41   | 19.61   |
| issue_indicators_per_1000_words        | 161 | 0.1     | 0.5     | 0.0  | 0.0   | 0.0   | 0.0    | 0.0    | 0.0    | 0.0     | 2.61    | 3.89    |
| metadata_completeness_score            | 161 | 0.46    | 0.06    | 0.38 | 0.38  | 0.38  | 0.5    | 0.5    | 0.5    | 0.5     | 0.5     | 0.5     |

## 3. Document Length Distributions & Bands

| Length Band | Document Count | Percentage |
| :--- | ---: | ---: |
| VERY_SHORT | 90 | 55.9% |
| SHORT | 59 | 36.6% |
| MEDIUM | 12 | 7.5% |


## 4. Citation & Authority Distribution

- **Total Citation Occurrences:** 6
- **Total Unique Authorities:** 5
- **Mean Citations per 1,000 Words:** 0.02
- **Mean Statutory References per 1,000 Words:** 2.03

## 5. Temporal Characterization

| decision_year | document_count | median_pages | median_words | mean_citations_per_1k | mean_legal_refs_per_1k | excellent_quality_pct |
| ------------- | -------------- | ------------ | ------------ | --------------------- | ---------------------- | --------------------- |
| 1998.0        | 18.0           | 1.0          | 89.5         | 0.0                   | 1.16                   | 0.0                   |
| 2010.0        | 18.0           | 1.0          | 4.0          | 0.0                   | 0.65                   | 0.0                   |
| 2020.0        | 18.0           | 1.0          | 473.0        | 0.0                   | 0.87                   | 5.6                   |
| 2021.0        | 17.0           | 1.0          | 96.0         | 0.04                  | 0.52                   | 0.0                   |
| 2024.0        | 54.0           | 1.0          | 123.0        | 0.04                  | 3.09                   | 0.0                   |
| 2025.0        | 36.0           | 1.0          | 152.0        | 0.0                   | 2.85                   | 0.0                   |

## 6. Document Anomalies & Forensic Observations

Anomalies represent observable empirical properties rather than deletion criteria:

| anomaly_flag              | count | percentage |
| ------------------------- | ----- | ---------- |
| MISSING_CNR               | 161   | 100.0      |
| MISSING_JUDGE             | 161   | 100.0      |
| ZERO_CITATIONS            | 159   | 98.76      |
| LOW_METADATA_COMPLETENESS | 52    | 32.3       |
| VERY_SHORT_TEXT           | 22    | 13.66      |
| IMAGE_ONLY_PDF            | 14    | 8.7        |
| NO_SECTION_STRUCTURE      | 9     | 5.59       |
| HIGH_SYMBOL_DENSITY       | 6     | 3.73       |
| CORRUPTED_TEXT_ENCODING   | 6     | 3.73       |
| MANY_BLANK_PAGES          | 1     | 0.62       |

## 7. RAG Architectural Implications for this Court Level

1. **Ultra-Short Document Handling:** District Court documents are predominantly single-page interim orders (median 122 words). Fixed 512-token chunks would pad or group unrelated proceedings.
2. **Factual / Docket-Heavy Queries:** Due to near-zero formal citations (0.22 citations/doc), retrieval cannot rely on precedent graphs; dense semantic and BM25 lexical matching on case numbers, parties, and statutes is necessary.
3. **Metadata Gap Management:** Unindexed CNR and Judge fields require search pipelines to route queries using State, District, Court Complex, and Year.

---
*Generated automatically by Vidhik Corpus Audit Engine.*
