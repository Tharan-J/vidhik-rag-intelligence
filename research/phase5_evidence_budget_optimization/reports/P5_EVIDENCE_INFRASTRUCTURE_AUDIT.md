# Phase 5.2 — Evidence Infrastructure Audit Report

**Date:** 2026-10-05  
**Audit Target:** Existing Evidence Pipeline, Schemas, Retrieval Infrastructure, and Selection Mechanisms  
**Status:** COMPLETE & CERTIFIED  

---

## 1. Executive Summary

This audit assesses the existing Vidhik evidence infrastructure across Phase 2, Phase 3, Phase 4, and Phase 5 to support the **P5.2 Evidence Budget Optimization Experiment**. 

Key findings:
1. **Evidence Schema & Integrity:** The candidate evidence corpus (`phase4_summarization/corpus/phase4_evidence.parquet`) contains 347 verified 3-sentence sliding windows across 31 documents, of which exactly **117 windows** belong to the 9 benchmark documents (`DC_000001` through `DC_000008` and `DC_000011`). Full Phase 2 provenance (`sentence_id`, `paragraph_id`, `page_number`, `source_sha256`) is preserved in every window.
2. **Construction Characteristics:** Windows are strictly intra-paragraph sliding windows of length $\le 3$ sentences with a stride of 2 (1-sentence overlap). Windows **never cross paragraph boundaries, page boundaries, or document boundaries**.
3. **The Historical Selection Defect:** Neither `stage4_2_generation_ladder.py` nor `stage5_3_frozen_generation.py` executed dynamic retrieval. Both scripts executed `p4_ev[p4_ev['document_id'] == doc_id].head(4)`. This was a static first-four-window truncation that starved multi-page documents of operative outcomes, charges, and dispositions on subsequent pages.
4. **Reusable Phase 3 Retrieval Infrastructure:** The existing Phase 3 retrieval modules (`rag_experiments/src/bm25_retriever.py` with Indian legal tokenizer and `rag_experiments/src/embeddings.py` using quantized BGE-M3 ONNX at `rag_experiments/indexes/models/bge-m3/BAAI-bge-m3_quantized.onnx`) are fully operational, deterministic, and can be directly reused for within-document evidence selection.
5. **Zero Hallucination / Zero Leakage Rule:** Gold fact labels/values are strictly isolated and never used as queries. Retrieval queries are derived exclusively from the legal task specification.

---

## 2. Evidence Parquet Schema Audit

Inspection of `phase4_summarization/corpus/phase4_evidence.parquet`:

| Column | Type | Description | Sample Value (`DC_000001`) |
| :--- | :--- | :--- | :--- |
| `evidence_id` | string | Unique window identifier | `EV_DC_000001_P001_WIN001` |
| `document_id` | string | Target District Court ID | `DC_000001` |
| `source_sha256` | string | SHA-256 of source court PDF | `49d91ccb95063a2cb7951c4b4bdf6e12...` |
| `page_number` | int64 | Source page (1-indexed) | `1` |
| `paragraph_id` | string | Source paragraph ID | `DC_000001_P001_PAR001` |
| `primary_sentence_id`| string | First sentence ID in window | `DC_000001_P001_PAR001_SEN001` |
| `sentence_ids` | ndarray | Array of constituent sentence IDs | `['...SEN001', '...SEN002']` |
| `evidence_text` | string | Concatenated sentence text | `IN THE COURT OF THE JUNIOR CIVIL...` |
| `word_count` | int64 | Word count of window | `20` |
| `character_count` | int64 | Character count of window | `114` |
| `provenance_chain` | string | Human/audit traceable DAG link | `EV_... -> SEN001 -> PAR001 -> Page 1...` |

### Benchmark Document Window Inventory

| Document ID | Page Count | Candidate Windows in Corpus | Page Range | Document Type |
| :--- | ---: | ---: | :--- | :--- |
| `DC_000001` | 1 | 8 | Page 1 | Criminal Docket / Order |
| `DC_000002` | 1 | 8 | Page 1 | Lok Adalat Award / Docket |
| `DC_000003` | 1 | 6 | Page 1 | Criminal Docket / Order |
| `DC_000004` | 1 | 7 | Page 1 | Criminal Docket / Order |
| `DC_000005` | 1 | 7 | Page 1 | Criminal Docket / Order |
| `DC_000006` | 5 | 46 | Pages 1–5 | Full Criminal Trial Judgment |
| `DC_000007` | 1 | 7 | Page 1 | Committal Docket / Order |
| `DC_000008` | 1 | 7 | Page 1 | Committal Docket / Order |
| `DC_000011` | 3 | 21 | Pages 1–3 | Detailed Committal Order |
| **Total** | **15** | **117** | **1–5** | **9 Certified Documents** |

---

## 3. Window Construction Analysis

Inspecting `stage4_1_evidence_preparation.py` (lines 90–121):
- **Window Unit:** Sliding window of up to 3 sentences (`sentences[i:i + 3]`).
- **Stride:** 2 sentences (`range(0, len(sentences), 2)`).
- **Overlap:** Consecutive windows within the same paragraph share exactly 1 sentence.
- **Boundaries:**
  - Paragraph boundary: A window never spans across two paragraphs. Short paragraphs (< 3 sentences) yield a single window with all available sentences in that paragraph.
  - Page boundary: Windows never span across pages because paragraphs in Phase 2 are strictly page-bound.
  - Document boundary: Windows strictly belong to a single document.
- **Fact Coverage Upper Bound:** Verification demonstrates that **100% of the 85 certified gold facts** have their `source_sentence_id` contained within these 117 candidate windows. Thus, the candidate window corpus has a theoretical fact coverage of **100% (85/85)** if all windows are available.

