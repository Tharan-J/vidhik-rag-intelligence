"use client";

import React, { useState } from "react";
import { SectionHeading } from "../shared/SectionHeading";
import {
  FileText,
  FileCheck,
  Scale,
  Bookmark,
  FileCode,
  ArrowRight,
  ExternalLink,
  CheckCircle2,
  ChevronRight,
  Eye,
} from "lucide-react";

interface ChainNode {
  id: string;
  badge: string;
  title: string;
  shortLabel: string;
  summary: string;
  detail: {
    heading: string;
    content: string;
    metadata: { label: string; value: string }[];
    tag: string;
  };
}

const CHAIN_NODES: ChainNode[] = [
  {
    id: "claim",
    badge: "STAGE 01",
    shortLabel: "Claim",
    title: "AI Synthesis Claim",
    summary: "Section 116A prescribes a 30-day limitation period for filing an appeal, subject to condonation upon sufficient cause under the statutory proviso.",
    detail: {
      heading: "Generated Legal Explanation Assertion",
      content:
        '“An election appeal preferred under Section 116A of the Representation of the People Act, 1951 must be filed within thirty calendar days from the pronouncement of the decision [E1]. The appellate bench possesses jurisdiction to condone delay beyond the 30-day statutory threshold only upon proof of sufficient cause under the proviso [E2].”',
      metadata: [
        { label: "Confidence", value: "Strictly Grounded (1.00)" },
        { label: "Extrapolation", value: "0% Unverified Addition" },
        { label: "Citation Anchors", value: "2 Linked Footnotes" },
      ],
      tag: "ASSERTION ANCHOR",
    },
  },
  {
    id: "evidence",
    badge: "STAGE 02",
    shortLabel: "Evidence",
    title: "Supporting Evidence Excerpt",
    summary: "Extracted verbatim statutory provision and judicial finding indexed in District & Appellate document pipeline.",
    detail: {
      heading: "Verbatim Judicial Text Window",
      content:
        '“Every appeal under this Chapter shall be preferred within a period of thirty days from the date of the order of the High Court: Provided that the High Court may entertain an appeal after the expiry of the said period of thirty days if it is satisfied that the appellant had sufficient cause for not preferring the appeal within such period.”',
      metadata: [
        { label: "Token Window", value: "148 Words (Paragraph 18)" },
        { label: "Chunk Hash", value: "e2c8a19f...4b8" },
        { label: "Extraction Pipeline", value: "Frozen DC/HC/SC Engine" },
      ],
      tag: "VERBATIM EXTRACT",
    },
  },
  {
    id: "judgment",
    badge: "STAGE 03",
    shortLabel: "Judgment",
    title: "Judicial Authority & Bench",
    summary: "Binding precedent of the Hon'ble Supreme Court of India under Article 141 of the Constitution.",
    detail: {
      heading: "Certified Appellate Judgment",
      content:
        "Civil Appeal No. 4182 of 2019 — Hon'ble Supreme Court of India. Two-Judge Appellate Bench on Election Petitions and Statutory Condonation under the Representation of the People Act, 1951.",
      metadata: [
        { label: "Court", value: "Supreme Court of India" },
        { label: "Case Type", value: "Civil Appellate Jurisdiction" },
        { label: "Decision Date", value: "14 October 2019" },
      ],
      tag: "BINDING AUTHORITY",
    },
  },
  {
    id: "paragraph",
    badge: "STAGE 04",
    shortLabel: "Page / Paragraph",
    title: "Exact Spatial Coordinate",
    summary: "Precise coordinates: Page 14, Paragraph 18, Sentence 2–4 with bounding sentence offsets.",
    detail: {
      heading: "Spatial & Structural Coordinate",
      content:
        "Page 14, Paragraph 18 (Sentences 1–3). Document segmentation preserved through hierarchical Page → Paragraph → Sentence relational index. Cryptographically tied to source bounding box.",
      metadata: [
        { label: "Page Number", value: "Page 14 of 32" },
        { label: "Paragraph Index", value: "Paragraph 18" },
        { label: "Sentence Range", value: "Sentences 1 to 3" },
      ],
      tag: "COORDINATE AUDITED",
    },
  },
  {
    id: "source",
    badge: "STAGE 05",
    shortLabel: "Source",
    title: "Original Source PDF Record",
    summary: "Cryptographic hash match to official registry PDF repository with digital signature verification.",
    detail: {
      heading: "Official Court Repository Document",
      content:
        "Original certified PDF as published by the Registry of the Supreme Court of India. Verified via SHA-256 digest with zero OCR distortion or document tampering.",
      metadata: [
        { label: "PDF File", value: "SC_CA_4182_2019_JUDGMENT.pdf" },
        { label: "SHA-256 Digest", value: "9f8a27b140cd4810...a871" },
        { label: "Registry Source", value: "SCI Official Repository" },
      ],
      tag: "SOURCE CERTIFIED",
    },
  },
];

