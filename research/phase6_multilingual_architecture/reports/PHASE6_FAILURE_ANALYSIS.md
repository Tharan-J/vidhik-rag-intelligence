# Phase 6 Failure Analysis & Causal Attribution Report

## 1. Causal Attribution Framework (R1 - R8)

Every fact evaluation unit is mapped to exactly one causal failure stage:
- **R1_RETRIEVAL_FAILURE**: Fact absent from frozen BM25 B=8 evidence windows.
- **R2_ENGLISH_GENERATION_FAILURE**: Fact present in evidence but omitted/incorrect in English intermediate summary.
- **R3_DIRECT_INDIC_GENERATION_FAILURE**: Fact present in English, but direct Indic Qwen3 fails.
- **R4_TRANSLATION_FAILURE**: Fact present in English, but IndicTrans2 translation omits or contradicts it.
- **R5_LEGAL_TERMINOLOGY_FAILURE**: General sentence translated, but legal entity/term damaged.
- **R6_SOURCE_AMBIGUITY**: Source text itself is genuinely ambiguous.
- **R7_EVALUATOR_DISAGREEMENT**: Evaluator disagreement.
- **R8_OTHER**: Other residual failure.

## 2. Failure Distribution by Architecture (Pooled 425 Units Per System)

| System | Total Units | NONE (Supported) | R1 Retrieval | R2 English Gen | R3 Direct Indic | R4 Translation | R5 Terminology |
|---|---:|---:|---:|---:|---:|---:|---:|
| Direct Indic Qwen3 | 425 | 72 (16.9%) | 95 (22.4%) | 20 (4.7%) | 238 (56.0%) | 0 (0.0%) | 0 (0.0%) |
| IndicTrans2 Raw | 425 | 94 (22.1%) | 95 (22.4%) | 20 (4.7%) | 0 (0.0%) | 204 (48.0%) | 12 (2.8%) |
| Legal-Aware Translation | 425 | 98 (23.1%) | 95 (22.4%) | 20 (4.7%) | 0 (0.0%) | 204 (48.0%) | 0 (0.0%) |
| Legal-Aware + Verification | 425 | 98 (23.1%) | 95 (22.4%) | 20 (4.7%) | 0 (0.0%) | 204 (48.0%) | 0 (0.0%) |
