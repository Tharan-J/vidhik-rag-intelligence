# Vidhik Phase 5.2 — Evidence Budget Optimization Experiment

This directory contains the code, data, evaluation pipelines, and formal research reports for the **Vidhik Phase 5.2 Evidence Budget Optimization Experiment**.

## Directory Structure
```
phase5_evidence_budget_optimization/
├── README.md
├── config/
│   └── evidence_budget_config.yaml
├── corpus/
│   ├── candidate_windows.parquet
│   └── candidate_window_embeddings_bge_m3.npy
├── retrieval/
│   ├── sequential_selector.py
│   ├── bm25_selector.py
│   ├── dense_selector.py
│   ├── hybrid_rrf_selector.py
│   ├── mmr_selector.py
│   └── budget_runner.py
├── evaluation/
│   ├── evaluate_fact_coverage.py
│   ├── evaluate_category_coverage.py
│   ├── evaluate_budget_efficiency.py
│   └── evaluate_saturation.py
├── results/
│   ├── evidence_budget_results.parquet
│   ├── evidence_budget_results.csv
│   ├── selected_evidence_manifest.parquet
│   ├── selected_evidence_manifest.csv
│   ├── category_coverage_breakdown.csv
│   ├── saturation_analysis.csv
│   └── oracle_budget_analysis.csv
├── reports/
│   ├── P5_EVIDENCE_INFRASTRUCTURE_AUDIT.md
│   ├── P5_EVIDENCE_BUDGET_TABLES.md
│   └── P5_EVIDENCE_BUDGET_OPTIMIZATION_REPORT.md
└── tests/
    └── test_evidence_budget_optimization.py
```

## Quick Execution
To rerun the entire experimental pipeline and verify all results:
```bash
python3 phase5_evidence_budget_optimization/retrieval/budget_runner.py
python3 phase5_evidence_budget_optimization/generate_reports.py
pytest -v phase5_evidence_budget_optimization/tests/test_evidence_budget_optimization.py
```

## Certified Outcome
- **Final Gate Status:** `EVIDENCE_BUDGET_ESTABLISHED`
- **Recommended Strategy:** BM25 at Budget $B=8$ (80.0% overall recall, 81.6% critical recall, 78.3% legal outcome recall at 1,875 tokens).
- **Automated Tests:** 12/12 passing.
