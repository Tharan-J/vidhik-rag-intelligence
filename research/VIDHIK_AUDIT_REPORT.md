# Research Audit Report: Vidhik Legal Intelligence System
**Project Title:** Vidhik: Evidence-Centric Multilingual Legal Intelligence for Indian Courts  
**Auditor:** Independent Read-Only Research & Reproducibility Auditor  
**Audit Date:** 2026-10-07  
**Workspace Root:** `/home/tharan/Seeds/vidhik/research`  
**Operating System:** Linux 6.13.0 (Red Hat / Fedora) | Python: 3.14.7  
**Integrity Rule Adherence:** Read-only observational audit; zero source code or dataset modification; deterministic recomputation only.

---

## Executive Summary

1. **Verified Artifacts:** The research corpus comprises 1,361 frozen documents across Supreme Court (600), High Courts (600: 150 each from Bombay, Karnataka, Madras, Delhi), and District Courts (161 across 9 states), with 100% SHA-256 provenance tracking down to 3,593 sentences in District Courts [VERIFIED].
2. **Dense vs. Lexical Retrieval:** On 40 frozen test queries across 733 District Court chunks, BM25 significantly outperformed Dense BGE-M3 (Recall@5: 0.450 vs. 0.225; MRR: 0.250 vs. 0.200) due to exact docket numbers and statutory codes [VERIFIED].
3. **Retrieval Benchmark Leakage:** The 60 retrieval queries (20 calibration, 40 test) were hand-crafted in Python code; 13 test queries (Q_TEST_028–040) explicitly contain the target document ID in their query strings (e.g., "in DC_000010?"), introducing severe leakage [VERIFIED].
4. **Evidence Budget Optimization:** Evaluated budgets B ∈ {2, 4, 6, 8, 10, 15} over 85 certified gold facts across 9 documents; BM25 at B=8 contextual windows achieved 81.58% critical fact recall (31/38) and 80.00% overall recall using 1,875 tokens (~208 tokens/doc) [VERIFIED].
5. **Dual Appearance of ~81.6%:** The figure 81.6% (31/38) appears in two distinct places: (a) BM25 B=8 retrieval recall (31/38 facts retrieved), and (b) Qwen3-4B English Condition C summarization preservation (31/38 facts supported). Cross-tabulation proves these are two separate measurements: Qwen gained 4 unretrieved facts from context while dropping 4 retrieved facts, coincidentally yielding the same 31/38 numerator [VERIFIED].
6. **Zero Contradictions Verified:** Across 425 summarization fact evaluations and 340 translation fact evaluations, 0 contradictory judicial outcomes occurred (0/425 and 0/340 = 0.0%) [VERIFIED].
7. **Entity Protection Guaranteed by Construction:** The reported 100% entity preservation in System D / T5 is guaranteed by construction: 92% of evaluated entities (92/100) were forcibly appended to the translation text in parentheses (`RESTORED_APPENDED`) when omitted by neural translation [VERIFIED].
8. **Collapse of Systems T0–T1 and T3–T5:** In Phase 7 translation outputs, T0 and T1 produced identical texts (36/36 cells, 100%), and T3, T4, and T5 produced identical texts (36/36 cells, 100%) because their code branches assigned or defaulted to the identical text pipeline [VERIFIED].
9. **Doc-Only Claims Unmasked:** Claims in draft READMEs of 68.4%, 76.3%, and 89.5% summarization preservation were doc-only placeholders copied from Phase 5 retrieval tables before models ran; actual Phase 6 Indic model preservation was 7.24% (System B), 21.05% (System C), and 26.32% (System D) [VERIFIED].
10. **Translation Quality Unmeasured:** Standard translation quality metrics (BLEU, chrF, COMET) were never computed anywhere in the repository; only fact-preservation and regex entity matches were evaluated [VERIFIED: NOT FOUND].
11. **Git History Missing:** No git repository was ever initialized in the project directory (`fatal: not a git repository`, 0 commits) [VERIFIED].
12. **Test Suite Hardcoded Paths:** 25 pytest test cases in Phase 6 and Phase 7 fail solely because test scripts hardcode `/home/tharan/Seeds/vidhik` instead of the active subpath `/home/tharan/Seeds/vidhik/research` [VERIFIED].

---

## STEP 0: Project Map

### 0.1 Directory Hierarchy (Depth 3–4, excluding caches/venvs)
```text
/home/tharan/Seeds/vidhik/research
├── district_extraction/
│   ├── config/ (extraction_config.yaml)
│   ├── diagnostics/ (milestone3_selection_report.md)
│   ├── logs/ (diagnostic_execution.log, extraction_execution.log)
│   ├── manifests/ (extraction_manifest_v1.parquet)
│   ├── normalized/ (v1/ [per-document normalized text])
│   ├── ocr_benchmark/ (ocr_benchmark_report.md)
│   ├── quality/ (milestone1_quality_report.md)
│   ├── raw_extraction/ (v1/ [raw native/OCR text files])
│   ├── source_manifest/ (district_source_manifest_v1.parquet)
│   ├── structure/ (milestone5_structure_report.md, v1/ [733 paragraphs, 3,593 sentences])
│   ├── tests/ (test_phase2_extraction.py)
│   ├── validation/ (milestone4_preservation_report.md, legal_entity_preservation.parquet)
│   └── PHASE2_LEGAL_DOCUMENT_EXTRACTION_REPORT.md
├── legal_data/
│   ├── district_court/
│   │   ├── bharat-courts/ (CLI scraper code, tests, docs)
│   │   ├── discovered_s3_pdfs.json (902 MB S3 inventory)
│   │   ├── experiments/ (s3_161/ [161 PDFs, processing_report.md])
│   │   ├── indian-district-court-judgments/ (eCourts mobile API scraper)
│   │   └── stageA1-A4 scripts & reports
│   ├── high_court/
│   │   ├── metadata/ (consolidate_hc_metadata.py, profile scripts)
│   │   ├── pdfs_stage1_candidates/ (4,990 PDFs across 4 HCs)
│   │   ├── text_stage2/ (extracted text samples)
│   │   ├── hc_stage2_final_600.parquet (600 frozen benchmark records)
│   │   └── candidate pool & selection reports (.txt)
│   └── supreme_court/
│       ├── index_cache/ (10 yearly JSON index files 2016-2025)
│       ├── metadata/ (download_sc_shortlist.py, analyze_sc_pdfs.py, selection scripts)
│       ├── pdfs_stage1_candidates/ (2,499 PDFs across 10 years)
│       ├── tar_cache/ (10 yearly TAR archives, 3.43 GB)
│       ├── text_stage2/ (2,499 extracted text files)
│       ├── sc_stage2_core_challenge_600.parquet (600 frozen benchmark records)
│       └── sc_audit.md
├── phase4_summarization/
│   ├── config/ (models.yaml, prompts.yaml, generation.yaml)
│   ├── corpus/ (phase4_documents.parquet, phase4_evidence.parquet, fact_inventory.parquet)
│   ├── generation/ (summaries_v1.parquet [153 summaries], claims_v1.parquet [946 claims])
│   ├── evaluation/ (claim_evaluation.parquet, rouge_scores.parquet)
│   └── reports/ (PHASE4_MULTILINGUAL_SUMMARIZATION_REPORT.md)
├── phase5_evidence_budget_optimization/
│   ├── config/ (budget_config.yaml)
│   ├── evaluation/ (evaluate_fact_coverage.py, evaluate_budget_efficiency.py)
│   ├── reports/ (P5_EVIDENCE_BUDGET_OPTIMIZATION_REPORT.md, P5_EVIDENCE_BUDGET_TABLES.md)
│   ├── results/ (evidence_budget_results.csv, oracle_budget_analysis.csv)
│   └── retrieval/ (bm25_selector.py, dense_selector.py, hybrid_rrf_selector.py, mmr_selector.py)
├── phase5_fact_preservation/
│   ├── claims/ (claims_v1.parquet, claim_fact_alignment_v1.parquet)
│   ├── corpus/ (fact_ledger_v1.parquet [1,089 machine facts], evidence_availability_v1.parquet)
│   ├── generation/ (generation_manifest_v1.parquet [805 runs], summaries/ [805 text files])
│   ├── reports/ (PHASE5_LEGAL_FACT_PRESERVATION_REPORT.md, HUMAN_VALIDATION_REPORT.md)
│   └── validation/ (deterministic_validation.parquet, gemini_validation.parquet, adjudication.parquet)
├── phase5_repaired_summarization/
│   ├── audit/ (run_manifest.json, evidence_hash_manifest.csv)
│   ├── comparison/ (old_vs_repaired.csv, failure_shift.csv)
│   ├── config/ (repaired_run_config.yaml)
│   ├── evaluation/ (fact_level_evaluation.parquet [425 rows], overall_results.csv)
│   ├── evidence/ (repaired_bm25_b8_evidence.parquet [66 selected windows])
│   ├── outputs/ (summaries.parquet [45 repaired summaries], raw/ [45 JSONs])
│   └── reports/ (PHASE5_REPAIRED_SUMMARIZATION_REPORT.md)
├── phase5_retrieval_evaluation/
│   ├── build_retrieval_evaluation.py
│   ├── retrieval_evidence_manifest.parquet
│   ├── retrieval_fact_evaluation.parquet
│   └── reports/ (P5_RETRIEVAL_EVALUATION_REPORT.md)
├── phase5_source_grounded_gold/ (symlinked as phase5_goldset)
│   ├── artifacts/ (gold_facts.parquet [85 certified facts], ambiguous_facts.parquet)
│   └── reports/ (P5_GOLD_FACT_SET_REPORT.md, source_fact_coverage.csv)
├── phase6_audit/
│   ├── artifact_inventory.md, metric_lineage.md, audit_log.md
│   ├── system_pair_comparison.csv, system_row_counts.csv
│   └── corrected_phase6_report.md
├── phase6_multilingual_architecture/
│   ├── config/ (phase6_config.yaml, terminology_config.yaml)
│   ├── evaluation/ (fact_level_evaluation.parquet [2,125 rows], terminology_evaluation.parquet [100 rows], system_comparison.csv)
│   ├── human_validation/ (validation_sample.csv, validation_results.csv [25 rows])
│   ├── inputs/ (frozen_benchmark_manifest.parquet, frozen_evidence_manifest.parquet, frozen_gold_facts.parquet)
│   ├── outputs/ (direct_indic_summaries.parquet, english_summaries.parquet, indictrans2_summaries.parquet, legal_aware_summaries.parquet, verified_summaries.parquet)
│   ├── systems/ (system_d_legal_aware/entity_protection.py, system_e_verified/verifier.py)
│   └── reports/ (PHASE6_MULTILINGUAL_ARCHITECTURE_REPORT.md, PHASE6_COMPARISON_TABLES.md, PHASE6_FAILURE_ANALYSIS.md)
├── phase7_forensic_audit/
│   ├── artifact_inventory.md, audit_log.md
│   ├── output_hash_matrix.csv, language_hash_audit.csv, system_pair_comparison.csv
│   ├── recomputed_metrics.csv, recomputed_system_results.csv
│   ├── tests/ (test_phase7_forensic_audit.py)
│   └── reports/ (PHASE7_FORENSIC_AUDIT_REPORT.md, PHASE7_METRIC_LINEAGE.md)
├── phase7_translation/
│   ├── config/ (translation_config.yaml, model_registry.yaml, terminology_registry.yaml)
│   ├── evaluation/ (evaluate_translation.py)
│   ├── human_validation/ (annotation_schema.md, generate_sample.py, validation_sample.csv)
│   ├── inputs/ (frozen_benchmark_manifest.parquet, frozen_english_summaries.parquet, frozen_evidence_manifest.parquet, frozen_gold_facts.parquet)
│   ├── outputs/ (translations.parquet [216 rows], fact_level_evaluation.parquet [2,040 rows], entity_translation_results.parquet)
│   ├── results/ (system_comparison.csv, language_results.csv, document_results.csv, failure_attribution.csv, ablation_results.csv)
│   ├── translation/ (run_phase7_pipeline.py, translation_runner.py, translation_systems.py)
│   └── reports/ (PHASE7_TRANSLATION_REPORT.md, PHASE7_TRANSLATION_TABLES.md, PHASE7_FAILURE_ANALYSIS.md)
├── rag_experiments/
│   ├── config/ (retrieval.yaml, embeddings.yaml, reranker.yaml, evaluation.yaml)
│   ├── corpus/ (chunks_v1.parquet [733 chunks], chunk_provenance_v1.parquet, chunk_embeddings_bge_m3.npy)
│   ├── evaluation/ (retrieval_metrics.parquet, drm_analysis.parquet, provenance_validation.parquet, error_analysis.md)
│   ├── experiments/ (retrieval_results_v1.parquet [1,600 rows], experiment_summary_v1.json)
│   ├── manifests/ (phase3_manifest_v1.json)
│   ├── queries/ (query_set_v1.jsonl [60 queries], qrels_v1.jsonl [180 judgments], query_metadata_v1.parquet, benchmark_specification_report.md)
│   ├── src/ (bm25_retriever.py, embeddings.py, vector_store.py, reranker.py, evaluation.py)
│   ├── tests/ (test_phase3_rag.py)
│   └── PHASE3_RAG_EXPERIMENT_REPORT.md
├── rag_readiness_audit/
│   ├── combined/ (VIDHIK_FIXED_CORPUS_AUDIT_REPORT.md, hierarchy_summary.csv, metadata_completeness.csv, chunking_feasibility.csv)
│   ├── district_court/ (corpus_summary.csv, yearly_summary.csv, citation_summary.csv, anomaly_report.csv, audit_report.md)
│   ├── high_court/ (corpus_summary.csv, yearly_summary.csv, citation_summary.csv, anomaly_report.csv, audit_report.md, extracted_text/ [600 text files])
│   ├── supreme_court/ (corpus_summary.csv, yearly_summary.csv, citation_summary.csv, anomaly_report.csv, audit_report.md)
│   ├── logs/ (audit_execution.log)
│   └── master_document_audit.parquet (1,361 rows × 60 columns)
├── root_scripts/
│   ├── run_corpus_audit.py, run_experiment.py
│   ├── stage2_1_milestone1.py through stage2_5_milestone5_structure_manifest.py
│   ├── stage3_1_corpus_benchmark_setup.py
│   ├── stage4_1_evidence_preparation.py, stage4_2_generation_ladder.py, stage4_3_verification_evaluation.py
│   └── stage5_1_fact_ledger_prototype.py through stage5_6_scorecards.py
├── PHASE5_BASELINE_AUDIT_REPORT.md
└── tests/ (test_p5_gold_fact_set.py, test_p5_retrieval_evaluation.py)
```

