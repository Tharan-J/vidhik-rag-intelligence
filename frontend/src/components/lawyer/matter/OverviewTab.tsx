"use client";

import React, { useState } from "react";
import { Matter } from "@/lib/types/matter";
import {
  FileText,
  Calendar,
  Users,
  AlertCircle,
  Sparkles,
  CheckCircle2,
  Clock,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { ProvenanceBadge } from "./ProvenanceBadge";

interface OverviewTabProps {
  matter: Matter;
  onNavigateTab: (tab: string) => void;
}

export function OverviewTab({ matter, onNavigateTab }: OverviewTabProps) {
  const [aiSummary, setAiSummary] = useState(matter.aiSummary);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const handleRefreshSummary = async () => {
    setLoadingSummary(true);
    setSummaryError(null);
    try {
      const res = await fetch("/api/ai/matter-summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: matter.title,
          caseNumber: matter.caseNumber,
          court: matter.court,
          parties: matter.parties,
          documentSummaries: matter.documents.map(
            (d) => `${d.name} (${d.type}): ${d.extractedMetadata?.important_points?.join("; ") || "Uploaded document"}`
          ),
        }),
      });

      if (!res.ok) throw new Error("Failed to generate AI summary.");
      const data = await res.json();
      setAiSummary({
        ...data.summary,
        generated_at: new Date().toISOString(),
        originating_documents: matter.documents.map((d) => d.name),
      });
    } catch (err: any) {
      setSummaryError(err.message || "Failed to generate AI summary.");
    } finally {
      setLoadingSummary(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}>
      {/* =====================================================================
          AI-GENERATED MATTER SUMMARY (GEMINI 3.5 FLASH LITE)
          ===================================================================== */}
      <div
        className="paper-card"
        style={{
          padding: "2rem",
          backgroundColor: "var(--bg-sheet)",
          border: "1.5px solid var(--border-dark)",
          borderRadius: "3px",
          position: "relative",
        }}
      >
        {/* Top Identification Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "1.25rem",
            flexWrap: "wrap",
            gap: "0.75rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.35rem",
                padding: "0.2rem 0.6rem",
                backgroundColor: "var(--maroon-faint)",
                border: "1px solid var(--maroon-border)",
                borderRadius: "2px",
                fontSize: "0.72rem",
                fontWeight: 700,
                color: "var(--maroon)",
                letterSpacing: "0.06em",
                textTransform: "uppercase",
              }}
            >
              <Sparkles size={12} />
              <span>AI-Generated Matter Summary</span>
            </span>

            <span
              style={{
                fontSize: "0.7rem",
                fontFamily: "var(--font-mono)",
                color: "var(--text-faint)",
              }}
            >
              Engine: Gemini 3.5 Flash Lite
            </span>
          </div>

          <button
            onClick={handleRefreshSummary}
            disabled={loadingSummary}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
              fontSize: "0.76rem",
              color: "var(--navy)",
              background: "none",
              border: "1px solid var(--border-rule)",
              borderRadius: "2px",
              padding: "0.3rem 0.65rem",
              cursor: loadingSummary ? "wait" : "pointer",
            }}
          >
            <RefreshCw
              size={12}
              style={{
                animation: loadingSummary ? "spin 1s linear infinite" : "none",
              }}
            />
            <span>{loadingSummary ? "Regenerating..." : "Refresh Summary"}</span>
          </button>
        </div>

        {summaryError && (
          <div
            style={{
              padding: "0.6rem 0.85rem",
              backgroundColor: "var(--maroon-faint)",
              color: "var(--maroon)",
              fontSize: "0.8rem",
              borderRadius: "2px",
              marginBottom: "1rem",
            }}
          >
            {summaryError}
          </div>
        )}

        {/* LAYER A: SOURCE FACTS (Verbatim Court Record Facts) */}
        <div
          style={{
            backgroundColor: "var(--bg-parchment)",
            border: "1px solid var(--border-rule)",
            borderRadius: "3px",
            padding: "1.25rem 1.5rem",
            marginBottom: "1.25rem",
            borderLeft: "4px solid #10754A",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem", flexWrap: "wrap", gap: "0.5rem" }}>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.72rem",
                fontWeight: 700,
                color: "#10754A",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              LAYER A — SOURCE FACTS (PRIMARY COURT RECORD)
            </span>
            <ProvenanceBadge
              type="SOURCE_EXPLICIT"
              sourceDoc={matter.documents[0]?.name}
              labelOverride="✓ SOURCE EXPLICIT"
            />
          </div>
          <p
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "1.05rem",
              lineHeight: 1.65,
              color: "var(--text-ink)",
              margin: 0,
            }}
          >
            {matter.sourceSummary || matter.summary}
          </p>
        </div>

        {/* LAYER B: SOURCE-DERIVED FACTS (Logically Derived without External Extrapolation) */}
        {matter.sourceDerivedSummary && (
          <div
            style={{
              backgroundColor: "#F0FDFA",
              border: "1px solid #99F6E4",
              borderRadius: "3px",
              padding: "1.1rem 1.4rem",
              marginBottom: "1.25rem",
              borderLeft: "4px solid #0F766E",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.4rem", flexWrap: "wrap", gap: "0.5rem" }}>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  color: "#0F766E",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                LAYER B — SOURCE-DERIVED FACTS
              </span>
              <ProvenanceBadge type="SOURCE_DERIVED" labelOverride="◒ SOURCE DERIVED" />
            </div>
            <p
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "0.95rem",
                lineHeight: 1.6,
                color: "var(--text-ink)",
                margin: 0,
              }}
            >
              {matter.sourceDerivedSummary}
            </p>
          </div>
        )}

        {/* LAYER C: AI ANALYSIS (Commentary & Doctrinal Implications - Never Court Findings) */}
        {matter.aiAnalysis && (
          <div
            style={{
              backgroundColor: "rgba(217, 119, 6, 0.05)",
              border: "1px solid rgba(217, 119, 6, 0.25)",
              borderRadius: "3px",
              padding: "1.1rem 1.4rem",
              marginBottom: "1.5rem",
              borderLeft: "4px solid #D97706",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.4rem", flexWrap: "wrap", gap: "0.5rem" }}>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  color: "#B45309",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                LAYER C — AI ANALYSIS (LEGAL COMMENTARY / IMPLICATIONS)
              </span>
              <ProvenanceBadge type="AI_ANALYSIS" labelOverride="⚠ AI ANALYSIS (NOT A COURT FINDING)" />
            </div>
            <p
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.88rem",
                lineHeight: 1.55,
                color: "var(--text-ink)",
                margin: 0,
              }}
            >
              {matter.aiAnalysis}
            </p>
          </div>
        )}

        {/* COURT-DIRECTED FUTURE ACTIONS (Must NEVER be presented as completed events) */}
        {matter.futureDirections && matter.futureDirections.length > 0 && (
          <div
            style={{
              backgroundColor: "#EFF6FF",
              border: "1px solid #BFDBFE",
              borderRadius: "3px",
              padding: "1.2rem 1.5rem",
              marginBottom: "1.5rem",
              borderLeft: "4px solid #2563EB",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.6rem", flexWrap: "wrap", gap: "0.5rem" }}>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.74rem",
                  fontWeight: 700,
                  color: "#1E40AF",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                COURT-DIRECTED FUTURE ACTIONS (PENDING COMPLIANCE)
              </span>
              <span
                style={{
                  fontSize: "0.68rem",
                  fontWeight: 700,
                  fontFamily: "var(--font-mono)",
                  color: "#1E40AF",
                  backgroundColor: "#DBEAFE",
                  padding: "0.15rem 0.5rem",
                  borderRadius: "2px",
                  border: "1px solid #93C5FD",
                }}
              >
                STATUS: DIRECTED NOT COMPLETED
              </span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {matter.futureDirections.map((dir, idx) => (
                <div
                  key={dir.id || idx}
                  style={{
                    backgroundColor: "#FFFFFF",
                    padding: "0.75rem 1rem",
                    borderRadius: "2px",
                    border: "1px solid #DBEAFE",
                    fontSize: "0.86rem",
                  }}
                >
                  <div style={{ color: "var(--text-ink)", lineHeight: 1.5, marginBottom: "0.35rem" }}>
                    {dir.direction}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "1rem", fontSize: "0.74rem", color: "var(--text-faint)", flexWrap: "wrap" }}>
                    {dir.directedTo && (
                      <span><strong>Directed To:</strong> {dir.directedTo}</span>
                    )}
                    {dir.timeframe && (
                      <span><strong>Timeframe:</strong> {dir.timeframe}</span>
                    )}
                    <ProvenanceBadge
                      type={dir.provenance || "SOURCE_EXPLICIT"}
                      page={dir.source?.page}
                      paragraph={dir.source?.paragraph}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Current Procedural Standing */}
        <div
          style={{
            backgroundColor: "var(--bg-parchment)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "2px",
            padding: "1rem 1.25rem",
            marginBottom: "1.5rem",
            display: "flex",
            alignItems: "flex-start",
            gap: "0.75rem",
          }}
        >
          <Clock size={16} color="var(--maroon)" style={{ marginTop: "2px", flexShrink: 0 }} />
          <div>
            <div
              style={{
                fontSize: "0.75rem",
                fontWeight: 700,
                color: "var(--navy)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: "0.2rem",
              }}
            >
              Current Procedural Standing
            </div>
            <div style={{ fontSize: "0.88rem", color: "var(--text-ink)", lineHeight: 1.5 }}>
              {matter.lastKnownEvent || matter.status}
            </div>
          </div>
        </div>

        {/* Key Identified Issues & Attention Documents */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.2fr 0.8fr",
            gap: "1.75rem",
            marginBottom: "1.5rem",
          }}
          className="research-breakdown-grid"
        >
          {/* Key Issues */}
          <div>
            <h4
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.82rem",
                fontWeight: 700,
                color: "var(--navy)",
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                marginBottom: "0.75rem",
              }}
            >
              Key Issues on Record
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {(aiSummary?.key_issues || matter.issues.map((i) => i.title)).map((issue, idx) => (
                <div
                  key={idx}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: "0.5rem",
                    fontSize: "0.85rem",
                    color: "var(--text-ink)",
                  }}
                >
                  <span style={{ color: "var(--maroon)", fontWeight: 700 }}>•</span>
                  <span>{issue}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Documents Requiring Attention */}
          <div>
            <h4
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.82rem",
                fontWeight: 700,
                color: "var(--navy)",
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                marginBottom: "0.75rem",
              }}
            >
              Documents Requiring Attention
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.45rem" }}>
              {(aiSummary?.documents_requiring_attention || [
                "Hospitalization_Certificate_Ex_A4.pdf",
                "Appellant_Written_Arguments.pdf",
              ]).map((doc, idx) => (
                <div
                  key={idx}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.45rem",
                    fontSize: "0.82rem",
                    color: "var(--navy)",
                    backgroundColor: "var(--bg-surface)",
                    padding: "0.35rem 0.6rem",
                    borderRadius: "2px",
                    border: "1px solid var(--border-subtle)",
                  }}
                >
                  <FileText size={13} color="var(--maroon)" />
                  <span style={{ fontWeight: 500 }}>{doc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Originating Documents & Disclaimer Footnote */}
        <div
          style={{
            paddingTop: "1rem",
            borderTop: "1px solid var(--border-subtle)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "0.75rem",
            fontSize: "0.74rem",
            color: "var(--text-faint)",
          }}
        >
          <div>
            <span style={{ fontWeight: 600, color: "var(--text-muted)" }}>
              Originating matter records:{" "}
            </span>
            <span>
              {(aiSummary?.originating_documents || matter.documents.map((d) => d.name))
                .slice(0, 3)
                .join(", ")}
            </span>
          </div>

          <div style={{ fontStyle: "italic", color: "var(--text-muted)" }}>
            * Workspace summary only. Not an authoritative legal conclusion.
          </div>
        </div>
      </div>

      {/* =====================================================================
          TWO-COLUMN GRID: KEY PARTIES & IMPORTANT DATES
          ===================================================================== */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "2rem",
        }}
        className="research-breakdown-grid"
      >
        {/* Key Parties */}
        <div
          className="paper-card"
          style={{
            padding: "1.75rem",
            backgroundColor: "var(--bg-sheet)",
            borderRadius: "3px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              marginBottom: "1.25rem",
            }}
          >
            <Users size={17} color="var(--maroon)" />
            <h3
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1.25rem",
                fontWeight: 700,
                color: "var(--text-ink)",
                margin: 0,
              }}
            >
              Key Parties & Representation
            </h3>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div style={{ paddingBottom: "0.75rem", borderBottom: "1px solid var(--border-subtle)" }}>
              <div style={{ fontSize: "0.72rem", color: "var(--text-faint)", textTransform: "uppercase" }}>
                Appellant / Petitioner
              </div>
              <div style={{ fontSize: "0.92rem", fontWeight: 600, color: "var(--text-ink)" }}>
                {matter.parties.petitioner}
              </div>
            </div>

            <div style={{ paddingBottom: "0.75rem", borderBottom: "1px solid var(--border-subtle)" }}>
              <div style={{ fontSize: "0.72rem", color: "var(--text-faint)", textTransform: "uppercase" }}>
                Respondent
              </div>
              <div style={{ fontSize: "0.92rem", fontWeight: 600, color: "var(--text-ink)" }}>
                {matter.parties.respondent}
              </div>
            </div>

            <div style={{ paddingBottom: "0.75rem", borderBottom: "1px solid var(--border-subtle)" }}>
              <div style={{ fontSize: "0.72rem", color: "var(--text-faint)", textTransform: "uppercase" }}>
                Advocate On Record
              </div>
              <div style={{ fontSize: "0.92rem", fontWeight: 600, color: "var(--navy)" }}>
                {matter.parties.counsel}
              </div>
            </div>

            <div>
              <div style={{ fontSize: "0.72rem", color: "var(--text-faint)", textTransform: "uppercase" }}>
                Judicial Bench
              </div>
              <div style={{ fontSize: "0.92rem", fontWeight: 600, color: "var(--text-ink)" }}>
                {matter.parties.court}
              </div>
            </div>
          </div>
        </div>

        {/* Important Dates */}
        <div
          className="paper-card"
          style={{
            padding: "1.75rem",
            backgroundColor: "var(--bg-sheet)",
            borderRadius: "3px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "1.25rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Calendar size={17} color="var(--navy)" />
              <h3
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "1.25rem",
                  fontWeight: 700,
                  color: "var(--text-ink)",
                  margin: 0,
                }}
              >
                Important Dates & Deadlines
              </h3>
            </div>

            <button
              onClick={() => onNavigateTab("timeline")}
              style={{
                fontSize: "0.78rem",
                color: "var(--maroon)",
                fontWeight: 600,
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: 0,
              }}
            >
              View Timeline →
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                paddingBottom: "0.75rem",
                borderBottom: "1px solid var(--border-subtle)",
              }}
            >
              <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                Filing Date
              </span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.88rem", fontWeight: 600 }}>
                {matter.importantDates.filingDate}
              </span>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                paddingBottom: "0.75rem",
                borderBottom: "1px solid var(--border-subtle)",
              }}
            >
              <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                Last Hearing
              </span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.88rem", fontWeight: 600 }}>
                {matter.importantDates.lastHearing}
              </span>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                paddingBottom: "0.75rem",
                borderBottom: "1px solid var(--border-subtle)",
              }}
            >
              <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--maroon)" }}>
                Next Hearing
              </span>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.92rem",
                  fontWeight: 700,
                  color: "var(--maroon)",
                }}
              >
                {matter.importantDates.nextHearing}
              </span>
            </div>

            {matter.importantDates.writtenSubmissionsDeadline && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <span style={{ fontSize: "0.85rem", color: "var(--navy)", fontWeight: 600 }}>
                  Submissions Deadline
                </span>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.88rem", fontWeight: 600 }}>
                  {matter.importantDates.writtenSubmissionsDeadline}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
