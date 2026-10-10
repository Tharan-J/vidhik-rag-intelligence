"use client";

import React, { useState, useEffect } from "react";
import {
  HelpCircle,
  Scale,
  FileCheck2,
  FileText,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";

interface Stage {
  id: string;
  stepNumber: string;
  label: string;
  subtitle: string;
  icon: React.ReactNode;
  detail: {
    title: string;
    body: string;
    meta: string;
    stamp?: string;
  };
}

const STAGES: Stage[] = [
  {
    id: "question",
    stepNumber: "01",
    label: "Legal Question",
    subtitle: "User Inquiry",
    icon: <HelpCircle size={16} />,
    detail: {
      title: "Query Submission",
      body: '"What is the limitation period for filing an appeal under Section 116A of the Representation of the People Act, 1951?"',
      meta: "Target Jurisdiction: Supreme Court & High Courts • Limitation Act 1963",
      stamp: "INQUIRY LOGGED",
    },
  },
  {
    id: "authority",
    stepNumber: "02",
    label: "Relevant Authority",
    subtitle: "Judicial Bench",
    icon: <Scale size={16} />,
    detail: {
      title: "Supreme Court of India",
      body: "Civil Appellate Jurisdiction • Bench: Hon'ble Two-Judge Bench on statutory election appeals.",
      meta: "Civil Appeal No. 4182/2019 • Binding Precedent Art. 141",
      stamp: "AUTHORITY LOCATED",
    },
  },
  {
    id: "evidence",
    stepNumber: "03",
    label: "Supporting Evidence",
    subtitle: "Certified Excerpt",
    icon: <FileCheck2 size={16} />,
    detail: {
      title: "Statutory & Judgment Excerpt",
      body: '"Every appeal under this Chapter shall be preferred within a period of thirty days from the date of the order... subject to condonation upon sufficient cause."',
      meta: "Section 116A(1) & Judgment Para 18 • Hash verified",
      stamp: "EVIDENCE EXTRACTED",
    },
  },
  {
    id: "explanation",
    stepNumber: "04",
    label: "Legal Explanation",
    subtitle: "Evidence-Grounded",
    icon: <FileText size={16} />,
    detail: {
      title: "Strict Evidence Synthesis",
      body: "Under Section 116A, the appeal must be preferred within thirty days [E1]. The appellate bench possesses jurisdiction to condone delay beyond 30 days only upon satisfaction of sufficient cause [E2].",
      meta: "0% contradiction against extracted judicial evidence",
      stamp: "VERIFIED SYNTHESIS",
    },
  },
  {
    id: "source",
    stepNumber: "05",
    label: "Original Source",
    subtitle: "Cryptographic Provenance",
    icon: <CheckCircle2 size={16} />,
    detail: {
      title: "Certified Judgment PDF",
      body: "Page 14, Paragraph 18 • Lineage verified to official court repository record.",
      meta: "Cryptographic linkage: sha256:7b1e8a9... • Scanned record aligned",
      stamp: "SOURCE CERTIFIED",
    },
  },
];

export function HeroAnimation() {
  const [activeStep, setActiveStep] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mediaQuery.matches);
    const handleChange = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  useEffect(() => {
    if (prefersReducedMotion || isPaused) return;

    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % STAGES.length);
    }, 3200);

    return () => clearInterval(timer);
  }, [prefersReducedMotion, isPaused]);

  const currentStage = STAGES[activeStep];

  return (
    <div
      style={{
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-rule)",
        borderRadius: "3px",
        boxShadow: "var(--shadow-layered)",
        padding: "1.75rem",
        position: "relative",
        overflow: "hidden",
      }}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      aria-label="Traceability pipeline visualization from Question to Original Source"
    >
      {/* Top Header of the visualization */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          paddingBottom: "1.25rem",
          borderBottom: "1px solid var(--border-subtle)",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
          <div
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              backgroundColor: "var(--maroon)",
              animation: prefersReducedMotion ? "none" : "nodePulse 2s infinite",
            }}
          />
          <span
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "0.72rem",
              fontWeight: 700,
              letterSpacing: "0.14em",
              color: "var(--navy)",
              textTransform: "uppercase",
            }}
          >
            Traceability Architecture
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.7rem",
              color: "var(--text-faint)",
            }}
          >
            STAGE {currentStage.stepNumber} / 05
          </span>
          <span
            style={{
              fontSize: "0.62rem",
              padding: "0.15rem 0.45rem",
              backgroundColor: "var(--brass-faint)",
              color: "var(--brass)",
              border: "1px solid var(--brass)",
              borderRadius: "2px",
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            {isPaused ? "PAUSED" : "ACTIVE TRACE"}
          </span>
        </div>
      </div>

      {/* Horizontal Flow Stages Track */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(5, 1fr)",
          gap: "0.5rem",
          position: "relative",
          marginBottom: "1.75rem",
        }}
      >
        {STAGES.map((stage, idx) => {
          const isActive = idx === activeStep;
          const isPassed = idx < activeStep;

          return (
            <button
              key={stage.id}
              onClick={() => setActiveStep(idx)}
              style={{
                background: "none",
                border: "none",
                padding: "0.4rem 0.2rem",
                textAlign: "left",
                cursor: "pointer",
                position: "relative",
                display: "flex",
                flexDirection: "column",
                gap: "0.4rem",
              }}
              aria-label={`Inspect Stage ${stage.stepNumber}: ${stage.label}`}
              aria-current={isActive ? "step" : undefined}
            >
              {/* Progress bar indicator line */}
              <div
                style={{
                  height: "3px",
                  width: "100%",
                  backgroundColor: isActive
                    ? "var(--maroon)"
                    : isPassed
                    ? "var(--navy)"
                    : "var(--border-rule)",
                  transition: "background-color 0.3s ease",
                  borderRadius: "1px",
                }}
              />

              {/* Node Icon & Step Indicator */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.4rem",
                  marginTop: "0.2rem",
                }}
              >
                <div
                  style={{
                    width: "22px",
                    height: "22px",
                    borderRadius: "2px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: isActive
                      ? "var(--maroon)"
                      : isPassed
                      ? "var(--navy)"
                      : "var(--bg-parchment)",
                    color: isActive || isPassed ? "#FFFFFF" : "var(--text-muted)",
                    border: `1px solid ${
                      isActive
                        ? "var(--maroon)"
                        : isPassed
                        ? "var(--navy)"
                        : "var(--border-rule)"
                    }`,
                    transition: "all 0.25s ease",
                    fontSize: "0.75rem",
                  }}
                >
                  {stage.icon}
                </div>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    color: isActive ? "var(--maroon)" : "var(--text-muted)",
                  }}
                >
                  {stage.stepNumber}
                </span>
              </div>

              {/* Stage Title */}
              <div style={{ marginTop: "0.1rem" }}>
                <div
                  style={{
                    fontFamily: "var(--font-sans)",
                    fontSize: "0.75rem",
                    fontWeight: isActive ? 700 : 500,
                    color: isActive ? "var(--text-ink)" : "var(--text-muted)",
                    lineHeight: 1.2,
                  }}
                >
                  {stage.label}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Stage Inspection Inspector Card */}
      <div
        style={{
          backgroundColor: "var(--bg-sheet)",
          border: "1px solid var(--border-rule)",
          borderRadius: "2px",
          padding: "1.35rem 1.5rem",
          position: "relative",
          minHeight: "165px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          boxShadow: "0 2px 8px rgba(30, 32, 36, 0.04)",
          transition: "all 0.3s ease",
        }}
      >
        <div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "0.75rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.7rem",
                  fontWeight: 700,
                  color: "var(--maroon)",
                  backgroundColor: "var(--maroon-faint)",
                  padding: "0.15rem 0.4rem",
                  borderRadius: "2px",
                  border: "1px solid var(--maroon-border)",
                }}
              >
                STAGE {currentStage.stepNumber}
              </span>
              <h4
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "1.1rem",
                  fontWeight: 700,
                  color: "var(--text-ink)",
                  margin: 0,
                }}
              >
                {currentStage.detail.title}
              </h4>
            </div>

            {currentStage.detail.stamp && (
              <span className="certified-stamp">
                {currentStage.detail.stamp}
              </span>
            )}
          </div>

          <p
            style={{
              fontFamily: currentStage.id === "evidence" || currentStage.id === "question"
                ? "var(--font-serif)"
                : "var(--font-sans)",
              fontSize: "0.95rem",
              fontStyle: currentStage.id === "evidence" || currentStage.id === "question" ? "italic" : "normal",
              lineHeight: 1.6,
              color: "var(--text-ink)",
              marginBottom: "1rem",
            }}
          >
            {currentStage.detail.body}
          </p>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            paddingTop: "0.75rem",
            borderTop: "1px solid var(--border-subtle)",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "0.75rem",
              color: "var(--navy)",
              fontWeight: 500,
            }}
          >
            {currentStage.detail.meta}
          </span>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.35rem",
              fontSize: "0.72rem",
              color: "var(--maroon)",
              fontWeight: 600,
            }}
          >
            <span>Verifiable chain</span>
            <ExternalLink size={12} />
          </div>
        </div>
      </div>

      {/* Visual Chain Bottom Footnote */}
      <div
        style={{
          marginTop: "1.25rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          fontSize: "0.72rem",
          color: "var(--text-faint)",
          fontFamily: "var(--font-sans)",
        }}
      >
        <span>
          Traceable: Question → Authority → Evidence → Explanation → Source
        </span>
        <span style={{ fontStyle: "italic" }}>
          Hover to pause inspection
        </span>
      </div>
    </div>
  );
}