### 0.2 File Classification Summary
- **Main Code Folders:** `district_extraction/`, `rag_experiments/src/`, `phase5_evidence_budget_optimization/retrieval/`, `phase5_repaired_summarization/`, `phase6_multilingual_architecture/systems/`, `phase7_translation/translation/`, `phase7_translation/evaluation/` [VERIFIED].
- **Data Folders:** `legal_data/supreme_court/`, `legal_data/high_court/`, `legal_data/district_court/experiments/s3_161/`, `district_extraction/normalized/v1/`, `district_extraction/raw_extraction/v1/`, `rag_experiments/corpus/` [VERIFIED].
- **Results & Logs Folders:** `rag_readiness_audit/`, `rag_experiments/experiments/`, `rag_experiments/evaluation/`, `phase5_evidence_budget_optimization/results/`, `phase5_repaired_summarization/evaluation/`, `phase6_multilingual_architecture/evaluation/`, `phase7_translation/results/`, `phase7_forensic_audit/` [VERIFIED].
- **Jupyter Notebooks:** Zero notebooks (`*.ipynb`) exist anywhere in the repository [VERIFIED].
- **Config Files:** `rag_experiments/config/`, `phase4_summarization/config/`, `phase5_repaired_summarization/config/`, `phase6_multilingual_architecture/config/`, `phase7_translation/config/`, `.env`, `.env.example` [VERIFIED].
- **Scripts:** 17 root execution scripts (`run_corpus_audit.py`, `run_experiment.py`, `stage2_*.py`, `stage3_*.py`, `stage4_*.py`, `stage5_*.py`) [VERIFIED].

### 0.3 Git History Audit
- **Git Repository Status:** Not a Git repository (`git status` returned code 128: `fatal: not a git repository (or any parent up to mount point /)`) [VERIFIED].
- **Commit Count:** 0 commits [VERIFIED].
- **Date Range / Log:** NOT FOUND (No git VCS initialization has ever taken place in this workspace) [VERIFIED].

### 0.4 Primary Project Documents & Result-Claiming Markdown Files
The master project documents making quantitative claims about corpus properties, retrieval, summarization, and translation are:
1. `rag_readiness_audit/combined/VIDHIK_FIXED_CORPUS_AUDIT_REPORT.md` (Corpus audit across 1,361 documents) [VERIFIED].
2. `district_extraction/PHASE2_LEGAL_DOCUMENT_EXTRACTION_REPORT.md` (Extraction pipeline, OCR benchmarks, provenance on 161 DC documents) [VERIFIED].
3. `rag_experiments/PHASE3_RAG_EXPERIMENT_REPORT.md` (Phase 3 retrieval ladder, BGE-M3 vs BM25) [VERIFIED].
4. `phase4_summarization/reports/PHASE4_MULTILINGUAL_SUMMARIZATION_REPORT.md` (Phase 4 summarization on 31 documents across 5 languages) [VERIFIED].
5. `PHASE5_BASELINE_AUDIT_REPORT.md` (Methodological audit flagging 1,089 unverified candidate facts and denominator errors) [VERIFIED].
6. `phase5_evidence_budget_optimization/reports/P5_EVIDENCE_BUDGET_OPTIMIZATION_REPORT.md` & `P5_EVIDENCE_BUDGET_TABLES.md` (Evidence budget optimization across budgets B=2 to B=15) [VERIFIED].
7. `phase5_source_grounded_gold/reports/P5_GOLD_FACT_SET_REPORT.md` (Certification of 85 gold facts across 9 benchmark documents) [VERIFIED].
8. `phase5_repaired_summarization/reports/PHASE5_REPAIRED_SUMMARIZATION_REPORT.md` (Repaired Qwen3 summarization under BM25 B=8) [VERIFIED].
9. `phase6_audit/corrected_phase6_report.md` (Audit reconciling draft README placeholders vs true model outputs) [VERIFIED].
10. `phase6_multilingual_architecture/reports/PHASE6_MULTILINGUAL_ARCHITECTURE_REPORT.md` (English-first vs direct Indic comparison) [VERIFIED].
11. `phase7_translation/reports/PHASE7_TRANSLATION_REPORT.md` & `PHASE7_TRANSLATION_TABLES.md` (Phase 7 English-to-Indic translation layer) [VERIFIED].
12. `phase7_forensic_audit/reports/PHASE7_FORENSIC_AUDIT_REPORT.md` (Forensic verification of translation hashes and identical systems) [VERIFIED].

---

## STEP 1: Corpus Construction and Auditing

### 1.1 Supreme Court (SC) Corpus Audit
- **Data Source & Acquisition Method:** Obtained via public AWS S3 bucket HTTP API containing annual judgment TAR archives (`english_2016.tar` through `english_2025.tar`, totaling 3.43 GB). Downloaded and extracted by `legal_data/supreme_court/metadata/download_sc_shortlist.py` [VERIFIED: `legal_data/supreme_court/sc_audit.md` lines 20–24].
- **Candidate Pool vs. Frozen Benchmark:** 
  - Total source population indexed: 7,994 judgements (2016–2025) [VERIFIED: `rag_readiness_audit/combined/VIDHIK_FIXED_CORPUS_AUDIT_REPORT.md` line 22].
  - Candidate pool downloaded to disk: 2,499 PDFs and 2,499 extracted `.txt` files [VERIFIED: `legal_data/supreme_court/sc_audit.md` lines 23–27].
  - Final frozen research benchmark: Exactly 600 documents (450 Representative Core + 150 Challenge Set) [VERIFIED: `legal_data/supreme_court/sc_stage2_core_challenge_600.parquet`, shape (600, 112)].
- **Temporal & Language Coverage:** Decision years 2016 to 2025 (10 years). Language: 100% English (`en`) [VERIFIED: `sc_audit.md` line 21].
- **Continuous Metrics (N=600 documents):**
  - Pages: Mean = 31.59, Median = 16.0, Min = 2, Max = 432 [VERIFIED: `rag_readiness_audit/supreme_court/corpus_summary.csv` row 0].
  - Words: Mean = 11,932.90, Median = 5,960.50, Min = 395, Max = 153,506 [VERIFIED: `rag_readiness_audit/supreme_court/corpus_summary.csv` row 1].
  - Paragraphs: Mean = 32.63, Median = 16.0, Max = 432 [VERIFIED: `rag_readiness_audit/supreme_court/corpus_summary.csv` row 3].
  - Numbered Paragraphs: Mean = 3.68, Median = 0.0, Max = 149 (12.0% of paragraphs numbered; 88.5% of docs contain ≥3 numbered paragraphs) [VERIFIED: `rag_readiness_audit/supreme_court/corpus_summary.csv` rows 4–5].
  - Formal Legal Citations: Total occurrences = 26,544; Mean = 44.24/doc (median = 18.0, max = 1,077) [VERIFIED: `rag_readiness_audit/supreme_court/corpus_summary.csv` row 6].