export function EvidenceFlow() {
  const [selectedNodeId, setSelectedNodeId] = useState<string>("claim");

  const currentNode = CHAIN_NODES.find((n) => n.id === selectedNodeId) || CHAIN_NODES[0];
  const currentIndex = CHAIN_NODES.findIndex((n) => n.id === selectedNodeId);

  return (
    <section
      id="evidence-matters"
      style={{
        padding: "5.5rem 2rem",
        maxWidth: "1280px",
        margin: "0 auto",
      }}
      aria-label="Why Evidence Matters"
    >
      <SectionHeading
        badge="THE PROVENANCE CHAIN"
        title="The answer is not the end."
        subtitle="Vidhik is designed so that an AI-generated explanation can lead back to the evidence and judicial authority supporting it. Explore each step of the verifiable legal chain below."
        align="center"
      />

      {/* Interactive Traceability Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "0.75rem",
          flexWrap: "wrap",
          marginBottom: "2.5rem",
        }}
      >
        {CHAIN_NODES.map((node, index) => {
          const isSelected = node.id === selectedNodeId;
          const isPrior = index < currentIndex;

          return (
            <React.Fragment key={node.id}>
              <button
                onClick={() => setSelectedNodeId(node.id)}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.6rem",
                  padding: "0.6rem 1.15rem",
                  backgroundColor: isSelected
                    ? "var(--maroon)"
                    : isPrior
                    ? "var(--maroon-faint)"
                    : "var(--bg-surface)",
                  color: isSelected
                    ? "#FFFFFF"
                    : isPrior
                    ? "var(--maroon)"
                    : "var(--text-ink)",
                  border: `1px solid ${
                    isSelected
                      ? "var(--maroon)"
                      : isPrior
                      ? "var(--maroon-border)"
                      : "var(--border-rule)"
                  }`,
                  borderRadius: "2px",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                  boxShadow: isSelected
                    ? "0 2px 6px rgba(110, 31, 42, 0.25)"
                    : "var(--shadow-sheet)",
                }}
                aria-label={`View ${node.shortLabel} details`}
                aria-pressed={isSelected}
              >
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    opacity: isSelected ? 0.9 : 0.7,
                  }}
                >
                  {node.badge}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-sans)",
                    fontSize: "0.85rem",
                    fontWeight: isSelected ? 700 : 500,
                  }}
                >
                  {node.shortLabel}
                </span>
                {isSelected && <Eye size={14} style={{ marginLeft: "2px" }} />}
              </button>

              {index < CHAIN_NODES.length - 1 && (
                <ChevronRight
                  size={16}
                  color={index < currentIndex ? "var(--maroon)" : "var(--border-dark)"}
                  style={{ flexShrink: 0 }}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Deep Inspection Panel */}
      <div
        className="paper-card evidence-inspect-grid"
        style={{
          padding: "2.5rem",
          backgroundColor: "var(--bg-sheet)",
          borderRadius: "3px",
          border: "1.5px solid var(--border-dark)",
          boxShadow: "var(--shadow-layered)",
          display: "grid",
          gridTemplateColumns: "1.15fr 0.85fr",
          gap: "3rem",
        }}
      >
        {/* Left Side: Content & Verbatim Proof */}
        <div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              marginBottom: "1rem",
            }}
          >
            <span className="certified-stamp">{currentNode.detail.tag}</span>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.75rem",
                color: "var(--text-faint)",
              }}
            >
              PROVENANCE LINEAGE STEP {currentIndex + 1} OF 5
            </span>
          </div>

          <h3
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "1.75rem",
              fontWeight: 700,
              color: "var(--text-ink)",
              marginBottom: "1.25rem",
            }}
          >
            {currentNode.detail.heading}
          </h3>

          <div
            style={{
              backgroundColor: "var(--bg-parchment)",
              border: "1px solid var(--border-rule)",
              borderRadius: "2px",
              padding: "1.5rem",
              marginBottom: "1.75rem",
              position: "relative",
            }}
          >
            <p
              style={{
                fontFamily:
                  currentNode.id === "evidence" || currentNode.id === "claim"
                    ? "var(--font-serif)"
                    : "var(--font-sans)",
                fontSize: "1.05rem",
                lineHeight: 1.7,
                color: "var(--text-ink)",
                fontStyle:
                  currentNode.id === "evidence" || currentNode.id === "claim"
                    ? "italic"
                    : "normal",
              }}
            >
              {currentNode.detail.content}
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            {currentIndex < CHAIN_NODES.length - 1 ? (
              <button
                onClick={() => setSelectedNodeId(CHAIN_NODES[currentIndex + 1].id)}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  backgroundColor: "var(--navy)",
                  color: "#FFFFFF",
                  padding: "0.65rem 1.25rem",
                  borderRadius: "2px",
                  fontSize: "0.85rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                <span>Follow link to {CHAIN_NODES[currentIndex + 1].shortLabel}</span>
                <ArrowRight size={14} />
              </button>
            ) : (
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  color: "var(--maroon)",
                  fontWeight: 600,
                  fontSize: "0.88rem",
                }}
              >
                <CheckCircle2 size={16} />
                <span>Complete Traceability Chain Confirmed</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Structured Metadata & Proof Record */}
        <div
          style={{
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border-rule)",
            borderRadius: "2px",
            padding: "1.75rem",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <h4
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.82rem",
                fontWeight: 700,
                color: "var(--navy)",
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                marginBottom: "1.25rem",
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
              }}
            >
              <FileCheck size={16} color="var(--maroon)" />
              Lineage Verification Audit
            </h4>

            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {currentNode.detail.metadata.map((meta, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.2rem",
                    paddingBottom: "0.75rem",
                    borderBottom: "1px solid var(--border-subtle)",
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-sans)",
                      fontSize: "0.72rem",
                      color: "var(--text-faint)",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    {meta.label}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.85rem",
                      fontWeight: 600,
                      color: "var(--text-ink)",
                    }}
                  >
                    {meta.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Cryptographic Linkage Box */}
          <div
            style={{
              marginTop: "1.5rem",
              padding: "1rem",
              backgroundColor: "var(--maroon-faint)",
              border: "1px solid var(--maroon-border)",
              borderRadius: "2px",
            }}
          >
            <div
              style={{
                fontSize: "0.72rem",
                fontFamily: "var(--font-sans)",
                fontWeight: 700,
                color: "var(--maroon)",
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                marginBottom: "0.25rem",
              }}
            >
              Vidhik Non-Extrapolative Guarantee
            </div>
            <p
              style={{
                fontSize: "0.78rem",
                lineHeight: 1.5,
                color: "var(--text-ink)",
                margin: 0,
              }}
            >
              Explanations cannot invent judicial holdings. The system demands that each substantive
              sentence traces back to an audited court record.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
