"use client";

import React from "react";
import { Matter, AuthorityRef } from "@/lib/types/matter";
import { Scale, FileText, CheckCircle2, ExternalLink, Bookmark } from "lucide-react";
import { ProvenanceBadge } from "./ProvenanceBadge";

interface AuthoritiesTabProps {
  matter: Matter;
  onNavigateToResearch: () => void;
  onUpdateAuthorities?: (authorities: AuthorityRef[]) => void;
}

export function AuthoritiesTab({ matter, onNavigateToResearch, onUpdateAuthorities }: AuthoritiesTabProps) {
  const [authorities, setAuthorities] = React.useState<AuthorityRef[]>(matter.authorities || []);
  const [showAddModal, setShowAddModal] = React.useState(false);
  const [caseTitle, setCaseTitle] = React.useState("");
  const [caseNumber, setCaseNumber] = React.useState("");
  const [court, setCourt] = React.useState("");
  const [year, setYear] = React.useState("");
  const [relevance, setRelevance] = React.useState("");
  const [supportingEvidence, setSupportingEvidence] = React.useState("");

  React.useEffect(() => {
    setAuthorities(matter.authorities || []);
  }, [matter.id, matter.authorities]);

  const handleAddAuthority = (e: React.FormEvent) => {
    e.preventDefault();
    if (!caseTitle.trim()) return;

    const newAuth: AuthorityRef = {
      id: `AUTH-NEW-${Date.now()}`,
      caseTitle: caseTitle.trim(),
      caseNumber: caseNumber.trim() || "Citation Pending",
      court: court.trim() || "Supreme Court of India",
      year: year.trim() || String(new Date().getFullYear()),
      relevance: relevance.trim() || "Precedent cited in support of matter issues.",
      supportingEvidence: supportingEvidence.trim() || "Judicial finding excerpt on record.",
      presence: "EXTERNAL_REFERENCE",
      verificationStatus: "unverified",
      independentVerification: "NOT_VERIFIED",
      provenance: "USER_PROVIDED",
    };

    const updated = [...authorities, newAuth];
    setAuthorities(updated);
    if (onUpdateAuthorities) onUpdateAuthorities(updated);

    setShowAddModal(false);
    setCaseTitle("");
    setCaseNumber("");
    setCourt("");
    setYear("");
    setRelevance("");
    setSupportingEvidence("");
  };

  const handleDeleteAuthority = (authId: string) => {
    const updated = authorities.filter((a) => a.id !== authId);
    setAuthorities(updated);
    if (onUpdateAuthorities) onUpdateAuthorities(updated);
  };

  return (
    <div style={{ maxWidth: "980px" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "2rem",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <h3
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "1.45rem",
              fontWeight: 700,
              color: "var(--text-ink)",
              marginBottom: "0.25rem",
            }}
          >
            Relevant Authorities & Judicial Precedents
          </h3>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: 0 }}>
            Judgments linked to this matter through Vidhik's hybrid retrieval and evidence audit.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <button
            onClick={() => setShowAddModal(true)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.45rem",
              padding: "0.5rem 0.95rem",
              backgroundColor: "var(--navy)",
              color: "#FFFFFF",
              borderRadius: "2px",
              fontSize: "0.82rem",
              fontWeight: 600,
              border: "none",
              cursor: "pointer",
            }}
          >
            <Bookmark size={14} />
            <span>Record Authority</span>
          </button>

          <button
            onClick={onNavigateToResearch}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.45rem",
              padding: "0.5rem 1rem",
              backgroundColor: "var(--maroon)",
              color: "#FFFFFF",
              borderRadius: "2px",
              fontSize: "0.82rem",
              fontWeight: 600,
              border: "none",
              cursor: "pointer",
            }}
          >
            <Scale size={14} />
            <span>Research New Authorities</span>
          </button>
        </div>
      </div>

      {showAddModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(26, 26, 26, 0.65)",
            backdropFilter: "blur(2px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "1rem",
          }}
          onClick={() => setShowAddModal(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              backgroundColor: "var(--bg-sheet)",
              border: "1.5px solid var(--border-dark)",
              borderRadius: "4px",
              padding: "2rem",
              width: "100%",
              maxWidth: "540px",
              boxShadow: "var(--shadow-sheet)",
            }}
          >
            <h4
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1.25rem",
                fontWeight: 700,
                color: "var(--text-ink)",
                marginBottom: "1rem",
              }}
            >
              Record Judicial Precedent / Authority
            </h4>
            <form onSubmit={handleAddAuthority} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "var(--text-ink)", marginBottom: "0.3rem" }}>
                  Case Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Union of India v. Popular Construction Co."
                  value={caseTitle}
                  onChange={(e) => setCaseTitle(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "0.5rem 0.75rem",
                    fontSize: "0.85rem",
                    border: "1px solid var(--border-rule)",
                    borderRadius: "2px",
                    backgroundColor: "var(--bg-parchment)",
                  }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "var(--text-ink)", marginBottom: "0.3rem" }}>
                    Citation / Case No.
                  </label>
                  <input
                    type="text"
                    placeholder="(2001) 8 SCC 470"
                    value={caseNumber}
                    onChange={(e) => setCaseNumber(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "0.5rem 0.75rem",
                      fontSize: "0.85rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      backgroundColor: "var(--bg-parchment)",
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "var(--text-ink)", marginBottom: "0.3rem" }}>
                    Court & Year
                  </label>
                  <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "0.4rem" }}>
                    <input
                      type="text"
                      placeholder="Supreme Court"
                      value={court}
                      onChange={(e) => setCourt(e.target.value)}
                      style={{
                        padding: "0.5rem 0.5rem",
                        fontSize: "0.85rem",
                        border: "1px solid var(--border-rule)",
                        borderRadius: "2px",
                        backgroundColor: "var(--bg-parchment)",
                      }}
                    />
                    <input
                      type="text"
                      placeholder="2001"
                      value={year}
                      onChange={(e) => setYear(e.target.value)}
                      style={{
                        padding: "0.5rem 0.5rem",
                        fontSize: "0.85rem",
                        border: "1px solid var(--border-rule)",
                        borderRadius: "2px",
                        backgroundColor: "var(--bg-parchment)",
                      }}
                    />
                  </div>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "var(--text-ink)", marginBottom: "0.3rem" }}>
                  Doctrinal Relevance *
                </label>
                <textarea
                  rows={2}
                  required
                  placeholder="How this precedent applies to the matter issues..."
                  value={relevance}
                  onChange={(e) => setRelevance(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "0.5rem 0.75rem",
                    fontSize: "0.85rem",
                    border: "1px solid var(--border-rule)",
                    borderRadius: "2px",
                    backgroundColor: "var(--bg-parchment)",
                  }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "var(--text-ink)", marginBottom: "0.3rem" }}>
                  Judicial Finding Excerpt (Optional)
                </label>
                <textarea
                  rows={2}
                  placeholder="Verbatim quote or holding from judgment..."
                  value={supportingEvidence}
                  onChange={(e) => setSupportingEvidence(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "0.5rem 0.75rem",
                    fontSize: "0.85rem",
                    border: "1px solid var(--border-rule)",
                    borderRadius: "2px",
                    backgroundColor: "var(--bg-parchment)",
                    fontFamily: "var(--font-serif)",
                  }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "0.5rem" }}>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  style={{
                    padding: "0.45rem 1rem",
                    fontSize: "0.82rem",
                    border: "1px solid var(--border-rule)",
                    backgroundColor: "transparent",
                    color: "var(--text-ink)",
                    borderRadius: "2px",
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{
                    padding: "0.45rem 1.15rem",
                    fontSize: "0.82rem",
                    fontWeight: 600,
                    backgroundColor: "var(--maroon)",
                    color: "#FFFFFF",
                    border: "none",
                    borderRadius: "2px",
                    cursor: "pointer",
                  }}
                >
                  Record Authority
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {authorities.map((auth) => (
          <div
            key={auth.id}
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
                alignItems: "flex-start",
                justifyContent: "space-between",
                marginBottom: "0.75rem",
                flexWrap: "wrap",
                gap: "0.5rem",
              }}
            >
              <div>
                <span
                  style={{
                    fontSize: "0.72rem",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 700,
                    color: "var(--maroon)",
                    backgroundColor: "var(--maroon-faint)",
                    padding: "0.15rem 0.5rem",
                    borderRadius: "2px",
                    border: "1px solid var(--maroon-border)",
                    marginRight: "0.5rem",
                  }}
                >
                  {auth.caseNumber}
                </span>

                <span
                  style={{
                    fontSize: "0.78rem",
                    fontWeight: 600,
                    color: "var(--navy)",
                  }}
                >
                  {auth.court} ({auth.year})
                </span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                {auth.presence && (
                  <span
                    style={{
                      fontSize: "0.65rem",
                      fontFamily: "var(--font-mono)",
                      fontWeight: 700,
                      padding: "0.1rem 0.4rem",
                      borderRadius: "2px",
                      backgroundColor: auth.presence === "FOUND_IN_SOURCE" ? "#EBF7F0" : "#F3F4F6",
                      color: auth.presence === "FOUND_IN_SOURCE" ? "#10754A" : "#4B5563",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    {auth.presence.replace(/_/g, " ")}
                  </span>
                )}

                {auth.independentVerification && (
                  <span
                    style={{
                      fontSize: "0.65rem",
                      fontFamily: "var(--font-mono)",
                      fontWeight: 700,
                      padding: "0.1rem 0.4rem",
                      borderRadius: "2px",
                      backgroundColor:
                        auth.independentVerification === "VERIFIED"
                          ? "#EBF7F0"
                          : auth.independentVerification === "FLAGGED_HALLUCINATION"
                          ? "#FEF2F2"
                          : "#F3F4F6",
                      color:
                        auth.independentVerification === "VERIFIED"
                          ? "#10754A"
                          : auth.independentVerification === "FLAGGED_HALLUCINATION"
                          ? "#B91C1C"
                          : "#6B7280",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    INDEP VERIF: {auth.independentVerification.replace(/_/g, " ")}
                  </span>
                )}

                <ProvenanceBadge
                  type={
                    auth.verificationStatus === "flagged_hallucination" ||
                    auth.independentVerification === "FLAGGED_HALLUCINATION" ||
                    auth.authorityStatus === "FLAGGED_FAKE"
                      ? "flagged_hallucination"
                      : auth.independentVerification === "VERIFIED"
                      ? "INDEPENDENTLY_VERIFIED"
                      : "SOURCE_EXPLICIT"
                  }
                  sourceDoc={auth.sourceFile}
                  page={auth.page}
                  paragraph={auth.paragraph}
                />

                {auth.evidenceId && (
                  <span
                    style={{
                      fontSize: "0.7rem",
                      fontFamily: "var(--font-mono)",
                      padding: "0.15rem 0.45rem",
                      backgroundColor: "var(--status-supported-bg)",
                      color: "var(--status-supported-text)",
                      border: "1px solid var(--status-supported-border)",
                      borderRadius: "2px",
                      fontWeight: 700,
                    }}
                  >
                    LINKED EVIDENCE [{auth.evidenceId}]
                  </span>
                )}
              </div>
            </div>

            <h4
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1.22rem",
                fontWeight: 700,
                color: "var(--text-ink)",
                marginBottom: "0.6rem",
                lineHeight: 1.35,
              }}
            >
              {auth.caseTitle}
            </h4>

            <p
              style={{
                fontSize: "0.88rem",
                lineHeight: 1.55,
                color: "var(--text-muted)",
                marginBottom: "1.25rem",
              }}
            >
              <strong style={{ color: "var(--text-ink)" }}>Doctrinal Relevance: </strong>
              {auth.relevance}
            </p>

            {auth.supportingEvidence && (
              <div
                style={{
                  backgroundColor: "var(--bg-parchment)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "2px",
                  padding: "1rem 1.25rem",
                  marginBottom: "1rem",
                }}
              >
                <div
                  style={{
                    fontSize: "0.72rem",
                    fontFamily: "var(--font-mono)",
                    color: "var(--maroon)",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    marginBottom: "0.25rem",
                  }}
                >
                  Judicial Finding Excerpt
                </div>
                <p
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "0.92rem",
                    lineHeight: 1.6,
                    color: "var(--text-ink)",
                    fontStyle: "italic",
                    margin: 0,
                  }}
                >
                  “{auth.supportingEvidence}”
                </p>
              </div>
            )}

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                paddingTop: "0.75rem",
                borderTop: "1px solid var(--border-subtle)",
                fontSize: "0.75rem",
                color: "var(--text-faint)",
                flexWrap: "wrap",
                gap: "0.5rem",
              }}
            >
              <div>
                <span>Spatial Coordinate: </span>
                <span style={{ fontFamily: "var(--font-mono)", color: "var(--navy)", fontWeight: 600 }}>
                  Page {auth.page || "N/A"}, {auth.paragraph || "N/A"}
                </span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.3rem", color: "var(--maroon)" }}>
                  <span>Certified Judgment PDF</span>
                  <ExternalLink size={12} />
                </div>
                {onUpdateAuthorities && (
                  <button
                    onClick={() => handleDeleteAuthority(auth.id)}
                    title="Remove authority"
                    style={{
                      background: "none",
                      border: "none",
                      color: "var(--text-faint)",
                      cursor: "pointer",
                      padding: "0.2rem",
                      display: "inline-flex",
                      alignItems: "center",
                    }}
                  >
                    ✕
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