- **Extraction Tools & Quality Validation:** Extracted using PyMuPDF (fitz) in `legal_data/supreme_court/metadata/analyze_sc_pdfs.py`. Extraction error count: 0 errors across 2,499 PDFs [VERIFIED: `legal_data/supreme_court/sc_stage2_extraction_errors.parquet`, 0 rows]. Valid text PDF rate: 99.8% (599/600; 1 file had minimal text) [VERIFIED: `rag_readiness_audit/supreme_court/audit_report.md` line 20].
- **Metadata Completeness:** Mean score = 0.995 (99.5%). Field missingness: `case_id`: 0.7%, `cnr`: 0.0%, `title`: 0.0%, `decision_date`: 0.0%, `court_name`: 0.0%, `judge`: 0.0%, `disposal_nature`: 3.7% [VERIFIED: `rag_readiness_audit/combined/VIDHIK_FIXED_CORPUS_AUDIT_REPORT.md` Section 4]. Deduplication performed on `citation` (the only 100% unique key) [VERIFIED: `legal_data/supreme_court/sc_audit.md` line 39].

### 1.2 High Court (HC) Corpus Audit
- **Data Source & Acquisition Method:** Acquired from official Indian High Court eCourts portals using automated session scraper scripts `legal_data/high_court/download_hc_candidate_pool.py` and `download_hc_metadata.py` [VERIFIED: `legal_data/high_court/consolidate_hc_metadata.py`].
- **Candidate Pool vs. Frozen Benchmark:**
  - Source population frame: 2,382,913 records across 4 High Courts (2019–2025) [VERIFIED: `rag_readiness_audit/combined/VIDHIK_FIXED_CORPUS_AUDIT_REPORT.md` line 23].
  - Candidate pool downloaded to disk: 4,990 PDFs [VERIFIED: `legal_data/high_court/hc_candidate_pool_report.txt` line 12]. Quality exclusions: 5 files. Sampling frame: 4,985 files [VERIFIED: `hc_stage2_selection_report.txt` line 14].
  - Final frozen research benchmark: Exactly 600 documents [VERIFIED: `legal_data/high_court/hc_stage2_final_600.parquet`, shape (600, 48)].
- **Jurisdictional & Temporal Stratification:** Perfectly balanced across 4 High Courts (150 documents each, 25.0%):
  - Court `27_1` (Bombay High Court): 150 documents (25.0%) [VERIFIED: `hc_stage2_selection_report.txt` line 48].
  - Court `29_3` (Karnataka High Court): 150 documents (25.0%) [VERIFIED: `hc_stage2_selection_report.txt` line 49].
  - Court `33_10` (Madras High Court): 150 documents (25.0%) [VERIFIED: `hc_stage2_selection_report.txt` line 50].
  - Court `7_26` (Delhi High Court): 150 documents (25.0%) [VERIFIED: `hc_stage2_selection_report.txt` line 51].
  - Temporal distribution: 2019 (86 docs), 2020 (86), 2021 (86), 2022 (88), 2023 (84), 2024 (85), 2025 (85) across 28 distinct court × year cells [VERIFIED: `hc_stage2_selection_report.txt` Section 6].
- **Continuous Metrics (N=600 documents):**
  - Pages: Mean = 21.88, Median = 10.0, Min = 1, Max = 718 [VERIFIED: `rag_readiness_audit/high_court/corpus_summary.csv` row 0].
  - Words: Mean = 4,999.36, Median = 1,941.50, Min = 29, Max = 133,331 [VERIFIED: `rag_readiness_audit/high_court/corpus_summary.csv` row 1].
  - Paragraphs: Mean = 126.32, Median = 20.50, Max = 8,798 [VERIFIED: `rag_readiness_audit/high_court/corpus_summary.csv` row 3].
  - Numbered Paragraphs: Mean = 14.97, Median = 0.0, Max = 1,369 (5.78% numbered; 72.8% of documents contain numbered paragraphs) [VERIFIED: `rag_readiness_audit/high_court/corpus_summary.csv` rows 4–5].
  - Formal Citations: Mean = 6.57/doc, Median = 1.0, Max = 302 [VERIFIED: `rag_readiness_audit/high_court/corpus_summary.csv` row 6].
- **Extraction Tools & Validation:** High Court source directories lacked raw `.txt` files; extracted dynamically during audit via PyMuPDF into `rag_readiness_audit/high_court/extracted_text/` (600 `.txt` files created) [VERIFIED]. Valid text PDF rate: 100.0% (600/600) [VERIFIED: `rag_readiness_audit/combined/VIDHIK_FIXED_CORPUS_AUDIT_REPORT.md` Section 3]. Scanned PDF rate: 0.8% (5/600) [VERIFIED].
- **Metadata Completeness:** Mean score = 0.968 (96.8%). Field missingness: `case_id`: 0.0%, `cnr`: 0.0%, `title`: 0.0%, `decision_date`: 0.0%, `court_name`: 0.0%, `judge`: 0.3%, `disposal_nature`: 25.3% [VERIFIED: `rag_readiness_audit/combined/VIDHIK_FIXED_CORPUS_AUDIT_REPORT.md` Section 4].

### 1.3 District Court (DC) Corpus Audit
- **Data Source & Acquisition Method:**
  - Macro population: 6,597,794 retained candidate records indexed in Stage A3.5 from eCourts mobile API scraping and S3 bucket crawling (`legal_data/district_court/discovered_s3_pdfs.json`, 902 MB) [VERIFIED: `legal_data/district_court/stageA4_output/A4_sampling_report.md` Section 1].
  - Frozen Experimental Slice (`s3_161`): 161 PDFs downloaded directly from public S3 repository into `legal_data/district_court/experiments/s3_161/orders/` [VERIFIED: `legal_data/district_court/experiments/s3_161/processing_report.md` Section 1]. Download success: 161/161 (100.0%).
- **Jurisdictional & Temporal Distribution (N=161):**
  - State Coverage (9 states): Telangana (18), Andhra Pradesh (18), Karnataka (18), Assam (18), Bihar (18), Punjab (18), Chandigarh (18), Arunachal Pradesh (18), Andaman & Nicobar (17) [VERIFIED: `processing_report.md` Section 2].
  - Decision Years: 1998 (18), 2010 (18), 2020 (18), 2021 (17), 2024 (54), 2025 (36) [VERIFIED: `processing_report.md` Section 3].
  - Languages: English (>98%), with bilingual regional scripts (Telugu, Hindi, Assamese) preserved verbatim [VERIFIED: `district_extraction/PHASE2_LEGAL_DOCUMENT_EXTRACTION_REPORT.md` Section 1].
- **Continuous Metrics (N=161 documents, 324 pages):**
  - Pages: Mean = 2.01, Median = 1.0, Min = 1, Max = 15 [VERIFIED: `rag_readiness_audit/district_court/corpus_summary.csv` row 0].
  - Words: Mean = 344.00, Median = 122.0, Min = 4, Max = 3,440 [VERIFIED: `rag_readiness_audit/district_court/corpus_summary.csv` row 1].
  - Paragraphs: Mean = 9.86, Median = 3.0, Max = 282 (Total paragraphs across corpus = 733) [VERIFIED: `district_extraction/structure/v1/paragraphs_provenance_v1.parquet`, shape (733, 11)].
  - Sentences: Total sentences across corpus = 3,593 [VERIFIED: `district_extraction/structure/v1/sentences_provenance_v1.parquet`, shape (3593, 11)].
  - Numbered Paragraphs: Mean = 0.04/doc (0.28% numbered). 98.1% of records contain zero citations (Mean = 0.04 citations/doc) [VERIFIED: `rag_readiness_audit/district_court/corpus_summary.csv` rows 4–6].
- **Extraction Tools & Routing Pipeline (Phase 2):**
  - Initial Diagnostic Routing: 129 `NATIVE_GOOD` (80.1%), 11 `NATIVE_SUSPICIOUS` (6.8%), 21 `OCR_REQUIRED` (13.0%) [VERIFIED: `district_extraction/quality/milestone1_quality_report.md` Section 1].
  - Primary OCR Tool: RapidOCR (PaddleOCR PP-OCRv4 ONNX). Benchmarked on 15 difficult scanned documents: 90.9% legal entity preservation [VERIFIED: `district_extraction/PHASE2_LEGAL_DOCUMENT_EXTRACTION_REPORT.md` Section 1].
  - Fallback OCR Tool: PyMuPDF-Tesseract 5.x (tessdata: `eng.traineddata`, `osd.traineddata`): 84.0% entity preservation [VERIFIED].
  - Final Extraction Routing: Native extraction = 139 (86.3%), RapidOCR = 17 (10.6%), Tesseract = 5 (3.1%) [VERIFIED: `district_extraction/manifests/extraction_manifest_v1.parquet`].
  - Final Quality Status: 138 `NATIVE_VALID`, 16 `OCR_VALID`, 5 `OCR_FALLBACK_VALID`, 2 `LOW_CONFIDENCE`, 0 `UNRECOVERABLE` [VERIFIED].
- **Page Alignment & Entity Preservation:** Page alignment preservation: 100.0% (324/324 pages) [VERIFIED]. Entity preservation before/after extraction: Case numbers 100%, Dates 100%, Dispositions 100%, Monetary amounts 100%, Statutes 99.5% [VERIFIED: `district_extraction/validation/milestone4_preservation_report.md`].
- **Metadata Missingness:** Severe trial court missingness: `case_id`: 0.0%, `court_name`: 0.0%, `cnr`: 100.0% MISSING, `judge`: 100.0% MISSING, `decision_date`: 100.0% MISSING, `disposal_nature`: 100.0% MISSING [VERIFIED: `rag_readiness_audit/combined/VIDHIK_FIXED_CORPUS_AUDIT_REPORT.md` Section 4].

### 1.4 Cryptographic Provenance Architecture
- **Provenance Chain:** Fully instantiated across Parquet DAG tables:
  $$\text{Sentence ID} \longrightarrow \text{Paragraph ID} \longrightarrow \text{Page Number} \longrightarrow \text{Document ID} \longrightarrow \text{Source PDF SHA-256}$$
- **SHA-256 Computation:** Computed over the raw PDF binary content and raw text files (`hashlib.sha256(open(pdf, 'rb').read()).hexdigest()`) [VERIFIED: `district_extraction/source_manifest/district_source_manifest_v1.parquet`].
- **Provenance Linkage Test:** Validated in `tests/test_p5_retrieval_evaluation.py` and `district_extraction/tests/test_phase2_extraction.py`: 100% of the 3,593 sentences trace to valid paragraphs, valid pages, and unaltered source PDF hashes [VERIFIED].

### 1.5 Privacy, PII, and Licensing Audit
- **PII / Redaction Policy:** NOT FOUND. No PII redaction, anonymization, or party masking was implemented. Real judicial parties (accused, complainants, victims, police witnesses) and judges are fully exposed in plain text in all derived files [VERIFIED].
- **Licensing:** No dataset license was granted by the judicial authorities; records are public domain court orders obtained under public judicial access mechanisms [VERIFIED].

---

## STEP 2: Retrieval Experiments (Dense vs. Lexical)

### 2.1 Inventory of Evaluated Retrieval Configurations
All Phase 3 retrieval experiments were executed across 8 controlled levels (`P3-L0` to `P3-L7`) over the 161 District Court documents index (733 paragraph chunks) [VERIFIED: `rag_experiments/config/retrieval.yaml`, `rag_experiments/PHASE3_RAG_EXPERIMENT_REPORT.md`]:

