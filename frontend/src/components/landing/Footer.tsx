"use client";

import React from "react";
import Link from "next/link";
import { Logo } from "../shared/Logo";
import { ShieldCheck, Scale, FileText } from "lucide-react";

export function LandingFooter() {
  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <footer
      style={{
        backgroundColor: "var(--bg-surface)",
        borderTop: "1px solid var(--border-rule)",
        padding: "4.5rem 2rem 3rem 2rem",
      }}
    >
      <div
        style={{
          maxWidth: "1280px",
          margin: "0 auto",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.5fr 1fr 1fr 1fr",
            gap: "3rem",
            marginBottom: "3.5rem",
          }}
          className="footer-grid"
        >
          {/* Col 1: Identity & Legal Philosophy */}
          <div>
            <Logo size="md" withTagline={true} />
            <p
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1rem",
                lineHeight: 1.6,
                color: "var(--navy)",
                marginTop: "1.25rem",
                marginBottom: "1rem",
                maxWidth: "340px",
              }}
            >
              Find the law. See the evidence. Understand the authority.
            </p>
            <p
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.82rem",
                lineHeight: 1.6,
                color: "var(--text-muted)",
                maxWidth: "360px",
              }}
            >
              An evidence-centric legal intelligence workspace built for Indian judicial
              documents, preserving verifiable provenance from Supreme Court to District Courts.
            </p>
          </div>

          {/* Col 2: Navigation */}
          <div>
            <h4
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.78rem",
                fontWeight: 700,
                color: "var(--maroon)",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                marginBottom: "1.25rem",
              }}
            >
              Product
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <button
                onClick={() => scrollTo("what-is-vidhik")}
                style={{
                  background: "none",
                  border: "none",
                  textAlign: "left",
                  fontSize: "0.88rem",
                  color: "var(--text-ink)",
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                The Evidence Layer
              </button>
              <button
                onClick={() => scrollTo("evidence-matters")}
                style={{
                  background: "none",
                  border: "none",
                  textAlign: "left",
                  fontSize: "0.88rem",
                  color: "var(--text-ink)",
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                Provenance Chain
              </button>
              <button
                onClick={() => scrollTo("workspace-profiles")}
                style={{
                  background: "none",
                  border: "none",
                  textAlign: "left",
                  fontSize: "0.88rem",
                  color: "var(--text-ink)",
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                Profile Workspaces
              </button>
            </div>
          </div>

          {/* Col 3: Research & Audit */}
          <div>
            <h4
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.78rem",
                fontWeight: 700,
                color: "var(--maroon)",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                marginBottom: "1.25rem",
              }}
            >
              Research & Audit
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <button
                onClick={() => scrollTo("research-metrics")}
                style={{
                  background: "none",
                  border: "none",
                  textAlign: "left",
                  fontSize: "0.88rem",
                  color: "var(--text-ink)",
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                Frozen Benchmark (1,361 Docs)
              </button>
              <button
                onClick={() => scrollTo("research-metrics")}
                style={{
                  background: "none",
                  border: "none",
                  textAlign: "left",
                  fontSize: "0.88rem",
                  color: "var(--text-ink)",
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                District Court Processing
              </button>
              <button
                onClick={() => scrollTo("research-metrics")}
                style={{
                  background: "none",
                  border: "none",
                  textAlign: "left",
                  fontSize: "0.88rem",
                  color: "var(--text-ink)",
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                Multilingual Entity Audit
              </button>
            </div>
          </div>

          {/* Col 4: Workspaces */}
          <div>
            <h4
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.78rem",
                fontWeight: 700,
                color: "var(--maroon)",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                marginBottom: "1.25rem",
              }}
            >
              Workspaces
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <Link
                href="/login"
                style={{
                  fontSize: "0.88rem",
                  color: "var(--text-ink)",
                  textDecoration: "none",
                }}
              >
                Advocate Workspace (/login)
              </Link>
              <Link
                href="/chat"
                style={{
                  fontSize: "0.88rem",
                  color: "var(--text-ink)",
                  textDecoration: "none",
                }}
              >
                Public Legal Chatbot (/chat)
              </Link>
            </div>
          </div>
        </div>

        {/* Legal Disclaimer & Corpus Statement */}
        <div
          style={{
            padding: "1.75rem 0",
            borderTop: "1px solid var(--border-rule)",
            borderBottom: "1px solid var(--border-rule)",
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "2rem",
            fontSize: "0.78rem",
            color: "var(--text-muted)",
            lineHeight: 1.6,
          }}
          className="disclaimer-grid"
        >
          <div>
            <span style={{ fontWeight: 600, color: "var(--navy)" }}>
              Regulatory & Advisory Notice:
            </span>{" "}
            Vidhik is an analytical document intelligence system engineered for legal research and
            information support. Vidhik does not render legal advice, establish attorney-client
            privilege, or replace independent judicial examination by qualified advocates.
          </div>
          <div>
            <span style={{ fontWeight: 600, color: "var(--maroon)" }}>
              Corpus Integrity Notice:
            </span>{" "}
            Document counts and validation figures reflect the verified frozen research/demo
            corpus (1,361 judgments across Supreme Court, High Courts, and District Courts).
            No claim is made regarding processing of the unbounded national judicial archive.
          </div>
        </div>

        {/* Bottom Credits */}
        <div
          style={{
            paddingTop: "2rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: "0.78rem",
            color: "var(--text-faint)",
            flexWrap: "wrap",
            gap: "1rem",
          }}
        >
          <div>
            © 2026 Vidhik Legal Technologies. All judicial document rights
            belong to respective court registries.
          </div>
          <div style={{ display: "flex", gap: "1.5rem" }}>
            <span>Non-Extrapolative Retrieval Engine</span>
            <span>Cryptographic Provenance Verified</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
