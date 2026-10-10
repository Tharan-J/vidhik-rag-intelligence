# Vidhik Phase 5 — Repaired Multilingual Summarization Experiment

This directory contains the code, data, outputs, evaluations, comparisons, and formal research reports for the **Phase 5 Repaired Summarization Experiment** on the Vidhik District Court benchmark.

## Structure
```
phase5_repaired_summarization/
├── README.md
├── config/
│   └── repaired_run_config.yaml
├── evidence/
│   ├── repaired_bm25_b8_evidence.parquet
│   └── repaired_bm25_b8_evidence.csv
├── outputs/
│   ├── summaries.parquet (45 rows)
│   ├── summaries.csv (45 rows)
│   └── raw/ (45 per-cell JSON records)
├── evaluation/
│   ├── fact_level_evaluation.parquet (425 evaluations)
│   ├── fact_level_evaluation.csv
│   ├── document_level_results.csv (45 rows)
│   ├── language_level_results.csv (5 rows)
│   ├── overall_results.csv
│   └── failure_attribution.csv (306 failure attributions)
├── comparison/
│   ├── old_vs_repaired.csv
│   ├── old_vs_repaired_by_language.csv
│   └── failure_shift.csv
├── audit/
│   ├── run_manifest.json
│   ├── evidence_hash_manifest.csv
│   └── generation_manifest.csv
├── reports/
│   └── PHASE5_REPAIRED_SUMMARIZATION_REPORT.md
└── tests/
    └── test_phase5_repaired_summarization.py
```

## Final Gate Outcome
- **Gate:** `PHASE5_REPAIRED_EVIDENCE_VALIDATED`
- **English Critical Fact Preservation:** 81.6% (vs 57.9% Historical `head(4)`)
- **English Overall Fact Preservation:** 82.4% (vs 52.9% Historical `head(4)`)
- **Retrieval Starvation (R1):** Plummeted by -68.0% (-117 failure instances)
- **Remaining Bottleneck:** R3 Multilingual Generation in 4B-parameter models, motivating Phase 6 IndicTrans2 translation.
- **Automated Tests:** 16/16 Passed.