| Experiment ID | Level & Method | Representation / Model | Chunking Unit | Parameters |
| :--- | :--- | :--- | :--- | :--- |
| `P3-L0-DENSE-V1` | Level 0: Naive Dense Baseline | BAAI/bge-m3 (1024-dim, cls pooling) | Paragraph (733 chunks) | Cosine similarity, Top-k=10 |
| `P3-L1-BM25-V1` | Level 1: BM25 Baseline | rank_bm25 (BM25Okapi) | Paragraph (733 chunks) | $k_1=1.5, b=0.75, \epsilon=0.25$, legal-aware tokenizer |
| `P3-L2-BGE-V1` | Level 2: Dense Full Provenance | BAAI/bge-m3 + Qdrant local | Paragraph (733 chunks) | Cosine similarity + Provenance payload |
| `P3-L3-HYBRID-RRF-V1` | Level 3: Hybrid Retrieval | BM25 + Dense BGE-M3 | Paragraph (733 chunks) | RRF ($k_{rrf}=60, w_{dense}=0.60, w_{bm25}=0.40$) |
| `P3-L4-HYBRID-RERANK-V1` | Level 4: Hybrid + Cross-Encoder | BAAI/bge-reranker-base | Paragraph (733 chunks) | Candidate $k=30$, final $k=10$, max_len=512 |
| `P3-L5-SENTENCE-V1` | Level 5: Unit Ablation (Sentence) | Hybrid RRF | Sentence (3,593 units) | Isolated sentence |
| `P3-L5-SENTENCE-WINDOW-V1`| Level 5: Unit Ablation (Window) | Hybrid RRF | 3-Sentence Window | Overlapping stride=2 |
| `P3-L5-PARAGRAPH-V1` | Level 5: Unit Ablation (Paragraph)| Hybrid RRF | Paragraph (733 units) | Baseline paragraph |
| `P3-L5-PAGE-V1` | Level 5: Unit Ablation (Page) | Hybrid RRF | Full Page (324 units) | Page container |
| `P3-L6-SAC-V1` | Level 6: Summary-Augmented | BM25 + Context Header | Paragraph | Prepended `[COURT:...|DISTRICT:...|CASE:...]` |
| `P3-L7-PROVENANCE-V1` | Level 7: Cryptographic Provenance| Hybrid + Reranker | Paragraph | Cryptographic validation layer |

### 2.2 Benchmark Specification & Ground Truth QRELs
- **Benchmark Name:** Vidhik Phase 3 Retrieval Benchmark [VERIFIED: `rag_experiments/queries/benchmark_specification_report.md`].
- **Index Scope:** 161 District Court documents, 733 paragraph chunks [VERIFIED: `rag_experiments/corpus/chunks_v1.parquet`].
- **Splits:** 60 queries total:
  - Calibration / Dev Split: 20 queries (`Q_CALIB_001` to `Q_CALIB_020`) [VERIFIED].
  - Frozen Test Split: 40 queries (`Q_TEST_001` to `Q_TEST_040`) [VERIFIED: `rag_experiments/queries/query_set_v1.jsonl`].
- **Information Categories:** Case identity (13), Parties (13), Procedural action (11), Dates (8), Statutory provisions (5), Disposition (4), Reasoning (3), Relief (2), Amount value (1) [VERIFIED: `benchmark_specification_report.md` Section 1].
- **QREL Relevance Judgments:** 180 entries in `rag_experiments/queries/qrels_v1.jsonl` graded as:
  - Grade 3 (`EXACT_SUPPORTING_SENTENCE`): Exact target sentence.
  - Grade 2 (`SUPPORTING_PARAGRAPH_CHUNK`): Parent paragraph chunk.
  - Grade 1 (`DOCUMENT_CONTEXT`): Any chunk from the target document.

### 2.3 Benchmark Query Leakage & Bias Analysis [CRITICAL AUDIT FINDING]
Inspection of `stage3_1_corpus_benchmark_setup.py` lines 124–608 uncovers severe methodological bias:
1. **Hand-Crafted Queries with Document Keywords:** Queries were hard-coded in Python scripts by the research developer (`"annotator_id": "legal_research_team_vidhik"`) targeting specific known documents and populated with exact keywords (e.g., `supporting_keywords: ["acquitted", "248(1)", "Cr.P.C."]`).
2. **Explicit Target Document ID in Test Queries:** In the frozen test split, queries `Q_TEST_028` through `Q_TEST_040` (13 out of 40 test queries, 32.5%) literally include the target document ID in their query strings:
   - `Q_TEST_028`: *"What is the case number and court name in DC_000010?"* [VERIFIED: line 508].
   - `Q_TEST_029`: *"What statutory sections or charges are listed in DC_000012?"* [VERIFIED: line 516].
   - `Q_TEST_030`: *"What judicial order was recorded on the docket sheet in DC_000013?"* [VERIFIED: line 524].
   - `Q_TEST_031` through `Q_TEST_040`: Similar formulation for `DC_000014`, `DC_000015`, `DC_000016`, `DC_000017`, `DC_000018`, `DC_000024`, `DC_000038`, `DC_000040`, `DC_000055`, `DC_000073`.
3. **Automated QREL Matching:** Ground truth chunk labels were assigned automatically by checking keyword occurrence: `matches = sum(1 for kw in keywords if re.search(..., s_text))`, falling back to the first sentence if no keyword matched [VERIFIED: lines 637–651].

### 2.4 Complete Retrieval Results Table (Held-Out Test Split, N=40)
Raw values extracted verbatim from `rag_experiments/evaluation/retrieval_metrics.parquet`:

| Experiment ID | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Precision@5 | MRR | nDCG@5 | Latency (ms) | DRM | Prov. Acc |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `P3-L0-DENSE-V1` | 0.150 | 0.225 | **0.225** | 0.375 | 0.045 | 0.1998 | 0.2032 | 14.37 | 0.850 | 1.000 |
| `P3-L1-BM25-V1` | 0.125 | 0.375 | **0.450** | 0.475 | 0.090 | 0.2496 | 0.3008 | 2.74 | 0.875 | 1.000 |
| `P3-L2-BGE-V1` | 0.150 | 0.225 | **0.225** | 0.375 | 0.045 | 0.1998 | 0.2032 | 14.37 | 0.850 | 1.000 |
| `P3-L3-HYBRID-RRF-V1` | 0.175 | 0.350 | **0.350** | 0.450 | 0.070 | 0.2584 | 0.2827 | 24.89 | 0.825 | 1.000 |
| `P3-L4-HYBRID-RERANK-V1` | 0.200 | 0.300 | **0.350** | 0.375 | 0.070 | 0.2488 | 0.2782 | 5631.66 | 0.800 | 1.000 |
| `P3-L5-SENTENCE-V1` | 0.175 | 0.325 | **0.325** | 0.350 | 0.065 | 0.2500 | 0.2812 | - | 0.825 | 1.000 |
| `P3-L5-SENTENCE-WINDOW-V1`| 0.175 | 0.400 | **0.425** | 0.425 | 0.155 | 0.2758 | 0.4988 | - | 0.825 | 1.000 |
| `P3-L5-PARAGRAPH-V1` | 0.125 | 0.375 | **0.450** | 0.475 | 0.090 | 0.2496 | 0.3008 | 2.74 | 0.875 | 1.000 |
| `P3-L5-PAGE-V1` | 0.000 | 0.000 | **0.000** | 0.000 | 0.000 | 0.0000 | 0.0502 | - | 0.850 | 1.000 |
| `P3-L6-SAC-V1` | 0.125 | 0.375 | **0.475** | 0.500 | 0.095 | 0.2599 | 0.3152 | - | 0.875 | 1.000 |
| `P3-L7-PROVENANCE-V1` | 0.175 | 0.300 | **0.350** | 0.375 | 0.070 | 0.2488 | 0.2782 | - | 0.800 | 1.000 |

### 2.5 Verification of Headline Numbers
- **Dense Recall@5 = 0.225 (22.5%):** Directly verified in `rag_experiments/evaluation/retrieval_metrics.parquet` row 0, column `recall@5` = 0.225 (9/40 queries matched in top 5) [VERIFIED].
- **BM25 Recall@5 = 0.450 (45.0%):** Directly verified in `rag_experiments/evaluation/retrieval_metrics.parquet` row 1, column `recall@5` = 0.450 (18/40 queries matched in top 5) [VERIFIED].
- **Recomputation from Raw Results:** Confirmed by re-running deterministic calculation on `retrieval_results_v1.parquet` (1,600 rows): Dense Recall@5 = 9/40 = 0.225; BM25 Recall@5 = 18/40 = 0.450 [RE-COMPUTED].
- **Seeds, Variance & Confidence Intervals:** None found. No random seeds, bootstrapping runs, or confidence intervals were implemented in `run_experiment.py` [VERIFIED: NOT FOUND].

---

## STEP 3: Evidence-Window Evaluation

### 3.1 Assembly Algorithm & Definition of Budget B
- **Assembly Algorithm:** Contextual evidence windows are assembled in `stage4_1_evidence_preparation.py` (lines 60–108). Within each extracted paragraph of each document, sentences are grouped into 3-sentence overlapping windows with a stride of 2 sentences (`range(0, len(sentences), 2)`).
- **Units & Definition of B:** The evidence budget $B$ represents the integer count of top contextual 3-sentence windows supplied per document (e.g., $B=8$ supplies up to 8 windows/doc) [VERIFIED: `phase5_evidence_budget_optimization/config/budget_config.yaml`]. In token units, $B=8$ corresponds to 1,875 total tokens across the 9 benchmark documents (mean ~208 tokens/doc) [VERIFIED: `evidence_budget_results.csv` row 11].

### 3.2 Evaluation of All Tested Budget Values
Evaluated across 9 benchmark documents against the certified 85 source gold facts in `phase5_evidence_budget_optimization/results/evidence_budget_results.csv`:

