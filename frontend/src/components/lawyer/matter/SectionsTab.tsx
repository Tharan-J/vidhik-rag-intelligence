"use client";

import React from "react";
import { Matter, SectionRef } from "@/lib/types/matter";
import { ProvenanceBadge } from "./ProvenanceBadge";
import { BookOpen, FileText, CheckCircle2, ShieldCheck } from "lucide-react";

interface SectionsTabProps {
  matter: Matter;
  onUpdateSections?: (sections: SectionRef[]) => void;
}

export function SectionsTab({ matter, onUpdateSections }: SectionsTabProps) {
  const [sections, setSections] = React.useState<SectionRef[]>(matter.sections || []);
  const [showAddModal, setShowAddModal] = React.useState(false);
  const [sectionNumber, setSectionNumber] = React.useState("");
  const [actName, setActName] = React.useState("");
  const [applicability, setApplicability] = React.useState<SectionRef["applicability"]>("SECTION_ALLEGED_BY_PARTY");
  const [description, setDescription] = React.useState("");

  React.useEffect(() => {
    setSections(matter.sections || []);
  }, [matter.id, matter.sections]);

  const handleAddSection = (e: React.FormEvent) => {
    e.preventDefault();
    if (!sectionNumber.trim() || !actName.trim()) return;

    const newSec: SectionRef = {
      id: `SEC-NEW-${Date.now()}`,
      section: sectionNumber.trim(),
      act: actName.trim(),
      applicability,
      description: description.trim() || "Cited in pleadings before the bench.",
      sourceDocument: "User Entry / Pleadings Record",
      provenance: "USER_PROVIDED",
      headingVerification: "NOT_VERIFIED",
    };

    const updated = [...sections, newSec];
    setSections(updated);
    if (onUpdateSections) onUpdateSections(updated);

    setShowAddModal(false);
    setSectionNumber("");
    setActName("");
    setDescription("");
  };

  const handleUpdateApplicability = (secId: string, newApp: SectionRef["applicability"]) => {
    const updated = sections.map((s) => (s.id === secId ? { ...s, applicability: newApp } : s));
    setSections(updated);
    if (onUpdateSections) onUpdateSections(updated);
  };

  const handleDeleteSection = (secId: string) => {
    const updated = sections.filter((s) => s.id !== secId);
    setSections(updated);
    if (onUpdateSections) onUpdateSections(updated);
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
            Statutory Provisions on Record
          </h3>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: 0 }}>
            Statutory provisions explicitly cited in the verified matter record and judicial authorities.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.4rem",
            padding: "0.45rem 0.95rem",
            fontSize: "0.82rem",
            fontWeight: 600,
            backgroundColor: "var(--maroon)",
            color: "#FFFFFF",
            border: "none",
            borderRadius: "2px",
            cursor: "pointer",
          }}
        >
          <BookOpen size={14} />
          <span>Record Statutory Provision</span>
        </button>
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
              maxWidth: "520px",
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
              Record Statutory Provision
            </h4>
            <form onSubmit={handleAddSection} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "var(--text-ink)", marginBottom: "0.3rem" }}>
                  Section / Rule Number *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Section 5 or Order VII Rule 11"
                  value={sectionNumber}
                  onChange={(e) => setSectionNumber(e.target.value)}
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
                  Act / Code / Statute *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Limitation Act, 1963"
                  value={actName}
                  onChange={(e) => setActName(e.target.value)}
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
                  Evidentiary Applicability Classification
                </label>
                <select
                  value={applicability}
                  onChange={(e) => setApplicability(e.target.value as any)}
                  style={{
                    width: "100%",
                    padding: "0.5rem 0.75rem",
                    fontSize: "0.85rem",
                    border: "1px solid var(--border-rule)",
                    borderRadius: "2px",
                    backgroundColor: "var(--bg-parchment)",
                  }}
                >
                  <option value="SECTION_ALLEGED_BY_PARTY">SECTION ALLEGED BY PARTY (Pleadings)</option>
                  <option value="SECTION_MENTIONED">SECTION MENTIONED (Incidental Reference)</option>
                  <option value="SECTION_APPLIED">SECTION APPLIED (Substantive Precedent)</option>
                  <option value="SECTION_HELD_APPLICABLE">SECTION HELD APPLICABLE (Judicial Finding)</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "var(--text-ink)", marginBottom: "0.3rem" }}>
                  Context / Quotation
                </label>
                <textarea
                  rows={3}
                  placeholder="Relevant statutory text or pleading extract..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
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
                  Save Statutory Provision
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {sections.map((sec) => (
          <div
            key={sec.id}
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
                marginBottom: "0.75rem",
                flexWrap: "wrap",
                gap: "0.5rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                <span
                  style={{
                    fontSize: "0.78rem",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 700,
                    color: "var(--maroon)",
                    backgroundColor: "var(--maroon-faint)",
                    padding: "0.15rem 0.5rem",
                    borderRadius: "2px",
                    border: "1px solid var(--maroon-border)",
                  }}
                >
                  {sec.section}
                </span>

                <span
                  style={{
                    fontSize: "0.88rem",
                    fontWeight: 700,
                    color: "var(--navy)",
                  }}
                >
                  {sec.act}
                </span>

                {sec.applicability && (
                  <span
                    style={{
                      fontSize: "0.65rem",
                      fontFamily: "var(--font-mono)",
                      fontWeight: 700,
                      color:
                        sec.applicability === "SECTION_APPLIED" || sec.applicability === "SECTION_HELD_APPLICABLE"
                          ? "#065F46"
                          : sec.applicability === "SECTION_ALLEGED_BY_PARTY"
                          ? "#4338CA"
                          : "#4B5563",
                      backgroundColor:
                        sec.applicability === "SECTION_APPLIED" || sec.applicability === "SECTION_HELD_APPLICABLE"
                          ? "#D1FAE5"
                          : sec.applicability === "SECTION_ALLEGED_BY_PARTY"
                          ? "#EEF2FF"
                          : "#F3F4F6",
                      padding: "0.1rem 0.4rem",
                      borderRadius: "2px",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    {sec.applicability.replace(/_/g, " ")}
                  </span>
                )}
              </div>

              <ProvenanceBadge
                type={sec.provenance || "SOURCE_EXPLICIT"}
                sourceDoc={sec.sourceDocument}
                page={sec.page}
                paragraph={sec.paragraph}
              />
            </div>

            {sec.heading ? (
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem", flexWrap: "wrap" }}>
                <h4
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.1rem",
                    fontWeight: 600,
                    color: "var(--text-ink)",
                    margin: 0,
                  }}
                >
                  {sec.heading}
                </h4>
                {sec.headingVerification === "NOT_VERIFIED" && (
                  <span style={{ fontSize: "0.68rem", color: "var(--text-faint)", fontStyle: "italic" }}>
                    (Heading not verified from official statute gazette)
                  </span>
                )}
              </div>
            ) : (
              <div style={{ fontSize: "0.75rem", color: "var(--text-faint)", fontStyle: "italic", marginBottom: "0.5rem" }}>
                No statutory heading established from primary source; unverified heading withheld.
              </div>
            )}

            <div
              style={{
                backgroundColor: "var(--bg-parchment)",
                border: "1px solid var(--border-rule)",
                borderRadius: "2px",
                padding: "1.15rem 1.35rem",
                marginBottom: "1rem",
              }}
            >
              <p
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "0.98rem",
                  lineHeight: 1.65,
                  color: "var(--text-ink)",
                  fontStyle: "italic",
                  margin: 0,
                }}
              >
                “{sec.description}”
              </p>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: "0.5rem",
                paddingTop: "0.5rem",
                borderTop: "1px dashed var(--border-rule)",
                fontSize: "0.76rem",
                color: "var(--text-faint)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <FileText size={13} color="var(--maroon)" />
                <span>Cited in: {sec.sourceDocument} {sec.page ? `(Page ${sec.page})` : ""}</span>
              </div>

              {onUpdateSections && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <label style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Status:</label>
                  <select
                    value={sec.applicability || "SECTION_MENTIONED"}
                    onChange={(e) => handleUpdateApplicability(sec.id, e.target.value as any)}
                    style={{
                      fontSize: "0.72rem",
                      padding: "0.15rem 0.4rem",
                      borderRadius: "2px",
                      border: "1px solid var(--border-rule)",
                      backgroundColor: "var(--bg-sheet)",
                      color: "var(--text-ink)",
                      cursor: "pointer",
                    }}
                  >
                    <option value="SECTION_ALLEGED_BY_PARTY">Alleged by Party</option>
                    <option value="SECTION_MENTIONED">Mentioned</option>
                    <option value="SECTION_APPLIED">Applied</option>
                    <option value="SECTION_HELD_APPLICABLE">Held Applicable</option>
                  </select>

                  <button
                    onClick={() => handleDeleteSection(sec.id)}
                    title="Remove statutory section"
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
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
