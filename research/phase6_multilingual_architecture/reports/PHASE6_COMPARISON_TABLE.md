# Phase 6 Multilingual Architecture Comparison Tables

**Vidhik Research Pipeline — Controlled Empirical Comparison**

## 1. Required Final System Comparison Table (Section 26)

| System | Language | Overall | Critical | Critical Omission | Disposition | Statutory | Legal Outcome | Contradiction |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Direct Qwen3 | Tamil | 3.5% | 2.6% | 97.4% | 0.0% | 0.0% | 0.0% | 0.0% |
| IndicTrans2 Raw | Tamil | 9.4% | 21.1% | 79.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Legal-aware | Tamil | 12.9% | 26.3% | 73.7% | 33.3% | 0.0% | 16.7% | 0.0% |
| Direct Qwen3 | Hindi | 10.6% | 18.4% | 81.6% | 0.0% | 0.0% | 0.0% | 0.0% |
| IndicTrans2 Raw | Hindi | 9.4% | 21.1% | 79.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Legal-aware | Hindi | 12.9% | 26.3% | 73.7% | 33.3% | 0.0% | 16.7% | 0.0% |
| Direct Qwen3 | Kannada | 2.4% | 2.6% | 97.4% | 0.0% | 0.0% | 0.0% | 0.0% |
| IndicTrans2 Raw | Kannada | 9.4% | 21.1% | 79.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Legal-aware | Kannada | 12.9% | 26.3% | 73.7% | 33.3% | 0.0% | 16.7% | 0.0% |
| Direct Qwen3 | Marathi | 4.7% | 5.3% | 94.7% | 0.0% | 0.0% | 0.0% | 0.0% |
| IndicTrans2 Raw | Marathi | 9.4% | 21.1% | 79.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Legal-aware | Marathi | 12.9% | 26.3% | 73.7% | 33.3% | 0.0% | 16.7% | 0.0% |

## 2. Indic Aggregate Comparison (Pooled Across Tamil, Hindi, Kannada, Marathi)

| Architecture | Indic Overall | Indic Critical | Indic Omission | Indic Disposition | Indic Statutory | Translation Fidelity | Evaluation Units |
|---|---:|---:|---:|---:|---:|---:|---:|
| Direct Indic Qwen3 (Baseline) | 5.3% | 7.2% | 92.8% | 0.0% | 0.0% | 32.4% | 340 |
| English -> IndicTrans2 Raw | 9.4% | 21.1% | 79.0% | 0.0% | 0.0% | 36.5% | 340 |
| Legal-Aware Translation | 12.9% | 26.3% | 73.7% | 33.3% | 0.0% | 40.0% | 340 |
| Legal-Aware + Verification | 12.9% | 26.3% | 73.7% | 33.3% | 0.0% | 40.0% | 340 |

## 3. English Intermediate Source Performance (System A)

| System | Language | Overall | Critical | Critical Omission | Disposition | Statutory | Legal Outcome |
|---|---|---:|---:|---:|---:|---:|---:|
| English Control (BM25 B=8) | English | 72.9% | 81.6% | 18.4% | 66.7% | 0.0% | 66.7% |