| Condition ID | Strategy | Budget ($B$) | Total Facts | Critical Recall ($N=38$) | Important Recall ($N=35$) | Contextual Recall ($N=12$) | Outcome Recall ($N=23$) | Overall Recall ($N=85$) | LLM Tokens |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `E0_HISTORICAL` | Historical `head(4)` | 4 | 85 | 63.16% (24/38) | 37.14% (13/35) | 83.33% (10/12) | **8.70% (2/23)** | 55.29% (47/85) | 727 |
| `E1_WHOLE_DOC` | Whole Document | All (117) | 85 | **100.00% (38/38)**| **100.00% (35/35)**| **100.00% (12/12)**| **100.00% (23/23)**| **100.00% (85/85)**| 4,818 |
| `E2_SEQ_B2` | Sequential | 2 | 85 | 31.58% (12/38) | 37.14% (13/35) | 75.00% (9/12) | 4.35% (1/23) | 40.00% (34/85) | 432 |
| `E2_SEQ_B4` | Sequential | 4 | 85 | 63.16% (24/38) | 37.14% (13/35) | 83.33% (10/12) | 8.70% (2/23) | 55.29% (47/85) | 727 |
| `E2_SEQ_B6` | Sequential | 6 | 85 | 81.58% (31/38) | 60.00% (21/35) | 83.33% (10/12) | 47.83% (11/23) | 72.94% (62/85) | 1,252 |
| `E2_SEQ_B8` | Sequential | 8 | 85 | 81.58% (31/38) | 85.71% (30/35) | 83.33% (10/12) | 52.17% (12/23) | 83.53% (71/85) | 2,020 |
| `E2_SEQ_B10` | Sequential | 10 | 85 | 81.58% (31/38) | 85.71% (30/35) | 83.33% (10/12) | 52.17% (12/23) | 83.53% (71/85) | 2,287 |
| `E2_SEQ_B15` | Sequential | 15 | 85 | 84.21% (32/38) | 94.29% (33/35) | 100.00% (12/12) | 69.57% (16/23) | 90.59% (77/85) | 2,889 |
| `E3_BM25_B2` | BM25 | 2 | 85 | 31.58% (12/38) | 14.29% (5/35) | 0.00% (0/12) | 17.39% (4/23) | 20.00% (17/85) | 471 |
| `E3_BM25_B4` | BM25 | 4 | 85 | 65.79% (25/38) | 57.14% (20/35) | 66.67% (8/12) | 56.52% (13/23) | 62.35% (53/85) | 1,114 |
| `E3_BM25_B6` | BM25 | 6 | 85 | 73.68% (28/38) | 77.14% (27/35) | 75.00% (9/12) | 69.57% (16/23) | 75.29% (64/85) | 1,535 |
| `E3_BM25_B8` | BM25 | **8** | **85** | **81.58% (31/38)**| **80.00% (28/35)**| **75.00% (9/12)** | **78.26% (18/23)**| **80.00% (68/85)**| **1,875** |
| `E3_BM25_B10`| BM25 | 10 | 85 | 81.58% (31/38) | 80.00% (28/35) | 75.00% (9/12) | 78.26% (18/23) | 80.00% (68/85) | 1,990 |
| `E3_BM25_B15`| BM25 | 15 | 85 | 89.47% (34/38) | 85.71% (30/35) | 83.33% (10/12) | 91.30% (21/23) | 87.06% (74/85) | 2,675 |
| `E4_DENSE_B8`| Dense BGE-M3 | 8 | 85 | 68.42% (26/38) | 71.43% (25/35) | 66.67% (8/12) | 65.22% (15/23) | 69.41% (59/85) | 1,669 |
| `E5_HYBRID_B8`| Hybrid RRF | 8 | 85 | 76.32% (29/38) | 77.14% (27/35) | 75.00% (9/12) | 65.22% (15/23) | 76.47% (65/85) | 1,829 |

### 3.3 Definition and Certification of "Critical Facts"
- **Authoritative Ground Truth:** Certified in `phase5_source_grounded_gold/artifacts/gold_facts.parquet` (85 facts, SHA-256: `e41e9880baf54fa385be5d095584669aa36d861c27c4805b049f551ea0a09ac9`) [VERIFIED: `P5_GOLD_FACT_SET_REPORT.md` Section 1].
- **Benchmark Scope:** Exactly 9 District Court judgments (`DC_000001` through `DC_000008`, `DC_000011`).
- **Criticality Breakdown:** Exactly 38 Critical facts, 35 Important facts, and 12 Contextual facts [VERIFIED: `gold_facts.parquet`].
- **Definition:** Critical facts encompass operative legal entities essential to the case: Case Number, Parties, Statutory Sections/Charges, Judicial Findings, Dispositions, Relief, and Bail Status.
- **Matching/Recovery Judgment Method:** Recovery was determined deterministically in `evaluate_fact_coverage.py`:
  - Primary check: source sentence ID membership (`sid in all_sids`).
  - Audited exact text fallback: 4 specific fact IDs with verified header/caption text matches.
  - Zero LLM judges were used for retrieval fact coverage evaluation [VERIFIED].

### 3.4 Verification of B=8 Critical Fact Recovery (~81.6%)
- **Raw File:** `phase5_evidence_budget_optimization/results/evidence_budget_results.csv`, row 11 (`condition == 'E3_BM25_B8'`).
- **Numerator:** `critical_retrieved` = 31 [VERIFIED].
- **Denominator:** `critical_count` = 38 [VERIFIED].
- **Exact Fraction:** $31 / 38 = 0.815789... = 81.58\% \approx 81.6\%$ [VERIFIED].

---

## STEP 4: Evidence-Constrained Summarization (Qwen3-4B)

### 4.1 Model Specifications and Inference Runtime
- **Model Name & Tag:** `qwen3-4b-instruct` (Ollama tag: `qwen3:4b-instruct`) [VERIFIED: `phase5_repaired_summarization/config/repaired_run_config.yaml` lines 24–25].
- **Parameter Count & Quantization:** 4.02B parameters, `Q4_K_M` quantization [VERIFIED: `phase4_summarization/config/models.yaml` lines 13–14].
- **Inference Runtime:** Ollama local API (`http://localhost:11434/api/generate`) [VERIFIED: `repaired_run_config.yaml` line 26].
- **Decoding Parameters:** `temperature: 0.1`, `top_p: 0.95`, `max_tokens: 450`, `thinking_enabled: false` (reasoning/thinking tokens explicitly disabled) [VERIFIED: `repaired_run_config.yaml` lines 27–30].
- **Hardware:** CPU / RTX 2050 CUDA [VERIFIED: `models.yaml` line 19].

### 4.2 Benchmark Cohort
9 certified District Court judgments (`DC_000001` through `DC_000008`, `DC_000011`) from the Phase 1 `s3_161` pool [VERIFIED: `repaired_run_config.yaml` lines 10–19].

### 4.3 Fact Preservation and Contradiction Measurement
- **Measurement Method:** Evaluated in Python by `phase5_repaired_summarization/evaluate_repaired_summaries.py` using deterministic lexical rules, multilingual disposition dictionaries (`DISPOSITION_LEXICON`), and regex pattern extractors [VERIFIED].
- **Who Judged:** Deterministic Python rule script; no human judge or NLI neural model was used for Phase 5 repaired scoring [VERIFIED].
- **Contradiction Definition:** An inverted legal outcome in `DISPOSITION` (e.g., summary contains "convicted" / "दोषी" when gold fact is "acquitted" / "बरी") [VERIFIED: lines 130–145].

### 4.4 Verification of 0.0% Contradiction Rate
- **Raw File:** `phase5_repaired_summarization/evaluation/fact_level_evaluation.parquet` (425 evaluation rows: 9 documents × 5 languages × 85 facts).
- **Contradiction Instances:** Exactly 0 rows with status `CONTRADICTED` (0/425 = 0.00%) [VERIFIED].
- **Across Translation Units (Phase 7):** Exactly 0 contradictions out of 340 evaluated units in `phase7_translation/outputs/fact_level_evaluation.parquet` [VERIFIED].

### 4.5 Baseline Comparison in Summarization
- In `phase5_repaired_summarization`, the single active run was `qwen3:4b-instruct` under Condition C with BM25 B=8 (45 summaries) [VERIFIED: `audit/run_manifest.json`]. The baseline was historical `head(4)` from Phase 4/5. NO unconstrained generation baseline, NO full-context baseline, and NO other model architectures were executed inside the repaired phase (`NO UNCONSTRAINED BASELINE FOUND IN PHASE 5 REPAIRED`).
- In Phase 4, baselines included `condition_a` (free-form unconstrained), `condition_b` (structured sections), `ai4bharat/IndicBARTSS`, and `extractive-lead3-baseline` [VERIFIED: `phase4_summarization/reports/PHASE4_MULTILINGUAL_SUMMARIZATION_REPORT.md`].

### 4.6 Resolution of the ~81.6% Dual Appearance [CRITICAL AUDIT FINDING]
The number 81.6% (31/38) appears in two separate stages:
1. **Evidence Budget Optimization (Step 3):** BM25 B=8 retrieval recall of critical facts is $31 / 38 = 81.58\%$.
2. **Repaired Summarization (Step 4):** Qwen3-4B English Condition C summary preservation of critical facts is $31 / 38 = 81.58\%$.

**Determination: TWO SEPARATE MEASUREMENTS that coincidentally share the same fraction (31/38).**  
Cross-tabulation of `retrieval_status_b8` vs `summary_preservation_status` for English critical facts in `phase5_repaired_summarization/evaluation/fact_level_evaluation.parquet` proves this definitively:

| BM25 B=8 Retrieval Status | Summary OMITTED | Summary PARTIAL | Summary SUPPORTED | Total |
| :--- | :---: | :---: | :---: | :---: |
| **NOT_RETRIEVED** | 2 | 1 | **4** | 7 |
| **RETRIEVED** | 2 | 2 | **27** | 31 |
| **Total** | 4 | 3 | **31** | 38 |

- Out of the 31 facts retrieved by BM25 B=8, Qwen preserved 27 (dropping 4: 2 omitted, 2 partial).
- However, Qwen correctly stated 4 critical facts that were marked `NOT_RETRIEVED` in evidence (e.g., inferring from standard procedural headers or dates).
- Consequently, $27 + 4 = 31$ facts were supported in the generated summary.
- The two 81.6% figures represent distinct operational phenomena that happen to sum to the identical integer numerator (31/38) [VERIFIED].

### 4.7 Qualitative Failure Modes & Language Degradation
- **Direct Indic Generation Degradation:** In direct generation with Qwen3-4B, Indic languages suffered catastrophic factual collapse:
  - English: 81.6% critical preservation (31/38) [VERIFIED].
  - Hindi: 23.7% critical preservation (9/38) [VERIFIED].
  - Marathi: 5.3% critical preservation (2/38) [VERIFIED].
  - Tamil: 2.6% critical preservation (1/38) [VERIFIED].
  - Kannada: 2.6% critical preservation (1/38) [VERIFIED].
- **IndicBARTSS Pre-Training Artifacts:** In Phase 4, IndicBARTSS generated Assamese/Bengali tokens (e.g., `<s>শিক্ষিকা`, `উঠিছিল`) and Chinese characters (`境境 ਤੇ 179`) on clean English legal text [VERIFIED: `phase4_summarization/generation/summaries_v1.parquet`].

---

## STEP 5: Multilingual Legal Representation

### 5.1 Architecture & Pipeline Stages
To overcome direct Indic generative failure, Phase 6 and Phase 7 introduced the **English-First Legal-Aware Representation Pipeline**:
1. **English Intermediate Generation:** Qwen3-4B Condition C generates an evidence-grounded English legal summary from BM25 B=8 evidence.
2. **Entity & Terminology Protection:** Regex patterns and dictionary terms detect case numbers, statutes, dates, amounts, dispositions, and bail terms, substituting them with indexed placeholders (`__ENTITY_{idx}__`).
3. **Neural Translation:** IndicTrans2 translates the protected English text into target Indic languages.
4. **Deterministic Restoration:** Placeholders are replaced with controlled glossary translations or verbatim alphanumeric strings. If an entity is omitted by the neural model, it is forcibly appended (`RESTORED_APPENDED`).
5. **Deterministic Validation:** Verification checks for entity survival and contradiction.

