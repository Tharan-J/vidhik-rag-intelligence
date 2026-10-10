"use client";

import React from "react";
import { SectionHeading } from "../shared/SectionHeading";
import { MetricCard } from "../shared/MetricCard";
import {
  Database,
  BarChart2,
  FileCheck2,
  Languages,
  CheckCircle,
  AlertTriangle,
  Info,
} from "lucide-react";

export function ResearchMetrics() {
  return (
    <section
      id="research-metrics"
      style={{
        padding: "5.5rem 2rem",
        backgroundColor: "var(--bg-surface)",
        borderTop: "1px solid var(--border-rule)",
        borderBottom: "1px solid var(--border-rule)",
      }}
      aria-label="Research and Experimentation Credibility"
    >
      <div style={{ maxWidth: "1280px", margin: "0 auto" }}>
        <SectionHeading
          badge="VALIDATED RESEARCH EXPERIMENTS"
          title="Empirical rigor. Not marketing claims."
          subtitle="Vidhik is built on documented, audited experiments across Indian court records. We publish verifiable metrics evaluated against frozen benchmark corpora rather than unverifiable generative assertions."
          align="center"
        />

        {/* 4 Core Metric Cards Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "1.75rem",
            marginBottom: "3.5rem",
          }}
          className="metrics-grid"
        >
          <MetricCard
            value="1,361"
            label="Verified Research Docs"
            description="Verified frozen research/demo corpus spanning 600 Supreme Court, 600 High Court, and 161 District Court judgments."
            benchmarkContext="Verified frozen research corpus"
          />

          <MetricCard
            value="0.450"
            label="BM25 Recall@5"
            description="Tested District Court benchmark: BM25 (0.450) vs tested dense baseline (0.225). Hybrid retrieval secures legal facts."
            benchmarkContext="Benchmark-specific retrieval test"
          />

          <MetricCard
            value="81.6%"
            label="Critical Facts Recovered"
            description="With an eight-window evidence budget, 81.6% of essential case facts were recovered in the audited District Court suite."
            benchmarkContext="District Court fact recovery audit"
          />

          <MetricCard
            value="0%"
            label="Evidence Contradiction"
            description="0% contradiction against provided evidence in the audited benchmark summarization evaluations."
            benchmarkContext="Audited summarization benchmark"
          />
        </div>

        {/* In-Depth Validated Pipelines Breakdown (2 Columns) */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "2.5rem",
          }}
          className="research-breakdown-grid"
        >
          {/* Deep Dive 1: District Court Processing Pipeline */}
          <div
            className="paper-card"
            style={{
              padding: "2rem",
              backgroundColor: "var(--bg-sheet)",
              borderRadius: "3px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.6rem",
                  marginBottom: "1rem",
                }}
              >
                <Database size={18} color="var(--maroon)" />
                <h3
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.25rem",
                    fontWeight: 700,
                    color: "var(--text-ink)",
                  }}
                >
                  District Court Document Processing
                </h3>
              </div>

              <p
                style={{
                  fontFamily: "var(--font-sans)",
                  fontSize: "0.88rem",
                  lineHeight: 1.6,
                  color: "var(--text-muted)",
                  marginBottom: "1.5rem",
                }}
              >
                District court judgments present extreme formatting diversity, scan degradation,
                and complex regional legal syntax. Our validated processing pipeline maps every
                record down to atomic sentence units with cryptographic integrity:
              </p>

              {/* Breakdown stats */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, 1fr)",
                  gap: "1rem",
                  backgroundColor: "var(--bg-parchment)",
                  padding: "1.25rem",
                  borderRadius: "2px",
                  border: "1px solid var(--border-subtle)",
                  marginBottom: "1.25rem",
                }}
              >
                <div>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "1.3rem",
                      fontWeight: 700,
                      color: "var(--navy)",
                    }}
                  >
                    161
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-faint)" }}>
                    District Court Judgments
                  </div>
                </div>

                <div>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "1.3rem",
                      fontWeight: 700,
                      color: "var(--navy)",
                    }}
                  >
                    324
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-faint)" }}>
                    Verified Pages Processed
                  </div>
                </div>

                <div>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "1.3rem",
                      fontWeight: 700,
                      color: "var(--maroon)",
                    }}
                  >
                    733
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-faint)" }}>
                    Indexed Paragraphs
                  </div>
                </div>

                <div>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "1.3rem",
                      fontWeight: 700,
                      color: "var(--maroon)",
                    }}
                  >
                    3,593
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-faint)" }}>
                    Sentences Relinked
                  </div>
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  fontSize: "0.8rem",
                  color: "var(--navy)",
                  fontWeight: 500,
                }}
              >
                <CheckCircle size={14} color="var(--maroon)" />
                <span>
                  Maintains page → paragraph → sentence relationships & cryptographic linkage to source PDFs.
                </span>
              </div>
            </div>

            <div
              style={{
                marginTop: "1.5rem",
                paddingTop: "0.85rem",
                borderTop: "1px solid var(--border-subtle)",
                fontSize: "0.72rem",
                fontFamily: "var(--font-mono)",
                color: "var(--text-faint)",
              }}
            >
              FROZEN DEMO CORPUS • STRICT VALIDATION PIPELINE
            </div>
          </div>

          {/* Deep Dive 2: Multilingual Legal Validation */}
          <div
            className="paper-card"
            style={{
              padding: "2rem",
              backgroundColor: "var(--bg-sheet)",
              borderRadius: "3px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.6rem",
                  marginBottom: "1rem",
                }}
              >
                <Languages size={18} color="var(--maroon)" />
                <h3
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.25rem",
                    fontWeight: 700,
                    color: "var(--text-ink)",
                  }}
                >
                  Multilingual Translation Validation
                </h3>
              </div>

              <p
                style={{
                  fontFamily: "var(--font-sans)",
                  fontSize: "0.88rem",
                  lineHeight: 1.6,
                  color: "var(--text-muted)",
                  marginBottom: "1.5rem",
                }}
              >
                Standard machine translation distorts judicial terms of art. Vidhik uses a
                protected entity-isolation pipeline before IndicTrans2 translation, restoring
                doctrinal references flawlessly in Indian languages:
              </p>

              {/* Translation pipeline flow */}
              <div
                style={{
                  backgroundColor: "var(--maroon-faint)",
                  border: "1px solid var(--maroon-border)",
                  borderRadius: "2px",
                  padding: "1.25rem",
                  marginBottom: "1.25rem",
                }}
              >
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.75rem",
                    lineHeight: 1.7,
                    color: "var(--maroon-dark)",
                  }}
                >
                  English Legal Representation
                  <br />
                  → Legal Entity Protection
                  <br />
                  → IndicTrans2 Engine (Tamil, Hindi, Kannada, Marathi)
                  <br />
                  → Entity Restoration & Forensic Audit
                </div>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "1rem",
                  marginBottom: "1rem",
                }}
              >
                <div
                  style={{
                    padding: "0.85rem",
                    backgroundColor: "var(--bg-parchment)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "2px",
                  }}
                >
                  <div
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontSize: "1.4rem",
                      fontWeight: 700,
                      color: "var(--maroon)",
                    }}
                  >
                    100%
                  </div>
                  <div style={{ fontSize: "0.74rem", color: "var(--text-muted)" }}>
                    Protected terminology & entity preservation
                  </div>
                </div>

                <div
                  style={{
                    padding: "0.85rem",
                    backgroundColor: "var(--bg-parchment)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "2px",
                  }}
                >
                  <div
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontSize: "1.4rem",
                      fontWeight: 700,
                      color: "var(--navy)",
                    }}
                  >
                    0%
                  </div>
                  <div style={{ fontSize: "0.74rem", color: "var(--text-muted)" }}>
                    Contradiction in evaluated translation pipeline
                  </div>
                </div>
              </div>
            </div>

            <div
              style={{
                marginTop: "1.5rem",
                paddingTop: "0.85rem",
                borderTop: "1px solid var(--border-subtle)",
                fontSize: "0.72rem",
                fontFamily: "var(--font-mono)",
                color: "var(--text-faint)",
              }}
            >
              FORENSIC AUDIT BENCHMARK • INDIC REASONING
            </div>
          </div>
        </div>

        {/* Disclaimer Ribbon */}
        <div
          style={{
            marginTop: "2.5rem",
            textAlign: "center",
            fontSize: "0.8rem",
            color: "var(--text-faint)",
            fontStyle: "italic",
          }}
        >
          * All metrics represent frozen, audited experimental benchmark evaluations. They are not
          extrapolated to represent all un-indexed Indian judgments.
        </div>
      </div>
    </section>
  );
}
