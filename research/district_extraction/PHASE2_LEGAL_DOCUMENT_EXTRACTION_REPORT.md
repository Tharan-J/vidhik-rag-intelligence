# Vidhik Phase 2 — Legal Document Extraction Master Forensic Report
**Project:** Multilingual Legal Summarizer Tool for District e-Court Service  
**Phase:** Phase 2 — Legal Document Extraction  
**Status:** COMPLETED & VALIDATED  
**Date:** October 2, 2026  
**Corpus:** Frozen District Court Experimental Sample (`s3_161`, 161 documents, 324 pages)  
**Corpus Integrity:** 100% Bit-Exact SHA-256 Match (Zero modifications, zero deletions, zero rebalancing)

---

## Executive Summary

Phase 2 constructed an auditable, deterministic, provenance-preserving extraction and normalization pipeline for the 161 frozen District Court legal documents collected in Phase 1. 

Adhering strictly to the master principle:
> *"The source corpus is immutable. Phase 2 creates a derived, reproducible, provenance-preserving extraction representation."*

All original PDFs and raw extraction texts remain frozen and unedited. Every derived representation is versioned, fully measured, and accompanied by automated forensic validation.

### Key Pipeline Outcomes

| Metric / Stage | Result | Audit Confirmation |
| :--- | :--- | :--- |
| **Source Corpus Size** | 161 PDFs (324 pages) | 100% Bit-exact SHA-256 integrity across all files |
| **Initial PDF Routing** | 129 `NATIVE_GOOD`, 11 `NATIVE_SUSPICIOUS`, 21 `OCR_REQUIRED` | Diagnostic pass completed before extraction |
| **Primary OCR Candidate** | **RapidOCR (PaddleOCR PP-OCRv4 ONNX)** | Benchmarked on 15 difficult cases (90.9% legal entity preservation) |
| **Fallback OCR Candidate** | **PyMuPDF-Tesseract 5.x** | Retained for edge-case fallback (84.0% legal entity preservation) |
| **Final Extraction Selection** | **Native**: 139 (86.3%), **PaddleOCR**: 17 (10.6%), **Tesseract**: 5 (3.1%) | Multi-signal selection scoring (zero word-count bias) |
| **Final Quality Status** | **138** `NATIVE_VALID`, **16** `OCR_VALID`, **5** `OCR_FALLBACK_VALID`, **2** `LOW_CONFIDENCE`, **0** `UNRECOVERABLE` | All 161 documents successfully accounted for |
| **Script Distribution** | Latin (English): >98%, Regional bilingual scripts preserved | Zero synthetic translation or transliteration |
| **Page Alignment Preservation** | **100.0%** (324/324 pages) | Page boundaries preserved through native, OCR, and normalized text |
| **Legal Entity Preservation** | **Case Numbers**: 100%, **Dates**: 100%, **Dispositions**: 100%, **Amounts**: 100%, **Statutes**: 99.5% | 148/161 (91.9%) zero-change; remaining 13 had formatting fixes |
| **Provenance Chain** | **733 Paragraphs**, **3,593 Sentences** | Complete hierarchy: Sentence → Paragraph → Page → Document → Source SHA |
| **Automated Test Suite** | **12/12 Tests Passing** (`pytest`) | Source integrity, page preservation, provenance, routing, and schema |

---

## 1. Pipeline Architecture (Sub-Stages 2.1 – 2.14)

The pipeline executes strictly according to the non-negotiable architecture principle:

```text
Frozen Source PDF (legal_data/district_court/experiments/s3_161/orders/)
      │
      ▼
2.1 Source Manifest (SHA-256, page counts, metadata)
      │
      ▼
2.2 Diagnostics & Routing (Text layer, symbol density, whitespace)
      │
      ├── NATIVE_GOOD (129 docs) ──────┐
      │                                │
      ├── NATIVE_SUSPICIOUS (11 docs) ─┼── 2.3 Native Text Extraction
      │                                │       │
      └── OCR_REQUIRED (21 docs) ──────┤       ▼
                                       ├── 2.4 Extraction Quality Assessment
                                       │       │
                                       └── 2.5 OCR Routing Decision
                                               │
                                               ├── Clean Native ──► Native Extraction
                                               │
                                               └── Poor/Image ──► 2.6 & 2.7 OCR Execution
                                                                      ├── PaddleOCR (Primary)
                                                                      └── Tesseract (Fallback)
                                                                            │
      ┌─────────────────────────────────────────────────────────────────────┘
      ▼
2.8 Extraction Selection (Multi-signal scoring: coverage, cleanliness, entities)
      │
      ▼
2.9 Conservative Normalization (CRLF→LF, NFKC Unicode, line-break hyphen repair)
      │
      ▼
2.10 Raw-vs-Normalized Comparison & 2.11 Legal-Sensitive Preservation Checks
      │
      ▼
2.12 Legal Structure Reconstruction & 2.13 Provenance Construction
      │   (Document → Page → Paragraph → Sentence hierarchy)
      │
      ▼
2.14 Final Phase-2 Dataset Manifest & Automated Validation
```

