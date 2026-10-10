# High Court Corpus Forensic Audit & RAG Readiness Report

**Date:** 2026-10-02 07:48:42  
**Corpus Level:** High Court  
**Evaluated Frozen Population:** 600 documents  
**Audit Methodology:** Non-destructive forensic analysis of fixed research artifacts.  

---

## 1. Executive Summary & Inventory

The fixed High Court dataset comprises **600 documents** frozen under a documented corpus-construction pipeline. Every document has been verified on disk for PDF bit integrity, text extraction completeness, structural markers, citations, legal reasoning indicators, and metadata reliability.

### Inventory Verification Table

| Metric | Verified Count | Integrity Status |
| :--- | ---: | :---: |
| Total Documents | 600 | 100.0% Verified |
| Valid Text PDFs | 600 | 100.0% |
| Page-Aligned Texts | 600 | 100.0% |
| Documents with Citations | 302 | 50.3% |
| Mean Metadata Completeness | 96.8% | Empirical Score |

## 2. Feature Distribution Summary

Below are the exact continuous feature distributions calculated across all documents:

| feature                                | N   | mean     | std      | min   | P10   | P25    | median  | P75      | P90     | P95      | P99       | max      |
| -------------------------------------- | --- | -------- | -------- | ----- | ----- | ------ | ------- | -------- | ------- | -------- | --------- | -------- |
| page_count                             | 600 | 21.88    | 47.26    | 1.0   | 1.0   | 4.0    | 10.0    | 22.0     | 43.1    | 71.5     | 229.06    | 718.0    |
| word_count                             | 600 | 4999.36  | 10453.11 | 29.0  | 100.8 | 738.0  | 1941.5  | 4801.75  | 10509.7 | 17948.9  | 48969.33  | 133331.0 |
| character_count                        | 600 | 32291.26 | 68473.48 | 255.0 | 705.7 | 5059.5 | 12324.0 | 30435.75 | 69041.3 | 112758.9 | 321647.34 | 855589.0 |
| paragraph_count                        | 600 | 126.32   | 481.86   | 1.0   | 4.0   | 11.0   | 20.5    | 79.0     | 206.3   | 448.35   | 1980.46   | 8798.0   |
| numbered_paragraph_count               | 600 | 14.97    | 79.52    | 0.0   | 0.0   | 0.0    | 0.0     | 9.0      | 25.1    | 44.0     | 187.17    | 1369.0   |
| numbered_paragraph_percentage          | 600 | 5.78     | 9.07     | 0.0   | 0.0   | 0.0    | 0.0     | 8.86     | 20.74   | 23.68    | 37.52     | 49.62    |
| citation_occurrence_count              | 600 | 6.57     | 20.48    | 0.0   | 0.0   | 0.0    | 1.0     | 5.0      | 18.0    | 29.0     | 63.24     | 302.0    |
| unique_citation_count                  | 600 | 4.39     | 12.44    | 0.0   | 0.0   | 0.0    | 1.0     | 3.0      | 11.0    | 20.0     | 46.16     | 181.0    |
| legal_reference_count                  | 600 | 40.68    | 126.58   | 0.0   | 0.0   | 1.0    | 9.0     | 33.0     | 84.0    | 153.05   | 451.81    | 1693.0   |
| precedent_relationship_count           | 600 | 10.87    | 21.14    | 0.0   | 0.0   | 0.0    | 4.0     | 11.0     | 29.0    | 43.05    | 136.0     | 184.0    |
| issue_indicator_total                  | 600 | 6.55     | 17.5     | 0.0   | 0.0   | 0.0    | 1.0     | 5.0      | 15.0    | 32.0     | 88.0      | 189.0    |
| citations_per_1000_words               | 600 | 1.14     | 2.22     | 0.0   | 0.0   | 0.0    | 0.07    | 1.19     | 3.53    | 6.07     | 10.11     | 21.37    |
| legal_references_per_1000_words        | 600 | 6.27     | 7.0      | 0.0   | 0.0   | 0.7    | 3.92    | 9.24     | 16.24   | 20.63    | 30.73     | 35.89    |
| precedent_relationships_per_1000_words | 600 | 1.95     | 1.81     | 0.0   | 0.0   | 0.0    | 1.77    | 2.97     | 4.32    | 5.34     | 6.96      | 11.57    |
| issue_indicators_per_1000_words        | 600 | 1.39     | 2.52     | 0.0   | 0.0   | 0.0    | 0.49    | 1.45     | 3.51    | 7.02     | 12.05     | 15.38    |
| metadata_completeness_score            | 600 | 0.97     | 0.06     | 0.75  | 0.88  | 0.88   | 1.0     | 1.0      | 1.0     | 1.0      | 1.0       | 1.0      |