### 5.2 Protection Mechanism & Terminology Registry
- **Detection Method:** Pure regular expressions and dictionary lookup [VERIFIED: `phase6_multilingual_architecture/systems/system_d_legal_aware/entity_protection.py`]. No NER model was used.
- **Dictionary Term List Size:** Exactly 7 critical legal terms:
  - 4 Dispositions: `acquitted`, `convicted`, `dismissed`, `allowed` [VERIFIED: `terminology_config.yaml` lines 27–49].
  - 3 Bail Statuses: `bail granted`, `anticipatory bail`, `bail rejected` [VERIFIED: `terminology_config.yaml` lines 50–65].
  - 4 Pattern Categories: Case Numbers, Statutory Sections, Currency Amounts, Dates [VERIFIED].

### 5.3 IndicTrans2 Model Specifications & Tested Languages
- **Model ID:** `ai4bharat/indictrans2-en-indic-dist-200M` (200M parameter distilled model) [VERIFIED: `phase7_translation/config/model_registry.yaml` line 4].
- **Direction & Runtime:** English to Indic (`en-indic`), PyTorch float16, CUDA [VERIFIED: line 9].
- **Decoding:** Beam search with `num_beams: 4`, `max_length: 256` [VERIFIED: lines 18–19].
- **Tested Target Languages:** Tamil (`ta` / `tam_Taml`), Hindi (`hi` / `hin_Deva`), Kannada (`kn` / `kan_Knda`), Marathi (`mr` / `mar_Deva`) [VERIFIED: lines 11–16].

### 5.4 Test Set & Evaluated Units
9 documents × 4 target languages = 36 translation cells per system; 6 systems = 216 translation outputs [VERIFIED: `phase7_translation/outputs/translations.parquet`]. Evaluated universe: 85 gold facts × 4 languages = 340 total fact units per system (152 Critical units per system) [VERIFIED: `phase7_forensic_audit/reports/PHASE7_FORENSIC_AUDIT_REPORT.md` Section 4].

### 5.5 Verification of "100% Terminology Survival" [CRITICAL AUDIT FINDING]
- **Claimed Value:** 100.0% entity preservation across System D / T5 [VERIFIED: `phase6_multilingual_architecture/evaluation/system_comparison.csv`].
- **Raw Evidence:** `phase6_multilingual_architecture/evaluation/terminology_evaluation.parquet` (100 rows).
- **Mechanism Unmasked:** 
  - `RESTORED_APPENDED`: 92 rows (92.0%) [VERIFIED].
  - `PRESENT_VERBATIM`: 8 rows (8.0%) [VERIFIED].
  - `RESTORED` (in-place): 0 rows (0.0%) [VERIFIED].
- **Audit Conclusion: Guaranteed by Construction.** The 100% preservation score is achieved because the code contains a fallback appending missing entities to the end of the text in parentheses (`restored_text += f" ({target})"`) [VERIFIED: `entity_protection.py` line 125]. It is not an empirical measurement of neural model preservation.

### 5.6 Translation Quality (BLEU/chrF/COMET) Audit
- **Standard MT Metrics:** NOT FOUND. Search across the entire codebase confirmed that BLEU, chrF, and COMET were never computed, imported, or referenced [VERIFIED: NOT FOUND].
- **Quality Evaluation:** Only factual preservation against gold facts and human Likert-scale ratings (25 sampled rows in `phase6_multilingual_architecture/human_validation/validation_results.csv`) were evaluated [VERIFIED].

---

## STEP 6: Full Inventory of Built and Measured Features

### 6.1 Classification of Experiments and Features
Every component in the repository is classified into: (a) Executed with saved outputs, (b) Implemented in code but not evaluated, or (c) Planned / doc-only:

| Component / Experiment | Classification | Artifact Path | Core Result / Status |
| :--- | :--- | :--- | :--- |
| **Phase 1 Master Corpus Audit** | Executed with saved outputs | `rag_readiness_audit/master_document_audit.parquet` | 1,361 documents characterized |
| **Phase 2 Document Extraction** | Executed with saved outputs | `district_extraction/manifests/extraction_manifest_v1.parquet` | 161 PDFs extracted (139 Native, 22 OCR) |
| **Phase 3 Retrieval Ladder (L0–L7)**| Executed with saved outputs | `rag_experiments/evaluation/retrieval_metrics.parquet` | BM25 R@5=0.450 vs Dense R@5=0.225 |
| **Phase 4 Multilingual Generation** | Executed with saved outputs | `phase4_summarization/generation/summaries_v1.parquet` | 153 summaries across 5 languages |
| **Phase 5.1 Fact Ledger Baseline** | Executed with saved outputs | `phase5_fact_preservation/corpus/fact_ledger_v1.parquet` | 1,089 candidate facts (flagged in audit) |
| **Phase 5.1 Certified Gold Set** | Executed with saved outputs | `phase5_source_grounded_gold/artifacts/gold_facts.parquet` | 85 certified facts across 9 documents |
| **Phase 5.2 Evidence Budget (B=2..15)**| Executed with saved outputs | `phase5_evidence_budget_optimization/results/` | BM25 B=8 optimal (81.58% critical recall) |
| **Phase 5 Repaired Summarization** | Executed with saved outputs | `phase5_repaired_summarization/outputs/summaries.parquet` | 45 summaries; EN critical pres=81.58% |
| **Phase 6 Direct vs English-First** | Executed with saved outputs | `phase6_multilingual_architecture/evaluation/` | System D achieves 26.32% critical pres. |
| **Phase 7 System T0 (Baseline)** | Executed with saved outputs | `phase7_translation/outputs/translations.parquet` | 26.32% critical preservation (40/152) |
| **Phase 7 System T1 (Context)** | Executed with saved outputs | `phase7_translation/outputs/translations.parquet` | Identical text to T0 (36/36 identical hashes)|
| **Phase 7 System T2 (Enhanced Term)** | Executed with saved outputs | `phase7_translation/outputs/translations.parquet` | 44.74% partial preservation (68/152) |
| **Phase 7 System T3 (Claim-Aligned)**| Executed with saved outputs | `phase7_translation/outputs/translations.parquet` | Identical text to T5 (36/36 identical hashes)|
| **Phase 7 System T4 (Candidate Rerank)**| Executed with saved outputs| `phase7_translation/outputs/translations.parquet` | Identical text to T5 (36/36 identical hashes)|
| **Phase 7 System T5 (Combined Optimal)**| Executed with saved outputs| `phase7_translation/outputs/translations.parquet` | 44.74% partial preservation (68/152) |
| **Tesseract Multilingual (Regional)** | Implemented in code, not evaluated | `stage2_3_milestone3_ocr_execution.py` | Regional traineddata downloaded but unused |
| **Parent-Child Chunk Expansion** | Implemented in code, not evaluated | `rag_experiments/src/evaluation.py` | Flagged in config; no standalone parquet |
| **Bharat-Courts Scraper Pipeline** | Implemented in code, not evaluated | `legal_data/district_court/bharat-courts/` | Working CLI tool, not used in benchmark run |
| **Full 6.5M DC RAG Deployment** | Planned only | `VIDHIK_FIXED_CORPUS_AUDIT_REPORT.md` | Architectural proposal only |

### 6.2 Forensic Audit of Systems T0 through T5
Analysis of `phase7_translation/translation/run_phase7_pipeline.py` lines 82–105 and `phase7_forensic_audit/output_hash_matrix.csv`:
- **T0 vs. T1 Identity:** `t1_text = raw_d` literally assigns the T0 output string to T1. 36 out of 36 document-language cells have identical SHA-256 hashes (100% identity) [VERIFIED].
- **T3 vs. T4 vs. T5 Identity:** 
  - `t3_text = protector.restore(raw_d, reg_t2)`
  - For T4, `sc_d >= sc_c` was true for all 36 cells, setting `t4_base = raw_d`, hence `t4_text = protector.restore(raw_d, reg_t2)`.
  - `t5_text = protector.restore(raw_d, reg_t2)`.
  - Therefore, T3, T4, and T5 produced 100% identical translation texts across all 36 cells [VERIFIED].
- **T2 vs. T5 Distinction:** T2 restores entities over raw translation (`raw_c`), whereas T5 restores them over legal-aware translation (`raw_d`). They share the same preservation rate (44.74%) because the surviving facts are the same 17 protected entities per document [VERIFIED].

### 6.3 Audit of Failure Taxonomy Codes T1 through T13
In `phase7_translation/reports/PHASE7_FAILURE_ANALYSIS.md`, T1–T13 represent the causal failure taxonomy (N=340 units/system):
- **T1 (Source Input Error):** 92 units (27.06%) missing from English intermediate summary.
- **T2 (Entity Corruption):** 24 units (7.06%) in T0; 0 units (0.00%) in T2–T5.
- **T4 (Fact Omission):** 180 units (52.94%) in T0; 176 units (51.76%) in T2–T5.
- **T6 (Contradiction):** 0 units (0.00%) across all systems [VERIFIED].

---

## STEP 7: Reproducibility and Integrity

### 7.1 Reproducibility Matrix

| Phase | Runner Script | Configuration File | Input Data | Output Artifact | Deterministic Command |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Corpus Audit** | `run_corpus_audit.py` | Script variables | `legal_data/` | `rag_readiness_audit/master_document_audit.parquet` | `python3 run_corpus_audit.py` |
| **Extraction** | `stage2_1_milestone1.py` | `extraction_config.yaml` | `s3_161/orders/` | `extraction_manifest_v1.parquet` | `python3 stage2_1_milestone1.py` |
| **Retrieval** | `run_experiment.py` | `retrieval.yaml` | `chunks_v1.parquet` | `retrieval_metrics.parquet` | `python3 run_experiment.py` |
| **Budget Opt** | `budget_runner.py` | `budget_config.yaml` | `gold_facts.parquet` | `evidence_budget_results.csv` | `python3 phase5_evidence_budget_optimization/retrieval/budget_runner.py` |
| **Repaired Sum**| `evaluate_repaired_summaries.py`| `repaired_run_config.yaml` | `summaries.parquet` | `fact_level_evaluation.parquet` | `python3 phase5_repaired_summarization/evaluate_repaired_summaries.py` |
| **Translation** | `run_phase7_pipeline.py` | `translation_config.yaml` | `translation_cache.json`| `fact_level_evaluation.parquet` | `python3 phase7_translation/translation/run_phase7_pipeline.py` |

### 7.2 Software Dependencies and Runtime
- Python: 3.14.7 | OS: Linux 6.13.0 (Red Hat 16.1.1-2).
- Key Libraries: `pandas 3.0.3`, `numpy 2.4.6`, `pymupdf 1.28.2`, `rank-bm25 0.2.2`, `qdrant-client 1.19.1`, `pyarrow 24.0.0` [VERIFIED].
- PyTorch & Transformers: Not installed in active system environment; models executed in separate GPU environments with outputs frozen to caches [VERIFIED].

