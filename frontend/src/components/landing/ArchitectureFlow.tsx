"use client";

import React from "react";
import { SectionHeading } from "../shared/SectionHeading";
import {
  FileText,
  Binary,
  Layers,
  Filter,
  Cpu,
  FileCheck2,
  CheckCircle,
  ArrowDown,
  ArrowRight,
} from "lucide-react";

interface ArchStep {
  step: string;
  title: string;
  subtitle: string;
  description: string;
  icon: React.ReactNode;
  tag: string;
}

const ARCH_STEPS: ArchStep[] = [
  {
    step: "01",
    title: "Indian Court Documents",
    subtitle: "Raw Records",
    description: "Certified PDF records from Supreme Court, High Courts, and District Courts.",
    icon: <FileText size={18} />,
    tag: "SOURCE REPOSITORIES",
  },
  {
    step: "02",
    title: "Document Intelligence",
    subtitle: "Structural Parsing",
    description: "Hierarchical segmentation (Page → Paragraph → Sentence) with cryptographic hashes.",
    icon: <Binary size={18} />,
    tag: "ATOMIC LINKAGE",
  },
  {
    step: "03",
    title: "Hybrid Retrieval",
    subtitle: "Dense + BM25",
    description: "Combines semantic embeddings with lexical statute indexing for maximum recall.",
    icon: <Layers size={18} />,
    tag: "DUAL PIPELINE",
  },
  {
    step: "04",
    title: "Evidence Selection",
    subtitle: "Context Budgeting",
    description: "Strict top-k fact windows selected within token constraints; non-facts discarded.",
    icon: <Filter size={18} />,
    tag: "BOUNDED BUDGET",
  },
  {
    step: "05",
    title: "Evidence-Constrained LLM",
    subtitle: "Guarded Synthesis",
    description: "LLM operates exclusively within provided evidence windows with anti-extrapolation checks.",
    icon: <Cpu size={18} />,
    tag: "ZERO INVENTIONS",
  },
  {
    step: "06",
    title: "Legal Explanation",
    subtitle: "Anchor Citations",
    description: "Synthesized explanation with clickable citations [E1] linked to judicial excerpts.",
    icon: <FileCheck2 size={18} />,
    tag: "CITATION GROUNDED",
  },
  {
    step: "07",
    title: "Source Verification",
    subtitle: "Certified Provenance",
    description: "Instant one-click verification against certified court PDF page and paragraph record.",
    icon: <CheckCircle size={18} />,
    tag: "COMPLETE AUDIT",
  },
];

export function ArchitectureFlow() {
  return (
    <section
      style={{
        padding: "5.5rem 2rem",
        maxWidth: "1280px",
        margin: "0 auto",
      }}
      aria-label="Simplified Vidhik Architecture"
    >
      <SectionHeading
        badge="ENGINEERING INTEGRITY"
        title="More than PDF → LLM → Answer."
        subtitle="Generic chatbots pass raw text to an AI and hope for accuracy. Vidhik enforces a rigorous multi-stage pipeline where every word is bound by legal evidence budgets and cryptographic source tracking."
        align="center"
      />

      {/* Grid of 7 Stages */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "1.25rem",
          marginTop: "3rem",
        }}
        className="arch-grid"
      >
        {ARCH_STEPS.map((step, idx) => (
          <div
            key={step.step}
            className="paper-card"
            style={{
              padding: "1.5rem",
              borderRadius: "3px",
              backgroundColor: "var(--bg-sheet)",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              position: "relative",
            }}
          >
            <div>
              {/* Header with step number and tag */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "1rem",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <div
                    style={{
                      width: "30px",
                      height: "30px",
                      borderRadius: "2px",
                      backgroundColor: "var(--maroon-faint)",
                      border: "1px solid var(--maroon-border)",
                      color: "var(--maroon)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    {step.icon}
                  </div>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      color: "var(--maroon)",
                    }}
                  >
                    {step.step}
                  </span>
                </div>

                <span
                  style={{
                    fontSize: "0.62rem",
                    fontFamily: "var(--font-mono)",
                    color: "var(--text-faint)",
                    letterSpacing: "0.06em",
                  }}
                >
                  {step.tag}
                </span>
              </div>

              {/* Title & Subtitle */}
              <h3
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "1.15rem",
                  fontWeight: 700,
                  color: "var(--text-ink)",
                  marginBottom: "0.25rem",
                }}
              >
                {step.title}
              </h3>

              <div
                style={{
                  fontFamily: "var(--font-sans)",
                  fontSize: "0.75rem",
                  color: "var(--navy)",
                  fontWeight: 600,
                  marginBottom: "0.75rem",
                }}
              >
                {step.subtitle}
              </div>

              {/* Description */}
              <p
                style={{
                  fontFamily: "var(--font-sans)",
                  fontSize: "0.85rem",
                  lineHeight: 1.55,
                  color: "var(--text-muted)",
                }}
              >
                {step.description}
              </p>
            </div>

            <div
              style={{
                marginTop: "1.25rem",
                paddingTop: "0.75rem",
                borderTop: "1px solid var(--border-subtle)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                fontSize: "0.7rem",
                color: "var(--text-faint)",
              }}
            >
              <span>PIPELINE BOUNDARY</span>
              {idx < ARCH_STEPS.length - 1 ? (
                <span style={{ color: "var(--maroon)", fontWeight: 600 }}>NEXT STAGE →</span>
              ) : (
                <span style={{ color: "var(--navy)", fontWeight: 600 }}>VERIFIED RESULT ✓</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
