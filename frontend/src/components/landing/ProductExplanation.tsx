"use client";

import React from "react";
import { SectionHeading } from "../shared/SectionHeading";
import { Search, Shield, CheckCircle, ArrowRight, AlertCircle, FileText } from "lucide-react";

export function ProductExplanation() {
  return (
    <section
      id="what-is-vidhik"
      style={{
        padding: "5rem 2rem",
        backgroundColor: "var(--bg-surface)",
        borderTop: "1px solid var(--border-rule)",
        borderBottom: "1px solid var(--border-rule)",
      }}
      aria-label="What is Vidhik"
    >
      <div style={{ maxWidth: "1280px", margin: "0 auto" }}>
        <SectionHeading
          badge="THE EVIDENCE LAYER"
          title="Legal information is more than finding a document."
          subtitle="Traditional legal search engines retrieve case files. Vidhik introduces a verified evidence-navigation and intelligence layer that connects legal questions directly to judicial authorities and supporting paragraphs."
          align="center"
        />

        {/* Side-by-side architectural contrast */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "2.5rem",
            marginTop: "3.5rem",
          }}
          className="explanation-grid"
        >
          {/* Card 1: Traditional Systems */}
          <div
            className="paper-card"
            style={{
              padding: "2.25rem",
              borderRadius: "3px",
              backgroundColor: "var(--bg-sheet)",
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
                  gap: "0.75rem",
                  marginBottom: "1.25rem",
                }}
              >
                <div
                  style={{
                    width: "36px",
                    height: "36px",
                    borderRadius: "2px",
                    backgroundColor: "var(--bg-parchment)",
                    border: "1px solid var(--border-rule)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "var(--text-muted)",
                  }}
                >
                  <Search size={18} />
                </div>
                <div>
                  <h3
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontSize: "1.25rem",
                      fontWeight: 700,
                      color: "var(--text-ink)",
                    }}
                  >
                    Traditional Legal Information
                  </h3>
                  <span
                    style={{
                      fontFamily: "var(--font-sans)",
                      fontSize: "0.75rem",
                      color: "var(--text-muted)",
                    }}
                  >
                    Document-level indexation
                  </span>
                </div>
              </div>

              <p
                style={{
                  fontFamily: "var(--font-sans)",
                  fontSize: "0.92rem",
                  lineHeight: 1.6,
                  color: "var(--text-muted)",
                  marginBottom: "1.5rem",
                }}
              >
                Existing databases excel at cataloging judgments and act citations. However,
                answering a complex legal question still demands manual cross-referencing
                across hundreds of PDF pages to isolate governing paragraphs.
              </p>

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.85rem",
                  backgroundColor: "var(--bg-parchment)",
                  padding: "1.25rem",
                  borderRadius: "2px",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem" }}>
                  <span style={{ color: "var(--text-faint)", marginTop: "2px" }}>•</span>
                  <span style={{ fontSize: "0.85rem", color: "var(--text-ink)" }}>
                    Returns long lists of full-length PDF judgments without granular fact isolation
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem" }}>
                  <span style={{ color: "var(--text-faint)", marginTop: "2px" }}>•</span>
                  <span style={{ fontSize: "0.85rem", color: "var(--text-ink)" }}>
                    Generic AI summaries often lack precise paragraph lineage and verifiable citations
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem" }}>
                  <span style={{ color: "var(--text-faint)", marginTop: "2px" }}>•</span>
                  <span style={{ fontSize: "0.85rem", color: "var(--text-ink)" }}>
                    Forces practitioners to manually reconcile conflicting headnotes against original records
                  </span>
                </div>
              </div>
            </div>

            <div
              style={{
                marginTop: "1.75rem",
                paddingTop: "1rem",
                borderTop: "1px solid var(--border-subtle)",
                fontSize: "0.78rem",
                color: "var(--text-faint)",
                fontFamily: "var(--font-mono)",
              }}
            >
              LOCATES THE RECORD • MANUAL AUDIT REQUIRED
            </div>
          </div>

          {/* Card 2: Vidhik Evidence Intelligence */}
          <div
            className="paper-card"
            style={{
              padding: "2.25rem",
              borderRadius: "3px",
              backgroundColor: "var(--bg-sheet)",
              border: "1.5px solid var(--maroon-border)",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              boxShadow: "0 4px 16px rgba(110, 31, 42, 0.06)",
            }}
          >
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  marginBottom: "1.25rem",
                }}
              >
                <div
                  style={{
                    width: "36px",
                    height: "36px",
                    borderRadius: "2px",
                    backgroundColor: "var(--maroon)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#FFFFFF",
                  }}
                >
                  <Shield size={18} />
                </div>
                <div>
                  <h3
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontSize: "1.25rem",
                      fontWeight: 700,
                      color: "var(--maroon)",
                    }}
                  >
                    Vidhik Intelligence Layer
                  </h3>
                  <span
                    style={{
                      fontFamily: "var(--font-sans)",
                      fontSize: "0.75rem",
                      color: "var(--navy)",
                      fontWeight: 600,
                    }}
                  >
                    Paragraph-level provenance & evidence synthesis
                  </span>
                </div>
              </div>

              <p
                style={{
                  fontFamily: "var(--font-sans)",
                  fontSize: "0.92rem",
                  lineHeight: 1.6,
                  color: "var(--text-ink)",
                  marginBottom: "1.5rem",
                }}
              >
                Vidhik decomposes judicial documents into verifiable units (page → paragraph → sentence)
                and performs hybrid retrieval so that every legal explanation links directly to certified
                evidence and judicial authority.
              </p>

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.85rem",
                  backgroundColor: "var(--maroon-faint)",
                  padding: "1.25rem",
                  borderRadius: "2px",
                  border: "1px solid var(--maroon-border)",
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem" }}>
                  <CheckCircle size={15} color="var(--maroon)" style={{ marginTop: "2px", flexShrink: 0 }} />
                  <span style={{ fontSize: "0.85rem", color: "var(--text-ink)", fontWeight: 500 }}>
                    Evidence-grounded explanations with interactive citation anchors [E1] [E2]
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem" }}>
                  <CheckCircle size={15} color="var(--maroon)" style={{ marginTop: "2px", flexShrink: 0 }} />
                  <span style={{ fontSize: "0.85rem", color: "var(--text-ink)", fontWeight: 500 }}>
                    Cryptographic linkage to original District Court, High Court, & Supreme Court judgments
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem" }}>
                  <CheckCircle size={15} color="var(--maroon)" style={{ marginTop: "2px", flexShrink: 0 }} />
                  <span style={{ fontSize: "0.85rem", color: "var(--text-ink)", fontWeight: 500 }}>
                    Audited benchmark: 0% contradiction against extracted evidence chunks
                  </span>
                </div>
              </div>
            </div>

            <div
              style={{
                marginTop: "1.75rem",
                paddingTop: "1rem",
                borderTop: "1px solid var(--border-subtle)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                fontSize: "0.78rem",
                color: "var(--maroon)",
                fontWeight: 600,
                fontFamily: "var(--font-mono)",
              }}
            >
              <span>GROUNDED IN EVIDENCE</span>
              <span>VERIFIABLE PROVENANCE</span>
            </div>
          </div>
        </div>

        {/* Truthfulness & Technical Rigor Boundary Notice */}
        <div
          style={{
            marginTop: "3rem",
            backgroundColor: "var(--bg-parchment)",
            border: "1px solid var(--border-rule)",
            borderRadius: "2px",
            padding: "1.5rem 1.75rem",
            display: "grid",
            gridTemplateColumns: "auto 1fr",
            gap: "1.25rem",
            alignItems: "flex-start",
          }}
        >
          <div
            style={{
              padding: "0.4rem",
              backgroundColor: "var(--bg-surface)",
              border: "1px solid var(--border-rule)",
              borderRadius: "2px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--brass)",
            }}
          >
            <AlertCircle size={20} />
          </div>

          <div>
            <h4
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.88rem",
                fontWeight: 700,
                color: "var(--text-ink)",
                letterSpacing: "0.04em",
                textTransform: "uppercase",
                marginBottom: "0.35rem",
              }}
            >
              Technical Boundary & System Ethics
            </h4>
            <p
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.85rem",
                lineHeight: 1.6,
                color: "var(--text-muted)",
              }}
            >
              Vidhik does not replace certified legal databases or legal counsel. It does not claim
              unbounded correctness across un-indexed jurisprudence, nor does it provide legal advice.
              Vidhik is an evidence-first intelligence workspace engineered to assist lawyers, researchers,
              and citizens in navigating and verifying Indian judicial authorities against verbatim court records.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