---

## 2. Sub-Stage Details & Verification

### 2.1 Source Manifest (`district_extraction/source_manifest/`)
- **Artifact:** `district_source_manifest_v1.parquet` (161 records).
- Computes SHA-256 hash, file size, page count, and extracts un-inferred embedded PDF metadata for all 161 District Court documents.
- The SHA-256 hash forms the immutable primary key for provenance tracking throughout all future phases.

### 2.2 & 2.5 PDF Diagnostics & Routing (`district_extraction/diagnostics/`)
- **Artifacts:** `pdf_diagnostics_v1.parquet`, `routing_decisions_v1.parquet`.
- Evaluates text coverage, symbol ratio, character distribution, and image-only pages.
- **Routing Decisions:**
  - `NATIVE_GOOD`: 129 documents (80.1%) — High word count, low symbol density, valid text layer.
  - `NATIVE_SUSPICIOUS`: 11 documents (6.8%) — Short text or minor encoding anomalies requiring post-extraction verification.
  - `OCR_REQUIRED`: 21 documents (13.0%) — Empty text layer, pure scanned images, or severe font corruption.

### 2.3 & 2.4 Native Text Extraction & Quality Assessment
- **Artifacts:** `district_extraction/raw_extraction/native/` (161 page-delimited files), `native_extraction_pages_v1.parquet` (324 pages), `district_extraction/quality/extraction_quality_v1.parquet`.
- Native extraction preserved deterministic page boundaries (`--- PAGE {n} ---`).
- Detected that 14 scanned/image-only PDFs had 0 native words, while genuine short docket orders (e.g. Assam court orders with 20–27 words) were cleanly preserved.

### 2.6 & 2.7 OCR Benchmark & Execution (`district_extraction/ocr_benchmark/`)
- **Artifacts:** `benchmark_results.json`, `ocr_benchmark_report.md`, raw benchmark outputs in `paddleocr/` and `tesseract/`.
- Benchmarked 15 representative difficult cases (image-only scans, font corruptions, faint scans, docket sheets).
- **Benchmark Metrics:**
  - **PaddleOCR (RapidOCR PP-OCRv4 ONNX):** 
    - Mean Quality Score: 0.7246
    - Mean Legal Entities Detected: 9.47
    - Legal Entity Preservation Rate: **90.9%**
    - Won: **12 / 15 documents**
  - **Tesseract 5.x (PyMuPDF C++ Engine):**
    - Mean Quality Score: 0.7119
    - Mean Legal Entities Detected: 8.53
    - Legal Entity Preservation Rate: 84.0%
    - Won: 3 / 15 documents
- **Conclusion:** PaddleOCR was selected as the **Primary OCR Engine** due to superior legal entity preservation (especially party names and statutory sections). Tesseract was retained as the deterministic **Baseline/Fallback Engine**.

### 2.8 Extraction Selection (`district_extraction/diagnostics/`)
- **Artifacts:** `extraction_selection_v1.parquet`, `extraction_selection_v1.json`, `district_extraction/raw_extraction/selected/` (161 files), `final_raw_pages_v1.parquet` (324 pages).
- Deterministic multi-signal selection formula:
  $$\text{Score} = 0.30 \cdot \text{Coverage} + 0.35 \cdot \text{Cleanliness} + 0.35 \cdot \text{Legal Entity Score}$$
- **Final Selected Extraction Methods:**
  - **Native (`PyMuPDF-Native`):** 139 documents (86.3%)
  - **PaddleOCR (`RapidOCR-PP-OCRv4`):** 17 documents (10.6%)
  - **Tesseract (`PyMuPDF-Tesseract`):** 5 documents (3.1%)
- **Quality Tiers:**
  - `NATIVE_VALID`: 138 documents
  - `OCR_VALID`: 16 documents
  - `OCR_FALLBACK_VALID`: 5 documents
  - `LOW_CONFIDENCE`: 2 documents (retained; zero dropped)
  - `UNRECOVERABLE`: 0 documents

