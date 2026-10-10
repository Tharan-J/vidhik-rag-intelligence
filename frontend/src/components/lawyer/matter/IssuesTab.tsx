"use client";

import React, { useState, useEffect } from "react";
import { Matter, MatterIssue } from "@/lib/types/matter";
import { ProvenanceBadge } from "./ProvenanceBadge";
import {
  FileText,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Plus,
  Trash2,
  Scale,
  BookOpen,
  Check,
} from "lucide-react";

interface IssuesTabProps {
  matter: Matter;
  onUpdateIssues?: (issues: MatterIssue[]) => void;
}

export function IssuesTab({ matter, onUpdateIssues }: IssuesTabProps) {
  const [issues, setIssues] = useState<MatterIssue[]>(matter.issues || []);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    setIssues(matter.issues || []);
  }, [matter.id, matter.issues]);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");

  const handleConfirmIssue = (issueId: string) => {
    const updated = issues.map((i) =>
      i.id === issueId ? { ...i, confirmed: true, source: "lawyer" as const, provenance: "USER_PROVIDED" as const } : i
    );
    setIssues(updated);
    if (onUpdateIssues) onUpdateIssues(updated);
  };

  const handleDeleteIssue = (issueId: string) => {
    const updated = issues.filter((i) => i.id !== issueId);
    setIssues(updated);
    if (onUpdateIssues) onUpdateIssues(updated);
  };

  const handleCreateIssue = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle) return;

    const newIssue: MatterIssue = {
      id: `ISS-${Date.now()}`,
      matterId: matter.id,
      issueNumber: `Issue ${String(issues.length + 1).padStart(2, "0")}`,
      title: newTitle,
      description: newDesc,
      source: "lawyer",
      confirmed: true,
      provenance: "USER_PROVIDED",
      relatedDocuments: matter.documents[0] ? [matter.documents[0].name] : [],
      relatedSections: [],
      relatedAuthorities: [],
    };

    const updated = [...issues, newIssue];
    setIssues(updated);
    if (onUpdateIssues) onUpdateIssues(updated);
    setShowAddModal(false);
    setNewTitle("");
    setNewDesc("");
  };

  const handleSuggestWithGemini = async () => {
    setLoadingSuggestions(true);
    try {
      const res = await fetch("/api/ai/issue-suggestion", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          matterTitle: matter.title,
          documentSnippets: matter.documents.map(
            (d) =>
              `${d.name}: ${d.extractedMetadata?.important_points?.join("; ") || "Pleadings record"}`
          ),
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const suggestedList = data.issues || [];
        const newSuggestedIssues: MatterIssue[] = suggestedList.map(
          (s: any, idx: number) => ({
            id: `ISS-SUGGEST-${Date.now()}-${idx}`,
            matterId: matter.id,
            issueNumber: `Issue ${String(issues.length + idx + 1).padStart(2, "0")}`,
            title: s.title,
            description: s.description || "Candidate issue suggested by Gemini document intelligence.",
            source: "ai_analysis",
            confirmed: false,
            provenance: "AI_ANALYSIS",
            relatedDocuments: matter.documents[0] ? [matter.documents[0].name] : [],
            relatedSections: s.relatedSections || [],
            relatedAuthorities: [],
          })
        );

        const updated = [...issues, ...newSuggestedIssues];
        setIssues(updated);
        if (onUpdateIssues) onUpdateIssues(updated);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  return (
    <div style={{ maxWidth: "980px" }}>
      {/* Header and Action Controls */}
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
            Issues for Adjudication
          </h3>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: 0 }}>
            Structured legal questions requiring determination by the court or trial counsel.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <button
            onClick={handleSuggestWithGemini}
            disabled={loadingSuggestions}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
              padding: "0.45rem 0.85rem",
              fontSize: "0.8rem",
              fontWeight: 600,
              color: "var(--maroon)",
              backgroundColor: "var(--maroon-faint)",
              border: "1px solid var(--maroon-border)",
              borderRadius: "2px",
              cursor: loadingSuggestions ? "wait" : "pointer",
            }}
          >
            <Sparkles size={13} />
            <span>{loadingSuggestions ? "Analyzing..." : "Suggest Issues via Gemini"}</span>
          </button>

          <button
            onClick={() => setShowAddModal(true)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
              padding: "0.45rem 1rem",
              fontSize: "0.82rem",
              fontWeight: 600,
              backgroundColor: "var(--maroon)",
              color: "#FFFFFF",
              border: "none",
              borderRadius: "2px",
              cursor: "pointer",
            }}
          >
            <Plus size={14} />
            <span>Add Confirmed Issue</span>
          </button>
        </div>
      </div>

      {/* Issues List */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {issues.map((issue) => {
          const isAi = issue.source === "ai_analysis" || issue.source === "ai_suggestion";
          const isCourt = issue.source === "court_explicit";
          const isParty = issue.source === "party_argument";
          const isUnconfirmed = isAi && !issue.confirmed;

          return (
            <div
              key={issue.id}
              className="paper-card"
              style={{
                padding: "1.75rem",
                backgroundColor: "var(--bg-sheet)",
                borderRadius: "3px",
                border: isUnconfirmed
                  ? "1.5px dashed #D97706"
                  : isCourt
                  ? "1.5px solid #10754A"
                  : "1.5px solid var(--border-rule)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  justifyContent: "space-between",
                  marginBottom: "0.85rem",
                  flexWrap: "wrap",
                  gap: "0.75rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      color: isUnconfirmed ? "#B45309" : isCourt ? "#10754A" : "var(--navy)",
                      backgroundColor: isUnconfirmed ? "#FFFBEB" : isCourt ? "#EBF7F0" : "var(--bg-parchment)",
                      padding: "0.2rem 0.55rem",
                      borderRadius: "2px",
                      border: `1px solid ${isUnconfirmed ? "#FDE68A" : isCourt ? "#B4E3CB" : "var(--border-rule)"}`,
                    }}
                  >
                    {issue.issueNumber}
                  </span>

                  <ProvenanceBadge
                    type={
                      issue.provenance ||
                      (isCourt
                        ? "court_explicit"
                        : isParty
                        ? "party_argument"
                        : isAi
                        ? "ai_analysis"
                        : "USER_PROVIDED")
                    }
                  />

                  {issue.confirmed ? (
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.3rem",
                        fontSize: "0.7rem",
                        color: "#10754A",
                        fontWeight: 600,
                        backgroundColor: "#EBF7F0",
                        padding: "0.15rem 0.45rem",
                        borderRadius: "2px",
                        border: "1px solid #B4E3CB",
                      }}
                    >
                      <CheckCircle2 size={11} />
                      <span>{isCourt ? "Framed in Order" : "Confirmed by Counsel"}</span>
                    </span>
                  ) : isAi ? (
                    <span
                      style={{
                        fontSize: "0.7rem",
                        color: "#B45309",
                        fontWeight: 600,
                        backgroundColor: "#FFFBEB",
                        padding: "0.15rem 0.45rem",
                        borderRadius: "2px",
                        border: "1px dashed #FDE68A",
                      }}
                    >
                      Pending Counsel Confirmation
                    </span>
                  ) : null}
                </div>

                {/* Issue Actions */}
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  {isUnconfirmed && (
                    <button
                      onClick={() => handleConfirmIssue(issue.id)}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.35rem",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        backgroundColor: "var(--status-supported-bg)",
                        color: "var(--status-supported-text)",
                        border: "1px solid var(--status-supported-border)",
                        padding: "0.25rem 0.65rem",
                        borderRadius: "2px",
                        cursor: "pointer",
                      }}
                    >
                      <Check size={12} />
                      <span>Confirm as Counsel</span>
                    </button>
                  )}

                  <button
                    onClick={() => handleDeleteIssue(issue.id)}
                    title="Dismiss or delete issue"
                    style={{
                      background: "none",
                      border: "none",
                      color: "var(--text-faint)",
                      cursor: "pointer",
                      padding: "0.3rem",
                    }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              {/* Issue Question */}
              <h4
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "1.2rem",
                  fontWeight: 700,
                  color: "var(--text-ink)",
                  lineHeight: 1.4,
                  marginBottom: "0.6rem",
                }}
              >
                {issue.title}
              </h4>

              {issue.description && (
                <p
                  style={{
                    fontSize: "0.88rem",
                    lineHeight: 1.55,
                    color: "var(--text-muted)",
                    marginBottom: "1.25rem",
                  }}
                >
                  {issue.description}
                </p>
              )}

              {/* Related metadata links */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "1.5rem",
                  paddingTop: "0.85rem",
                  borderTop: "1px solid var(--border-subtle)",
                  fontSize: "0.78rem",
                  color: "var(--text-faint)",
                  flexWrap: "wrap",
                }}
              >
                {issue.relatedSections && issue.relatedSections.length > 0 ? (
                  <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                    <BookOpen size={13} color="var(--maroon)" />
                    <span style={{ fontWeight: 600, color: "var(--text-ink)" }}>Sections:</span>
                    <span>{issue.relatedSections.join(", ")}</span>
                  </div>
                ) : null}

                {issue.relatedDocuments && issue.relatedDocuments.length > 0 ? (
                  <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                    <FileText size={13} color="var(--navy)" />
                    <span style={{ fontWeight: 600, color: "var(--text-ink)" }}>Docs:</span>
                    <span>{issue.relatedDocuments.join(", ")}</span>
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal: Add Confirmed Issue */}
      {showAddModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(30, 32, 36, 0.45)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "1rem",
          }}
        >
          <div
            className="paper-card"
            style={{
              maxWidth: "540px",
              width: "100%",
              backgroundColor: "var(--bg-sheet)",
              borderRadius: "4px",
              padding: "2rem",
            }}
          >
            <h3
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1.35rem",
                fontWeight: 700,
                color: "var(--text-ink)",
                marginBottom: "1.25rem",
              }}
            >
              Add Confirmed Matter Issue
            </h3>

            <form onSubmit={handleCreateIssue}>
              <div style={{ display: "flex", flexDirection: "column", gap: "1.1rem" }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.3rem" }}>
                    Issue Formulation (Question)
                  </label>
                  <textarea
                    rows={3}
                    required
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g. Whether Section 29(2) of the Limitation Act excludes CPC Order XLI Rule 3A?"
                    style={{
                      width: "100%",
                      padding: "0.65rem 0.8rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      fontSize: "0.88rem",
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.3rem" }}>
                    Factual Basis / Context
                  </label>
                  <textarea
                    rows={2}
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    placeholder="Context from trial court proceedings or grounds of appeal..."
                    style={{
                      width: "100%",
                      padding: "0.65rem 0.8rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      fontSize: "0.88rem",
                    }}
                  />
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "0.5rem" }}>
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    style={{ padding: "0.55rem 1rem", border: "1px solid var(--border-rule)", borderRadius: "2px", background: "none" }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    style={{
                      padding: "0.55rem 1.3rem",
                      backgroundColor: "var(--maroon)",
                      color: "#FFFFFF",
                      borderRadius: "2px",
                      fontWeight: 600,
                      border: "none",
                    }}
                  >
                    Add Issue
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