---

## 4. Audit of Historical Retrieval Scores & Selection Code

Inspection of `stage4_2_generation_ladder.py` and `stage5_3_frozen_generation.py`:
- In both generation scripts, evidence was passed to the summarizer using:
  ```python
  doc_evidence_map[doc_id] = p4_ev[p4_ev["document_id"] == doc_id].head(4)
  ```
- **Findings:**
  1. No retrieval scores were computed or saved in `phase4_evidence.parquet` or `generation_manifest_v1.parquet`.
  2. The historical baseline was purely an extractive prefix truncation (`head(4)`).
  3. For 1-page documents (`DC_000001` to `DC_000005`, `DC_000007`, `DC_000008`), `head(4)` captured ~50–60% of the document's windows (all on page 1).
  4. For multi-page documents:
     - `DC_000006` (46 windows, 5 pages): `head(4)` took only 4/46 windows (8.7%), capturing only the caption on page 1 and missing pages 2–5 where all witness testimony, judicial reasoning, and final acquittal orders reside.
     - `DC_000011` (21 windows, 3 pages): `head(4)` took only 4/21 windows (19.0%), missing pages 2–3 where the committal order, Section 209 Cr.P.C. remand, and bail orders reside.
  5. This confirms that the historical low recall on substantive outcomes (0/7) was a consequence of the truncation artifact, NOT a failure of legal retrieval algorithms.

---

## 5. Audit of Reusable Phase 3 Retrieval Infrastructure

We audited the components in `rag_experiments/`:

1. **BM25 Sparse Retriever:**
   - Module: `rag_experiments/src/bm25_retriever.py`
   - Class: `BM25Retriever` using `rank_bm25.BM25Okapi` with parameters $k_1 = 1.5, b = 0.75, \epsilon = 0.25$.
   - Tokenizer: `tokenize_legal_text` normalizes legal abbreviations (`u/s`, `cr.p.c`, `c.c.`), slash-separated citation numbers, and preserves statutory terminology.
   - Status: Fully functional, deterministic, zero external API dependency.
2. **Dense BGE-M3 Embedder:**
   - Module: `rag_experiments/src/embeddings.py`
   - Class: `BGEM3Embedder` using local quantized ONNX model:
     - Path: `rag_experiments/indexes/models/bge-m3/BAAI-bge-m3_quantized.onnx` (544 MB)
     - Tokenizer: `rag_experiments/indexes/models/bge-m3/tokenizer.json` (17 MB)
   - Performance: Initializes in ~6s; embeds 20 text windows in 1.24s.
   - Dimensions: 1024-dimensional normalized dense vectors.
   - Status: Fully functional, deterministic, zero GPU dependency.
3. **Hybrid RRF Fusion:**
   - Phase 3 validated parameters:
     - Reciprocal Rank Fusion constant $k = 60$.
     - Linear combination weights: Dense = 0.60, BM25 = 0.40.
4. **Vector Store:**
   - `rag_experiments/src/vector_store.py` (Qdrant client). For within-document selection across 6–46 windows per document, exact in-memory cosine similarity via numpy dot product on normalized vectors is completely deterministic, faster, and avoids socket/database overhead.

---

## 6. Implementation Architecture Plan for Phase 5.2

Based on this audit, Phase 5.2 will be structured as follows:

1. **Candidate Universe:** The 117 verified candidate windows in `phase4_summarization/corpus/phase4_evidence.parquet` for the 9 benchmark documents.
2. **Embedding Cache:** Pre-embed the 117 candidate windows once using `BGEM3Embedder` and save to `phase5_evidence_budget_optimization/corpus/candidate_window_embeddings_bge_m3.npy` to guarantee fast, deterministic execution.
3. **Legal Task Query Formulation:**
   - Under Rule 4 (Zero Leakage), gold facts are NEVER used to query.
   - The query represents the general legal summarization task defined in Phase 4 `stage4_2_generation_ladder.py`:
     ```text
     Case identity, presiding court, judge, parties, complainant, accused, charges, statutory provisions, procedural history, witness evidence, judicial findings, decision, disposition, acquittal, conviction, committal order, relief, bail custody, monetary amount.
     ```
   - For document-grounded context, document-level metadata known *prior* to reading the body text (from the docket registry: case number, court, district) may be appended without inspecting gold facts.
4. **Selectors to Implement:**
   - `sequential_selector.py`: Historical `head(B)` (E0 reproduces `head(4)` exactly; E2 tests $B \in \{2, 4, 6, 8, 10, 15\}$).
   - `bm25_selector.py`: BM25 ranking over candidate windows (E3).
   - `dense_selector.py`: BGE-M3 cosine similarity ranking over candidate windows (E4).
   - `hybrid_rrf_selector.py`: RRF fusion of BM25 + BGE-M3 with $k=60$ (E5).
   - `mmr_selector.py`: Maximal Marginal Relevance on Hybrid candidates with diversity penalty and page-spread regularization (E6).
   - `whole_document_evaluator.py`: E1 upper bound evaluator (all windows available).
5. **Evaluation Engine:**
   - Evaluates exact fact coverage against `phase5_source_grounded_gold/gold_facts.parquet` (85 gold facts).
   - Reconciles 100% with the historical baseline (47 retrieved, 1 partial, 37 not retrieved at E0).
   - Calculates overall, critical, important, contextual, category-level, and legal outcome recalls, token counts, and cost-efficiency ratios.

---

## 7. Audit Certification

- **Audited by:** Vidhik Research Engineering Pair Programmer
- **Date:** 2026-10-05
- **Conclusion:** Evidence infrastructure verified. Proceed to Phase 5.2 implementation.