### 2.9, 2.10 & 2.11 Conservative Normalization & Legal Preservation Audit
- **Artifacts:** `district_extraction/normalized/v1/` (161 files), `raw_normalized_comparison.parquet`, `legal_entity_preservation.parquet`, `milestone4_preservation_report.md`.
- Normalization operations strictly avoided paraphrasing, summarizing, translating, or hallucinating.
- **Operations:**
  - CRLF $\rightarrow$ LF, Unicode normalization (NFKC: 159,024 chars), whitespace normalization (4,486 instances), hyphenation repairs across line wraps (28 instances).
  - Page markers (`--- PAGE {n} ---`) 100.0% preserved.
- **Legal Entity Preservation Results:**
  - **Case Numbers:** 524 / 524 (**100.0%**)
  - **Dates:** 764 / 764 (**100.0%**)
  - **Dispositions (Order Terms):** 183 / 183 (**100.0%**)
  - **Monetary Amounts:** 98 / 98 (**100.0%**)
  - **Statutory Sections:** 183 / 184 (**99.5%**)
  - **Zero-Change Preservation:** 148 / 161 (91.9%) documents had identical entity sets before and after normalization. The remaining 13 documents had formatting improvements (e.g. hyphenated statutory sections re-joined).

### 2.12 & 2.13 Legal Structure Reconstruction & Provenance
- **Artifacts:** 
  - 161 structured JSON files: `district_extraction/structure/v1/{doc_id}.json`
  - High-speed columnar tables:
    - `district_extraction/structure/v1/paragraphs_provenance_v1.parquet` (733 rows)
    - `district_extraction/structure/v1/sentences_provenance_v1.parquet` (3,593 rows)
- Reconstructed hierarchical structure:
  $$\text{Document} \longrightarrow \text{Page} \longrightarrow \text{Paragraph} \longrightarrow \text{Sentence}$$
- **Provenance IDs:**
  - Document: `{document_id}` (e.g. `DC_000021`)
  - Page: `{page_number}` (1-indexed)
  - Paragraph: `{document_id}_P{page:03d}_PAR{par:03d}` (e.g. `DC_000021_P001_PAR001`)
  - Sentence: `{paragraph_id}_SEN{sen:03d}` (e.g. `DC_000021_P001_PAR001_SEN005`)
- Every record maintains a direct cryptographic link to `source_sha256`.

### 2.14 Final Manifest & Automated Testing
- **Artifacts:** `district_extraction/manifests/extraction_manifest_v1.json`, `extraction_manifest_v1.parquet`, `district_extraction/tests/test_phase2_extraction.py`.
- **Test Results:** 12 passed in 0.81s (`pytest`):
  1. `test_source_corpus_count_is_frozen`: PASSED
  2. `test_source_corpus_sha256_unaltered`: PASSED
  3. `test_page_preservation_across_all_documents`: PASSED
  4. `test_total_corpus_page_count`: PASSED
  5. `test_paragraph_provenance_format_and_linking`: PASSED
  6. `test_sentence_provenance_format_and_linking`: PASSED
  7. `test_raw_extraction_remains_intact`: PASSED
  8. `test_normalized_pages_marker_preservation`: PASSED
  9. `test_routing_edge_cases`: PASSED
  10. `test_ocr_benchmark_artifact_validity`: PASSED
  11. `test_final_manifest_consistency`: PASSED
  12. `test_structured_json_schema`: PASSED

---

## 3. Directory Layout & Artifact Map