## 3. Document Length Distributions & Bands

| Length Band | Document Count | Percentage |
| :--- | ---: | ---: |
| MEDIUM | 319 | 53.2% |
| VERY_SHORT | 101 | 16.8% |
| SHORT | 79 | 13.2% |
| LONG | 66 | 11.0% |
| EXTREME | 18 | 3.0% |
| VERY_LONG | 17 | 2.8% |


## 4. Citation & Authority Distribution

- **Total Citation Occurrences:** 3,940
- **Total Unique Authorities:** 2,632
- **Mean Citations per 1,000 Words:** 1.14
- **Mean Statutory References per 1,000 Words:** 6.27

## 5. Temporal Characterization

| decision_year | document_count | median_pages | median_words | mean_citations_per_1k | mean_legal_refs_per_1k | excellent_quality_pct |
| ------------- | -------------- | ------------ | ------------ | --------------------- | ---------------------- | --------------------- |
| 2019.0        | 86.0           | 6.0          | 1488.0       | 0.65                  | 4.39                   | 9.3                   |
| 2020.0        | 86.0           | 7.5          | 1912.5       | 0.69                  | 5.57                   | 11.6                  |
| 2021.0        | 86.0           | 10.0         | 2236.5       | 0.72                  | 6.54                   | 14.0                  |
| 2022.0        | 88.0           | 10.5         | 1869.5       | 0.77                  | 6.16                   | 14.8                  |
| 2023.0        | 84.0           | 13.5         | 2584.0       | 1.48                  | 7.95                   | 10.7                  |
| 2024.0        | 85.0           | 10.0         | 2217.0       | 1.6                   | 6.68                   | 7.1                   |
| 2025.0        | 85.0           | 10.0         | 2056.0       | 2.08                  | 6.62                   | 5.9                   |

## 6. Document Anomalies & Forensic Observations

Anomalies represent observable empirical properties rather than deletion criteria:

| anomaly_flag            | count | percentage |
| ----------------------- | ----- | ---------- |
| ZERO_CITATIONS          | 298   | 49.67      |
| NO_SECTION_STRUCTURE    | 138   | 23.0       |
| HIGH_SYMBOL_DENSITY     | 21    | 3.5        |
| CORRUPTED_TEXT_ENCODING | 21    | 3.5        |
| VERY_LONG_TEXT          | 12    | 2.0        |
| VERY_SHORT_TEXT         | 7     | 1.17       |
| MISSING_JUDGE           | 2     | 0.33       |

## 7. RAG Architectural Implications for this Court Level

1. **Bimodal Length Distribution:** High Court texts split between concise dispositive orders (<10 pages) and lengthy statutory reviews (>50 pages). Chunking must adapt dynamically between small single-order chunks and hierarchical trees.
2. **Reporter Diversity:** Diverse citations across SCC, AIR, Cri LJ, and High Court reporters require robust citation normalization.
3. **Court-Level Filtering:** Bombay, Karnataka, Madras, and Delhi exhibit distinctive formatting styles; court code metadata is essential for scoped retrieval.

---
*Generated automatically by Vidhik Corpus Audit Engine.*