### 7.3 Integrity & Path Misconfiguration Audit [CRITICAL AUDIT FINDING]
- **Unexecuted Placeholder Numbers in Phase 6 README:** The draft `phase6_multilingual_architecture/README.md` contained placeholder values (68.4%, 76.3%, 89.5%) copied from Phase 5 retrieval tables before models ran. Reconciled in `phase6_audit/corrected_phase6_report.md` [VERIFIED].
- **Pytest Hardcoded Base Paths:** Running `pytest` on `phase6_audit/tests/` and `phase7_forensic_audit/tests/` results in 25 test failures because tests hardcode `BASE_DIR = "/home/tharan/Seeds/vidhik"`, whereas the files are located in `/home/tharan/Seeds/vidhik/research` [VERIFIED].

---

## STEP 8: Comprehensive Consistency Check

### 8.1 Master Headline Number Verification Matrix

| Claimed Number | Claim Location | Raw Artifact Source | Verified Value | Evidence Tag | Audit Finding / Resolution |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **0.225** | `PHASE3_RAG_EXPERIMENT_REPORT.md` | `retrieval_metrics.parquet` | `0.225` | `[VERIFIED]` | Dense Recall@5 (9/40 queries matched). Exact match. |
| **0.450** | `PHASE3_RAG_EXPERIMENT_REPORT.md` | `retrieval_metrics.parquet` | `0.450` | `[VERIFIED]` | BM25 Recall@5 (18/40 queries matched). Exact match. |
| **81.6%** | `P5_EVIDENCE_BUDGET_REPORT.md` | `evidence_budget_results.csv` | `0.8158` (31/38) | `[VERIFIED]` | Critical fact retrieval recall under BM25 B=8. |
| **81.6%** | `PHASE5_REPAIRED_SUMMARIZATION_REPORT.md` | `fact_level_evaluation.parquet` | `0.8158` (31/38) | `[VERIFIED]` | Qwen3 English critical fact preservation. Separate measurement. |
| **0.0%** | `PHASE5_REPAIRED_SUMMARIZATION_REPORT.md` | `fact_level_evaluation.parquet` | `0.0%` (0/425) | `[VERIFIED]` | Zero contradictory judicial outcomes across all 45 summaries. |
| **0.0%** | `PHASE7_TRANSLATION_REPORT.md` | `fact_level_evaluation.parquet` | `0.0%` (0/340) | `[VERIFIED]` | Zero contradictory outcomes across 6 translation systems. |
| **100.0%** | `corrected_phase6_report.md` | `terminology_evaluation.parquet` | `100.0%` (100/100) | `[VERIFIED]` | Guaranteed by construction: 92% appended to text. |
| **100.0%** | `PHASE2_EXTRACTION_REPORT.md` | `sentences_provenance_v1.parquet` | `100.0%` (3593/3593) | `[VERIFIED]` | Sentence-to-PDF SHA-256 cryptographic traceability. |
| **1,361** | `VIDHIK_FIXED_CORPUS_AUDIT_REPORT.md` | `master_document_audit.parquet` | `1,361` | `[VERIFIED]` | 600 SC + 600 HC + 161 DC documents verified on disk. |
| **68.4%** | `phase6_multilingual_architecture/README.md` | `P5_EVIDENCE_BUDGET_TABLES.md` | Conflict (7.24% actual) | `[CONFLICT]` | Unexecuted placeholder copied from Phase 5 retrieval tables. |
| **76.3%** | `phase6_multilingual_architecture/README.md` | `P5_EVIDENCE_BUDGET_TABLES.md` | Conflict (26.32% actual) | `[CONFLICT]` | Unexecuted placeholder copied from Phase 5 retrieval tables. |
| **89.5%** | `phase6_multilingual_architecture/README.md` | `P5_EVIDENCE_BUDGET_TABLES.md` | Conflict (26.32% actual) | `[CONFLICT]` | Unexecuted placeholder copied from Phase 5 retrieval tables. |

---

## Master Experiment Inventory Table

| Experiment / Subsystem | Status | Raw Output Path | Headline Result | Evidence Tag |
| :--- | :--- | :--- | :--- | :---: |
| **Corpus Forensic Audit** | Executed | `rag_readiness_audit/master_document_audit.parquet` | 1,361 documents verified (SC: 600, HC: 600, DC: 161) | `[VERIFIED]` |
| **Phase 2 Document Extraction** | Executed | `district_extraction/manifests/extraction_manifest_v1.parquet` | 139 Native, 22 OCR; 100% page alignment (324 pp) | `[VERIFIED]` |
| **P3-L0 Naive Dense Retrieval** | Executed | `rag_experiments/evaluation/retrieval_metrics.parquet` | Recall@5: 0.225, MRR: 0.200 | `[VERIFIED]` |
| **P3-L1 BM25 Lexical Retrieval** | Executed | `rag_experiments/evaluation/retrieval_metrics.parquet` | Recall@5: 0.450, MRR: 0.250 | `[VERIFIED]` |
| **P3-L3 Hybrid RRF Retrieval** | Executed | `rag_experiments/evaluation/retrieval_metrics.parquet` | Recall@5: 0.350, MRR: 0.258, Recall@1: 0.175 | `[VERIFIED]` |
| **P3-L4 Hybrid + Cross-Encoder** | Executed | `rag_experiments/evaluation/retrieval_metrics.parquet` | Recall@5: 0.350, MRR: 0.249, Latency: 5,631 ms | `[VERIFIED]` |
| **P3-L5 Unit: Sentence Window** | Executed | `rag_experiments/evaluation/retrieval_metrics.parquet` | Recall@5: 0.425, nDCG@5: 0.499, Prec@5: 0.155 | `[VERIFIED]` |
| **P3-L6 Summary-Augmented Chunking**| Executed | `rag_experiments/evaluation/retrieval_metrics.parquet` | Recall@5: 0.475, MRR: 0.260 | `[VERIFIED]` |
| **Phase 4 Multilingual Gen (Qwen3)**| Executed | `phase4_summarization/generation/summaries_v1.parquet` | 82.5% support on EN Condition A; hallucination on B | `[VERIFIED]` |
| **Phase 4 IndicBARTSS Generation** | Executed | `phase4_summarization/generation/summaries_v1.parquet` | Latency 1.29s; vocabulary transfer noise | `[VERIFIED]` |
| **Phase 5.1 Certified Gold Fact Set**| Executed | `phase5_source_grounded_gold/artifacts/gold_facts.parquet` | 85 certified facts across 9 documents | `[VERIFIED]` |
| **Phase 5.2 Evidence Budget (BM25 B=8)**| Executed| `phase5_evidence_budget_optimization/results/evidence_budget_results.csv`| 81.58% critical recall (31/38), 1,875 tokens | `[VERIFIED]` |
| **Phase 5 Repaired Qwen3 EN (B=8)**| Executed | `phase5_repaired_summarization/evaluation/fact_level_evaluation.parquet` | 81.58% critical preservation (31/38), 0.0% contradiction | `[VERIFIED]` |
| **Phase 5 Repaired Qwen3 Indic** | Executed | `phase5_repaired_summarization/evaluation/fact_level_evaluation.parquet` | Severe collapse: HI: 23.7%, MR: 5.3%, TA: 2.6%, KN: 2.6% | `[VERIFIED]` |
| **Phase 6 System B (Direct Indic)** | Executed | `phase6_multilingual_architecture/evaluation/system_comparison.csv` | 7.24% critical preservation, 92.76% omission | `[VERIFIED]` |
| **Phase 6 System C (IndicTrans2)** | Executed | `phase6_multilingual_architecture/evaluation/system_comparison.csv` | 21.05% critical preservation, 78.95% omission | `[VERIFIED]` |
| **Phase 6 System D (Legal-Aware)** | Executed | `phase6_multilingual_architecture/evaluation/system_comparison.csv` | 26.32% critical preservation, 100% entity survival | `[VERIFIED]` |
| **Phase 7 System T0 (Baseline)** | Executed | `phase7_translation/results/system_comparison.csv` | 26.32% critical preservation (40/152) | `[VERIFIED]` |
| **Phase 7 System T1 (Context)** | Executed | `phase7_translation/results/system_comparison.csv` | Identical text to T0 (36/36 identical hashes) | `[VERIFIED]` |
| **Phase 7 System T2 (Enhanced Term)** | Executed | `phase7_translation/results/system_comparison.csv` | 44.74% partial preservation (68/152) | `[VERIFIED]` |
| **Phase 7 System T3 (Claim-Aligned)**| Executed | `phase7_translation/results/system_comparison.csv` | Identical text to T5 (36/36 identical hashes) | `[VERIFIED]` |
| **Phase 7 System T4 (Candidate Rerank)**| Executed| `phase7_translation/results/system_comparison.csv` | Identical text to T5 (36/36 identical hashes) | `[VERIFIED]` |
| **Phase 7 System T5 (Combined Optimal)**| Executed| `phase7_translation/results/system_comparison.csv` | 44.74% partial preservation (68/152) | `[VERIFIED]` |
| **Parent-Child Chunk Retrieval** | Implemented | `rag_experiments/src/evaluation.py` | Configured; no independent evaluation run | `[DOC-ONLY]` |
| **Standard MT Evaluation (BLEU)** | Planned | `phase7_translation/evaluation/` | Zero code or outputs found in repository | `[NOT FOUND]`|

---

## Gaps and Risks Analysis

1. **Benchmark Leakage Risk:** 32.5% of frozen test retrieval queries (`Q_TEST_028`–`040`) explicitly contain the document ID (e.g., "in DC_000010?"). In a 733-chunk index where chunk IDs contain `DC_000010`, lexical matching achieves trivial perfect precision due to target identifier leakage.
2. **Small Benchmark Sample Size:** Phase 5, Phase 6, and Phase 7 evaluations are evaluated on only 9 District Court documents (85 total facts, 38 critical facts). While internally consistent, findings on 9 documents cannot establish generalizability across India's 6.5M trial court corpus.
3. **Appended Entity Artifacts:** The 100% terminology survival score in System D / T5 is artificial; 92% of entities were not preserved in the translated text flow, but appended at the end in parentheses (`RESTORED_APPENDED`). This yields grammatically disfluent text for human readers.
4. **Missing MT Baselines:** No standard machine translation metrics (BLEU, chrF, COMET) were computed. Evaluating translation solely by checking whether case numbers and keywords survive in the text risks obscuring severe grammatical distortion.
5. **Collapsed Evaluation Systems:** Systems T0/T1 and T3/T4/T5 produced identical outputs, meaning claims regarding the benefits of context-aware translation (T1), claim-aligned translation (T3), and legal reranking (T4) are unvalidated empirical duplicates.
6. **No Variance or Statistical Significance Testing:** Zero random seeds, confidence intervals, or permutation tests were run for retrieval or translation evaluations.

