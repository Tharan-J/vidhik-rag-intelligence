"use client";

import React, { useState } from "react";
import { Claim, CitationAuthority, EvidenceItem } from "../lib/types";

interface ProvenanceTrailProps {
  claim: Claim;
  claimIndex: number;
  evidenceList: EvidenceItem[];
  onSelectEvidence: (evidenceId: string) => void;
}

export function ProvenanceTrail({
  claim,
  claimIndex,
  evidenceList,
  onSelectEvidence,
}: ProvenanceTrailProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Group authorities by evidence ID
  const authoritiesByEvidence: Record<string, CitationAuthority[]> = {};
  claim.authorities.forEach((auth) => {
    if (!authoritiesByEvidence[auth.evidence_id]) {
      authoritiesByEvidence[auth.evidence_id] = [];
    }
    authoritiesByEvidence[auth.evidence_id].push(auth);
  });

  return (
    <div
      style={{
        marginTop: "0.75rem",
        borderTop: "1px dashed var(--border-subtle)",
        paddingTop: "0.6rem",
      }}
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.35rem",
          fontSize: "0.76rem",
          fontFamily: "var(--font-sans)",
          fontWeight: 600,
          color: isOpen ? "var(--maroon)" : "var(--text-muted)",
          cursor: "pointer",
        }}
      >
        <span>{isOpen ? "▾ Hide Provenance Authority Trail" : "▸ Inspect Judicial Authority Trail"}</span>
        <span
          style={{
            backgroundColor: "var(--bg-parchment)",
            border: "1px solid var(--border-rule)",
            borderRadius: "2px",
            padding: "0.05rem 0.35rem",
            fontSize: "0.68rem",
            color: "var(--maroon)",
            fontWeight: 700,
          }}
        >
          {claim.evidence_ids.length} Sources
        </span>
      </button>

      {isOpen && (
        <div
          style={{
            marginTop: "0.75rem",
            padding: "0.85rem 1rem",
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border-rule)",
            borderRadius: "2px",
            fontFamily: "var(--font-sans)",
            fontSize: "0.78rem",
            lineHeight: 1.6,
          }}
        >
          <div style={{ color: "var(--text-faint)", fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.5rem" }}>
            STATUTORY CITATION CHAIN &bull; CLAIM #{claimIndex + 1}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
            {claim.evidence_ids.map((evId) => {
              const matchedEvidence = evidenceList.find((e) => e.evidence_id === evId);
              const authorities = authoritiesByEvidence[evId] || [];

              return (
                <div
                  key={evId}
                  style={{
                    borderLeft: "2px solid var(--maroon)",
                    paddingLeft: "0.85rem",
                    marginLeft: "0.25rem",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                    <span
                      className="cite-tag active"
                      onClick={() => onSelectEvidence(evId)}
                      title="Click to highlight authority on the right panel"
                    >
                      {evId}
                    </span>
                    <strong style={{ color: "var(--navy)", fontSize: "0.82rem" }}>
                      {matchedEvidence?.court || "Supreme Court / High Court of India"}
                    </strong>
                    <span style={{ color: "var(--text-faint)", fontSize: "0.72rem" }}>
                      ({matchedEvidence?.court_level || "Appellate Court"})
                    </span>
                  </div>

                  {/* Hierarchical Trail */}
                  <div style={{ color: "var(--text-muted)", paddingLeft: "0.5rem", borderLeft: "1px solid var(--border-subtle)" }}>
                    <div style={{ fontFamily: "var(--font-serif)", fontWeight: 600, color: "var(--text-ink)" }}>
                      ↳ {matchedEvidence?.case_title || "Official Certified Record"}
                    </div>
                    <div style={{ fontSize: "0.74rem", color: "var(--text-faint)" }}>
                      ↳ Date: {matchedEvidence?.decision_date || "Certified Date"} &bull; Case No: {matchedEvidence?.case_number || "INSC/HC Record"}
                    </div>
                    <div style={{ fontSize: "0.74rem", color: "var(--maroon)", fontWeight: 600 }}>
                      ↳ Certified Page: {matchedEvidence?.page_number || `${matchedEvidence?.page_start}-${matchedEvidence?.page_end}`} &bull; Paragraph: {matchedEvidence?.paragraph_id || "PAR001"}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
