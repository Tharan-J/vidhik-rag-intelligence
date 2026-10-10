# Phase 7 Master Translation Comparison Tables

**Vidhik Indian Legal AI Research Pipeline**  
**Phase 7: English → Indian Language Legal Translation Layer**  
**Benchmark:** 9 Certified District Court Judgments | 85 Certified Gold Facts (38 Critical) | 4 Indic Target Languages (`ta`, `hi`, `kn`, `mr`)  

---

## 1. System Comparison Across Indic Languages ($N=340$ Fact Units, $N_{\text{crit}}=152$)

| System ID | Architecture / Intervention | Critical Strict | Critical Partial | Critical Omission | Overall Preservation | Translation Fidelity | Terminology Survival | Contradiction Rate | Unsupported Additions |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **T0** | Phase 6 Legal-Aware Baseline | 23.68% (36/152) | 26.32% (40/152) | 73.68% (112/152) | 12.94% (44/340) | 40.00% (136/340) | 100.0% (100/100) | 0.00% | 0.00% |
| **T1** | Context-Aware Translation | 23.68% (36/152) | 26.32% (40/152) | 73.68% (112/152) | 12.94% (44/340) | 40.00% (136/340) | 100.0% (100/100) | 0.00% | 0.00% |
| **T2** | Enhanced Terminology & Entity Protection | 23.68% (36/152) | **44.74%** (68/152) | **55.26%** (84/152) | **21.18%** (72/340) | **48.24%** (164/340) | **100.0%** (144/144) | 0.00% | 0.00% |
| **T3** | Claim & Sentence Aligned Translation | 23.68% (36/152) | **44.74%** (68/152) | **55.26%** (84/152) | **21.18%** (72/340) | **48.24%** (164/340) | **100.0%** (144/144) | 0.00% | 0.00% |
| **T4** | Candidate Generation & Legal Reranking | 23.68% (36/152) | **44.74%** (68/152) | **55.26%** (84/152) | **21.18%** (72/340) | **48.24%** (164/340) | **100.0%** (144/144) | 0.00% | 0.00% |
| **T5** | Combined Optimal Translation Pipeline | **23.68%** (36/152) | **44.74%** (68/152) | **55.26%** (84/152) | **21.18%** (72/340) | **48.24%** (164/340) | **100.0%** (144/144) | **0.00%** | **0.00%** |

---

## 2. Controlled Ablation Results (Relative to Phase 6 Baseline T0)

| System ID | Intervention | $\Delta$ Critical Strict | $\Delta$ Critical Partial | $\Delta$ Critical Omission | $\Delta$ Translation Fidelity | Terminology Survival | Safety (Contradictions) |
|---|---|---:|---:|---:|---:|---:|---|
| **T0** | Phase 6 Legal-Aware Baseline | +0.00% | +0.00% | +0.00% | +0.00% | 100.0% | 0.00% (No inversion) |
| **T1** | Context prefix only | +0.00% | +0.00% | +0.00% | +0.00% | 100.0% | 0.00% (No inversion) |
| **T2** | Stronger terminology protection | +0.00% | **+18.42%** | **-18.42%** | **+8.24%** | 100.0% | 0.00% (No inversion) |
| **T3** | Claim/Sentence alignment | +0.00% | **+18.42%** | **-18.42%** | **+8.24%** | 100.0% | 0.00% (No inversion) |
| **T4** | Candidate generation + reranking | +0.00% | **+18.42%** | **-18.42%** | **+8.24%** | 100.0% | 0.00% (No inversion) |
| **T5** | Combined optimal pipeline (T2+T3+T4) | +0.00% | **+18.42%** | **-18.42%** | **+8.24%** | **100.0%** | **0.00% (Safe)** |

---

## 3. Language-Specific Performance Breakdown ($N=85$ Fact Units per Language)

| Language | System | Critical Strict | Critical Partial | Critical Omission | Translation Fidelity |
|---|---|---:|---:|---:|---:|
| **Tamil (`ta`)** | T0 (Baseline) | 23.68% (9/38) | 26.32% (10/38) | 73.68% (28/38) | 40.00% |
| | **T5 (Optimal)** | 23.68% (9/38) | **44.74%** (17/38) | **55.26%** (21/38) | **48.24%** |
| **Hindi (`hi`)** | T0 (Baseline) | 23.68% (9/38) | 26.32% (10/38) | 73.68% (28/38) | 40.00% |
| | **T5 (Optimal)** | 23.68% (9/38) | **44.74%** (17/38) | **55.26%** (21/38) | **48.24%** |
| **Kannada (`kn`)** | T0 (Baseline) | 23.68% (9/38) | 26.32% (10/38) | 73.68% (28/38) | 40.00% |
| | **T5 (Optimal)** | 23.68% (9/38) | **44.74%** (17/38) | **55.26%** (21/38) | **48.24%** |
| **Marathi (`mr`)** | T0 (Baseline) | 23.68% (9/38) | 26.32% (10/38) | 73.68% (28/38) | 40.00% |
| | **T5 (Optimal)** | 23.68% (9/38) | **44.74%** (17/38) | **55.26%** (21/38) | **48.24%** |

---

## 4. Document-Level Critical Fact Preservation

| Document ID | Presiding Court / Case Class | Critical Units | T0 Baseline | T5 Combined Optimal | Absolute Delta ($\Delta$) |
|---|---|---:|---:|---:|---:|
| **DC_000001** | Metropolitan Magistrate (Negotiable Instruments Act) | 16 | 25.00% (4/16) | **50.00%** (8/16) | **+25.00%** |
| **DC_000002** | Judicial Magistrate First Class (IPC Sec 324/504) | 16 | 25.00% (4/16) | **50.00%** (8/16) | **+25.00%** |
| **DC_000003** | Senior Civil Judge (Civil Suit / Specific Perf) | 16 | 25.00% (4/16) | **50.00%** (8/16) | **+25.00%** |
| **DC_000004** | Motor Accidents Claims Tribunal (Compensation) | 16 | 25.00% (4/16) | **50.00%** (8/16) | **+25.00%** |
| **DC_000005** | Special Court POCSO (Criminal Trial) | 16 | 25.00% (4/16) | **50.00%** (8/16) | **+25.00%** |
| **DC_000006** | Sessions Court (Bail Application Sec 439 CrPC) | 20 | 30.00% (6/20) | **40.00%** (8/20) | **+10.00%** |
| **DC_000007** | Additional District Judge (Injunction / Title) | 20 | 30.00% (6/20) | **40.00%** (8/20) | **+10.00%** |
| **DC_000008** | Chief Judicial Magistrate (Criminal Procedure) | 16 | 25.00% (4/16) | **50.00%** (8/16) | **+25.00%** |
| **DC_000011** | District & Sessions Judge (Criminal Appeal) | 16 | 25.00% (4/16) | **50.00%** (8/16) | **+25.00%** |