---

## Appendices

### Appendix A: Verbatim Prompts and Generation Templates

#### 1. Phase 4 Condition A (Unconstrained Free-Form Generation)
```text
Summarize this court document concisely:

{evidence}

Instruction: {language_instruction}
```

#### 2. Phase 4 Condition B (Structured Legal Summary)
```text
Generate a structured legal summary based on the provided court evidence with the following sections:
- Case Identity
- Parties
- Facts
- Procedural History
- Issues & Arguments
- Court Findings
- Decision / Disposition
- Relief

Evidence:
{evidence}

Instruction: {language_instruction}
```

#### 3. Phase 4 Condition C & Phase 5 Repaired Summarization Prompt
```text
You are an expert legal summarizer. Generate an evidence-grounded legal summary in {language} following these strict rules:
1. Use ONLY the supplied legal evidence.
2. Do NOT invent, assume, or hallucinate facts, dates, amounts, or names.
3. Preserve exact case numbers, party names, statutory sections, dates, and court dispositions.
4. If a fact (such as CNR, Judge Name, or specific section) is missing from the evidence, explicitly state '[Not Available in Evidence]'.
5. Never convert uncertainty into certainty. Do not alter the legal outcome.
6. Preserve legal meaning faithfully in {language}.

VERIFIED EVIDENCE:
{evidence_text}

EVIDENCE-CONSTRAINED SUMMARY IN {language}:
```

#### 4. Phase 4 Translation Baseline Prompt
```text
Translate the following English legal summary faithfully into {target_language}:

{english_summary_text}
```

---

### Appendix B: Key Configuration Files

#### 1. BM25 & Retrieval Configuration (`rag_experiments/config/retrieval.yaml`)
```yaml
pipeline_version: "1.0.0"
corpus_name: "district_court_s3_161"

bm25:
  k1: 1.5
  b: 0.75
  epsilon: 0.25
  tokenizer: "legal_aware"
  lowercase: true

dense:
  top_k_default: 10
  score_threshold: 0.0

hybrid:
  fusion_method: "rrf"
  rrf_k: 60
  dense_weight: 0.6
  bm25_weight: 0.4
```

#### 2. IndicTrans2 Runtime Registry (`phase7_translation/config/model_registry.yaml`)
```yaml
model:
  name: "IndicTrans2 Distilled 200M"
  hf_model_id: "ai4bharat/indictrans2-en-indic-dist-200M"
  tokenizer: "ai4bharat/indictrans2-en-indic-dist-200M"
  framework: "HuggingFace Transformers (Seq2SeqLM)"
  processor: "IndicTransToolkit.IndicProcessor"
  torch_dtype: "float16"
  device: "cuda"

languages:
  en: "eng_Latn"
  ta: "tam_Taml"
  hi: "hin_Deva"
  kn: "kan_Knda"
  mr: "mar_Deva"

decoding_parameters:
  num_beams: 4
  max_length: 256
  min_length: 0
  use_cache: false
```

---

### Appendix C: Raw Result Tables (Trimmed)

#### 1. Phase 5 Repaired Summarization Results by Language
Source: `phase5_repaired_summarization/evaluation/language_level_results.csv`

| language | total_facts | critical_facts | supported | partially_supported | omitted | critical_preservation | critical_omission | overall_preservation | legal_outcome_preservation |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **en** | 85 | 38 | 70 | 7 | 8 | **81.58%** | 10.53% | **82.35%** | **73.91%** |
| **hi** | 85 | 38 | 15 | 6 | 64 | **23.68%** | 71.05% | **17.65%** | **13.04%** |
| **kn** | 85 | 38 | 1 | 4 | 80 | **2.63%** | 94.74% | **1.18%** | **0.00%** |
| **mr** | 85 | 38 | 5 | 4 | 76 | **5.26%** | 92.11% | **5.88%** | **0.00%** |
| **ta** | 85 | 38 | 3 | 4 | 78 | **2.63%** | 94.74% | **3.53%** | **4.35%** |

#### 2. Phase 7 System Comparison Evaluation Matrix
Source: `phase7_translation/results/system_comparison.csv`

| system_id | system_name | critical_strict | critical_partial | critical_omission | overall_pres | translation_fidelity | terminology_survival | contradiction | unsupported_addition |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **T0_BASELINE_LEGAL_AWARE** | Phase 6 Legal Baseline | 23.68% | 26.32% | 73.68% | 12.94% | 40.00% | 100.00% | 0.00% | 0.00% |
| **T1_CONTEXT_AWARE** | Context-Aware | 23.68% | 26.32% | 73.68% | 12.94% | 40.00% | 100.00% | 0.00% | 0.00% |
| **T2_STRONGER_TERMINOLOGY**| Enhanced Terminology | 23.68% | 44.74% | 55.26% | 21.18% | 48.24% | 100.00% | 0.00% | 0.00% |
| **T3_CLAIM_ALIGNED** | Claim-Aligned | 23.68% | 44.74% | 55.26% | 21.18% | 48.24% | 100.00% | 0.00% | 0.00% |
| **T4_CANDIDATE_RERANKING** | Candidate Reranking | 23.68% | 44.74% | 55.26% | 21.18% | 48.24% | 100.00% | 0.00% | 0.00% |
| **T5_COMBINED_OPTIMAL** | Combined Optimal | 23.68% | 44.74% | 55.26% | 21.18% | 48.24% | 100.00% | 0.00% | 0.00% |

---

### Appendix D: Sample Outputs and Failure Cases

#### 1. Phase 3 Retrieval Hit vs Failure Example
- **Query `Q_TEST_001`:** *"Who is the father of accused I.V.Sreedhar Reddy contractor from Gospadu village?"* (Target: `DC_000021`)
  - **BM25 Hit (Rank 1):** Retrieved `CHK_DC_000021_P001_PAR001` containing text: *"I.V.Sreedhar Reddy, S/o V.Sivereddy, 32 years, Contractor, resident of Deebaguntla village, Gospadu Mandal..."* (Relevance Grade 3).
  - **Dense BGE-M3 (Rank 2):** Placed target chunk at Rank 2, ranking a generic calendar order from `DC_000020` at Rank 1.
- **Query `Q_TEST_005` (Lexical Failure / Abbreviation):** *"Under what section was the accused examined on 19.12.13 after trial closure?"*
  - **BM25 Failure:** Missed Rank 1 hit because document text contained the OCR mis-scan `3i3 Cr.P.C` instead of `313 Cr.P.C.`.
  - **Dense BGE-M3:** Overcame typographical OCR error, scoring top semantic similarity.

#### 2. Phase 5 Repaired English Summary (`DC_000001`, Qwen3-4B Condition C)
```text
Legal Summary:

The case between the State of Telangana, through the Sub-Inspector of Police, Srirampur (Complainant), and Bodduna Rajamallu (Accused), was suo-moto advanced and transferred by the District and Sessions Judge, Adilabad, vide Proc.Dis.No.5555/2017/Admn dated 3.8.2017, to the Junior Civil Judge, Mancherial.

The case is presently before the Junior Civil Judge at Chennur, Sri Uday Bhaskar Rao, CC.

The court order was executed and recorded under the hand and seal of the Junior Civil Judge, Chennur, on the 8th day of August, 2017.

The case is referenced under Section 179 of the Code of Criminal Procedure, 1998.

[Note: The specific nature of the offense or the factual details of the case are not available in the provided evidence.]
```

#### 3. Direct Indic Generative Failure (`DC_000001`, Qwen3-4B Tamil Condition C)
```text
இந்த செய்தியை நிரூபிக்கும் காலாவலம் மற்றும் சட்ட விவரங்கள் பின்வருமாறு:

இந்த வழக்கு செய்தியை செய்தியாக முன்னுரைக்கப்பட்டது. அதன் பொருளாக அதிகாரி பொது மாவட்ட மற்றும் செயல்முறை நீதிபதி அடிலாபத்தின் நிர்வாக நிர்வாக அறிவிப்பு எண் 5555/2017/Admn, 3.8.2017 அன்று வழங்கப்பட்டது. இது வழக்கை இ.ஏ. ஜி. மாங்கரே...
```
*(Failure Mode: Distorted case identity, missing docket numbers, and fragmented legal clauses).*

#### 4. IndicBARTSS Vocabulary Transfer Artifact (`DC_000001`, Phase 4)
```text
<s>শিক্ষিকা [Evidence 1 | Page 1]: IN THE COURT OF THE JUNIOR CIVIL JUDGE AT CHENNUR Present: Sri Uday Bhaskar Rao Junior Civil Judge, Chennur. CC. [Evidence 2 | Page 1]: No. [Evidence 3 | Page 1]: 179 [Evidence 4 | Page 1]: of 1998境境 ਤੇ 1998 [Evidence 4 | Page 1
```
*(Failure Mode: Hallucinated Bengali word `শিক্ষিকা` ("female teacher"), Chinese characters `境境`, and Punjabi token `ਤੇ`).*

#### 5. Phase 7 System T5 English-First Translation with Appended Restorations (`DC_000001`, Tamil)
```text
சட்டப்பூர்வ சுருக்கம்ஃ ஆதில் _ மன்சைன் _ ஒய் தேதியிட்ட தெலுங்கானா சிவில் வழக்கு _ மன்சைன் _ ஒய் வழக்கு ராஜமைன் மாநில போலீசாருக்கும் ராஜமைன் மாநில நீதிபதிக்கும் இடையேயான புகார் மூலம் இடமாற்றம் செய்யப்பட்டது, இது ஜூனியர்-செஷன்ஸ், போதிராபாத், ஜூனியர் செஷன்ஸ், (வீடியோ), ஜூனியர் செஷன்ஸ், போதிராபாத், ஜூனியர் செஷன்ஸ், போதிராபாத், (வீடியோ) க்கு மாற்றப்பட்டது. உதய் பாஸ்கர் தற்போது சி. சி. என், ஜூனியர், ஸ்ரீ சென்னூரில் உள்ள சிவில் நீதிபதி முன் வழக்குத் தொடர்கிறார். 2017 ஆம் ஆண்டு சிவில் முத்திரை நிறைவேற்றப்பட்டது மற்றும் ஆகஸ்ட் 8 ஆம் தேதி சென்னை ஜூனியர் நீதிமன்றத்தின் ஆணையின் கீழ் பதிவு செய்யப்பட்டது. 1998 _ குறிப்பிடப்படாத வழக்கு ENURET, DURET. [வழங்கப்பட்ட குறிப்பு குறிப்பிட்ட சான்றுகள் அல்லஃ குற்றத்தின் தன்மை அல்லது வழக்கில் உள்ள உண்மை விவரங்கள்]. (3.8.2017) (Section 179 of the Code of Criminal Procedure)
```
*(Failure Mode: Note the verbatim strings `(3.8.2017) (Section 179 of the Code of Criminal Procedure)` forcibly appended at the end in parentheses due to status `RESTORED_APPENDED`).*

---
*End of Vidhik Research Audit Report.*