```text
district_extraction/
│
├── config/
│   ├── extraction.yaml
│   ├── ocr.yaml
│   ├── normalization.yaml
│   └── quality.yaml
│
├── source_manifest/
│   └── district_source_manifest_v1.parquet (161 docs, SHA-256)
│
├── diagnostics/
│   ├── pdf_diagnostics_v1.parquet
│   ├── routing_decisions_v1.parquet
│   ├── extraction_selection_v1.parquet
│   ├── extraction_selection_v1.json
│   └── milestone3_selection_report.md
│
├── raw_extraction/
│   ├── native/ (161 raw text files)
│   ├── native_extraction_pages_v1.parquet (324 pages)
│   ├── selected/ (161 raw text files from selected extractors)
│   └── final_raw_pages_v1.parquet (324 pages)
│
├── ocr_benchmark/
│   ├── reference/ (15 reference texts)
│   ├── paddleocr/ (15 PaddleOCR benchmark outputs)
│   ├── tesseract/ (15 Tesseract benchmark outputs)
│   ├── benchmark_results.json
│   └── ocr_benchmark_report.md
│
├── normalized/
│   └── v1/ (161 normalized text files with page markers)
│
├── validation/
│   ├── raw_normalized_comparison.parquet
│   ├── raw_normalized_comparison.csv
│   ├── legal_entity_preservation.parquet
│   ├── legal_entity_preservation.csv
│   └── milestone4_preservation_report.md
│
├── structure/
│   ├── milestone5_structure_report.md
│   └── v1/
│       ├── DC_000001.json ... DC_000161.json (161 structured JSONs)
│       ├── paragraphs_provenance_v1.parquet (733 paragraphs)
│       └── sentences_provenance_v1.parquet (3,593 sentences)
│
├── manifests/
│   ├── extraction_manifest_v1.json
│   └── extraction_manifest_v1.parquet
│
└── tests/
    └── test_phase2_extraction.py (Automated pytest suite)
```

---

## 4. Phase-2 Acceptance Criteria Compliance Matrix

| Criterion (Section 24) | Status | Evidence / Location |
| :--- | :---: | :--- |
| 1. All 161 source PDFs have immutable hashes | **PASS** | `source_manifest/district_source_manifest_v1.parquet`, tested via SHA check |
| 2. Every document has a diagnostic record | **PASS** | `diagnostics/pdf_diagnostics_v1.parquet` (161 rows) |
| 3. Every document has a deterministic extraction route | **PASS** | `diagnostics/routing_decisions_v1.parquet` (161 rows) |
| 4. Native extraction attempted where appropriate | **PASS** | `raw_extraction/native/` and `native_extraction_pages_v1.parquet` |
| 5. OCR used only where routing/quality assessment requires it | **PASS** | Only 32 docs processed; 129 clean native docs bypassed OCR |
| 6. OCR alternatives benchmarked on representative subset | **PASS** | 15 difficult cases evaluated across PaddleOCR and Tesseract |
| 7. Selected OCR engine supported by measured evidence | **PASS** | PaddleOCR won 12/15 docs with 90.9% legal entity preservation |
| 8. Raw extraction preserved | **PASS** | `raw_extraction/selected/` and `final_raw_pages_v1.parquet` |
| 9. Normalized extraction stored separately | **PASS** | `normalized/v1/` contains distinct, derived normalized files |
| 10. Raw-vs-normalized changes measurable | **PASS** | `validation/raw_normalized_comparison.parquet` |
| 11. Page provenance preserved | **PASS** | 100% page count match (324/324 pages) across all formats |
| 12. Paragraph provenance preserved where available | **PASS** | 733 paragraphs in `structure/v1/paragraphs_provenance_v1.parquet` |
| 13. Legal-sensitive fields checked for preservation | **PASS** | `validation/legal_entity_preservation.parquet` (100% docket/date preservation) |
| 14. Missing metadata represented as missing | **PASS** | No hallucinated CNR/judge data; missing fields stored as null/omitted |
| 15. Extraction failures explicitly recorded | **PASS** | Quality tiers assigned to all 161 docs; zero silently dropped |
| 16. No source document modified or removed | **PASS** | `legal_data/district_court/experiments/s3_161/` 100% unchanged |
| 17. Complete Phase-2 extraction manifest generated | **PASS** | `manifests/extraction_manifest_v1.json` & `.parquet` |
| 18. Consumable directly by Phase 3 RAG | **PASS** | Page-, paragraph-, and sentence-level columnar tables ready for chunking/indexing |

---

## 5. Handover to Phase 3 (RAG / Evidence Retrieval Experiments)

The pipeline is now ready for **Phase 3 — RAG / Evidence Retrieval Experiments**.

Phase 3 can directly ingest:
1. `district_extraction/structure/v1/paragraphs_provenance_v1.parquet` (for paragraph-level chunks), or
2. `district_extraction/structure/v1/sentences_provenance_v1.parquet` (for sentence-window or hybrid retrieval), or
3. `district_extraction/structure/v1/{doc_id}.json` (for hierarchical document retrieval).

Every retrieved piece of text in Phase 3 will carry its full provenance chain:
$$\text{Evidence Chunk} \longrightarrow \text{Paragraph ID} \longrightarrow \text{Page Number} \longrightarrow \text{Document ID} \longrightarrow \text{Source SHA-256}$$

This ensures full auditability and paves the way for strict legal fact preservation validation in Phase 5.
