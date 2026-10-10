"use client";

import React from "react";
import { EvidenceItem } from "../lib/types";

interface JudgmentModalProps {
  evidence: EvidenceItem | null;
  onClose: () => void;
}

export function JudgmentModal({ evidence, onClose }: JudgmentModalProps) {
  if (!evidence) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(23, 42, 58, 0.45)",
        backdropFilter: "blur(2px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 100,
        padding: "2rem",
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: "#FFFFFF",
          width: "100%",
          maxWidth: "760px",
          maxHeight: "90vh",
          display: "flex",
          flexDirection: "column",
          borderRadius: "3px",
          boxShadow: "0 20px 40px -10px rgba(23, 42, 58, 0.35)",
          border: "1px solid var(--border-rule)",
          position: "relative",
          overflow: "hidden",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Court Registry Header */}
        <div
          style={{
            backgroundColor: "var(--bg-surface)",
            borderBottom: "1px solid var(--border-rule)",
            padding: "1rem 1.5rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <span className="certified-stamp">CERTIFIED EXTRACT</span>
            <span
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.8rem",
                fontWeight: 600,
                color: "var(--maroon)",
                letterSpacing: "0.05em",
              }}
            >
              EVIDENCE [{evidence.evidence_id}]
            </span>
          </div>

          <button
            onClick={onClose}
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "0.85rem",
              fontWeight: 600,
              color: "var(--text-muted)",
              padding: "0.25rem 0.5rem",
              border: "1px solid var(--border-subtle)",
              borderRadius: "2px",
              backgroundColor: "#FFFFFF",
            }}
          >
            Close &times;
          </button>
        </div>

        {/* Certified Judgment Sheet Paper Surface */}
        <div
          style={{
            padding: "2.5rem 3rem",
            overflowY: "auto",
            backgroundColor: "#FAF9F5",
            fontFamily: "var(--font-serif)",
            lineHeight: 1.7,
            color: "var(--text-ink)",
          }}
        >
          {/* Header of Court */}
          <div style={{ textAlign: "center", marginBottom: "2rem" }}>
            <h3
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1.25rem",
                textTransform: "uppercase",
                letterSpacing: "0.1em",
                color: "var(--text-ink)",
                fontWeight: 700,
                marginBottom: "0.35rem",
              }}
            >
              IN THE {evidence.court.toUpperCase()}
            </h3>
            <p
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.75rem",
                letterSpacing: "0.15em",
                color: "var(--text-muted)",
                textTransform: "uppercase",
              }}
            >
              {evidence.court_level} &bull; APPELLATE / ORIGINAL JURISDICTION
            </p>
          </div>

          {/* Cause Title Box */}
          <div
            style={{
              border: "1px solid var(--border-rule)",
              padding: "1.25rem 1.5rem",
              backgroundColor: "#FFFFFF",
              marginBottom: "2rem",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: "0.78rem",
                fontFamily: "var(--font-sans)",
                color: "var(--text-muted)",
                marginBottom: "0.75rem",
                borderBottom: "1px solid var(--border-subtle)",
                paddingBottom: "0.5rem",
              }}
            >
              <span>CASE NO: <strong>{evidence.case_number || "REGULAR APPEAL"}</strong></span>
              <span>DECISION DATE: <strong>{evidence.decision_date}</strong></span>
            </div>

            <p
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1.05rem",
                fontWeight: 600,
                color: "var(--navy)",
                textAlign: "center",
                lineHeight: 1.4,
              }}
            >
              {evidence.case_title}
            </p>
          </div>

          {/* Certified Pages Landmark */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              fontSize: "0.72rem",
              fontFamily: "var(--font-sans)",
              color: "var(--text-faint)",
              marginBottom: "1rem",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            <span>Passage From Pages: {evidence.page_number || `${evidence.page_start}-${evidence.page_end}`}</span>
            <span>Paragraph: {evidence.paragraph_id || evidence.paragraph_start || "CERTIFIED"}</span>
          </div>

          {/* Highlighted Extract Content */}
          <div
            style={{
              backgroundColor: "#FFFDF0",
              borderLeft: "3px solid var(--maroon)",
              padding: "1.5rem 1.75rem",
              fontSize: "1.02rem",
              lineHeight: 1.8,
              boxShadow: "0 1px 3px rgba(0,0,0,0.02)",
              marginBottom: "2rem",
            }}
          >
            <p>{evidence.text}</p>
          </div>

          {/* Official Document Seal Footer */}
          <div
            style={{
              borderTop: "1px solid var(--border-rule)",
              paddingTop: "1.25rem",
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "1rem",
              fontSize: "0.75rem",
              fontFamily: "var(--font-sans)",
              color: "var(--text-muted)",
            }}
          >
            <div>
              <span style={{ display: "block", color: "var(--text-faint)", fontSize: "0.68rem" }}>
                DOCUMENT RECORD
              </span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", wordBreak: "break-all" }}>
                {evidence.source_file || evidence.chunk_id}
              </span>
            </div>

            <div style={{ textAlign: "right" }}>
              <span style={{ display: "block", color: "var(--text-faint)", fontSize: "0.68rem" }}>
                QDRANT POINT ID &bull; RRF RANK
              </span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem" }}>
                #{evidence.rrf_rank || 1} &bull; {evidence.qdrant_point_id ? evidence.qdrant_point_id.slice(0, 16) + "..." : "indexed"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
