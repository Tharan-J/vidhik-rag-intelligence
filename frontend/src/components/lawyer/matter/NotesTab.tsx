"use client";

import React, { useState, useEffect } from "react";
import { Matter, MatterNote } from "@/lib/types/matter";
import { ProvenanceBadge } from "./ProvenanceBadge";
import { BookOpen, Plus, Trash2, Sparkles, Tag, CheckCircle2 } from "lucide-react";

interface NotesTabProps {
  matter: Matter;
  onUpdateNotes?: (notes: MatterNote[]) => void;
}

export function NotesTab({ matter, onUpdateNotes }: NotesTabProps) {
  const [notes, setNotes] = useState<MatterNote[]>(matter.notes || []);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newTags, setNewTags] = useState("");
  const [structuring, setStructuring] = useState(false);

  useEffect(() => {
    setNotes(matter.notes || []);
  }, [matter.id, matter.notes]);

  const handleCreateNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle || !newContent) return;

    const newNote: MatterNote = {
      id: `NOTE-${Date.now()}`,
      matterId: matter.id,
      title: newTitle,
      content: newContent,
      updatedAt: new Date().toISOString(),
      tags: newTags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
    };

    const updated = [newNote, ...notes];
    setNotes(updated);
    if (onUpdateNotes) onUpdateNotes(updated);
    setShowAddModal(false);
    setNewTitle("");
    setNewContent("");
    setNewTags("");
  };

  const handleDeleteNote = (id: string) => {
    const updated = notes.filter((n) => n.id !== id);
    setNotes(updated);
    if (onUpdateNotes) onUpdateNotes(updated);
  };

  const handleStructureWithAI = async () => {
    if (!newContent.trim()) return;
    setStructuring(true);
    try {
      // In a real call we invoke our server endpoint or format
      const structuredPoints = newContent
        .split("\n")
        .filter((line) => line.trim())
        .map((l) => `• ${l.replace(/^[-*•]\s*/, "")}`);

      setNewContent(
        `STRATEGIC BRIEFING POINTS:\n${structuredPoints.join("\n")}\n\nACTION ITEMS:\n1. Verify hospital discharge summary registry timestamp\n2. Prepare citations for Division Bench`
      );
      if (!newTitle) {
        setNewTitle("Strategy Note — Procedural & Evidentiary Points");
      }
      if (!newTags) {
        setNewTags("Strategy, Evidence, Hearing");
      }
    } finally {
      setStructuring(false);
    }
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
            Counsel Strategy Notes & Briefs
          </h3>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: 0 }}>
            Confidential workspace notes, hearing briefs, and examination strategies.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
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
          <Plus size={14} />
          <span>New Counsel Note</span>
        </button>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {notes.map((note) => (
          <div
            key={note.id}
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
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
                <h4
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.25rem",
                    fontWeight: 700,
                    color: "var(--text-ink)",
                    margin: 0,
                  }}
                >
                  {note.title}
                </h4>

                <ProvenanceBadge
                  type={
                    note.noteType ||
                    note.provenance ||
                    "USER_NOTE"
                  }
                  labelOverride={
                    note.noteType
                      ? note.noteType.replace(/_/g, " ")
                      : undefined
                  }
                />
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <span style={{ fontSize: "0.72rem", color: "var(--text-faint)" }}>
                  {note.updatedAt
                    ? note.updatedAt.slice(0, 10)
                    : note.createdAt
                    ? note.createdAt.slice(0, 10)
                    : matter.createdAt || "Verified Record"}
                </span>
                <button
                  onClick={() => handleDeleteNote(note.id)}
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--text-faint)",
                    cursor: "pointer",
                    padding: "0.2rem",
                  }}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>

            <p
              style={{
                fontSize: "0.9rem",
                lineHeight: 1.6,
                color: "var(--text-ink)",
                whiteSpace: "pre-line",
                marginBottom: "1rem",
              }}
            >
              {note.content}
            </p>

            {note.tags && note.tags.length > 0 && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.4rem",
                  borderTop: "1px solid var(--border-subtle)",
                  paddingTop: "0.75rem",
                }}
              >
                <Tag size={12} color="var(--maroon)" />
                {note.tags.map((t, idx) => (
                  <span
                    key={idx}
                    style={{
                      fontSize: "0.72rem",
                      padding: "0.1rem 0.45rem",
                      backgroundColor: "var(--bg-parchment)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "2px",
                      color: "var(--navy)",
                    }}
                  >
                    #{t}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Modal: New Note */}
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
              maxWidth: "560px",
              width: "100%",
              backgroundColor: "var(--bg-sheet)",
              borderRadius: "4px",
              padding: "2rem",
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
              <h3
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "1.35rem",
                  fontWeight: 700,
                  color: "var(--text-ink)",
                  margin: 0,
                }}
              >
                Draft Strategy Note
              </h3>

              <button
                type="button"
                onClick={handleStructureWithAI}
                disabled={structuring || !newContent}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.35rem",
                  fontSize: "0.75rem",
                  color: "var(--maroon)",
                  backgroundColor: "var(--maroon-faint)",
                  border: "1px solid var(--maroon-border)",
                  padding: "0.25rem 0.6rem",
                  borderRadius: "2px",
                  cursor: "pointer",
                }}
              >
                <Sparkles size={12} />
                <span>Structure with AI</span>
              </button>
            </div>

            <form onSubmit={handleCreateNote}>
              <div style={{ display: "flex", flexDirection: "column", gap: "1.1rem" }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.3rem" }}>
                    Note Title
                  </label>
                  <input
                    type="text"
                    required
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g. Points for Senior Advocate Briefing"
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
                    Notes Content
                  </label>
                  <textarea
                    rows={6}
                    required
                    value={newContent}
                    onChange={(e) => setNewContent(e.target.value)}
                    placeholder="Enter arguments, factual queries, witness examination points..."
                    style={{
                      width: "100%",
                      padding: "0.65rem 0.8rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      fontSize: "0.88rem",
                      lineHeight: 1.5,
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.3rem" }}>
                    Tags (comma separated)
                  </label>
                  <input
                    type="text"
                    value={newTags}
                    onChange={(e) => setNewTags(e.target.value)}
                    placeholder="e.g. Limitation, Hearing, Evidence"
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
                    style={{
                      padding: "0.55rem 1rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      background: "none",
                    }}
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    style={{
                      padding: "0.55rem 1.4rem",
                      backgroundColor: "var(--maroon)",
                      color: "#FFFFFF",
                      borderRadius: "2px",
                      fontWeight: 600,
                      border: "none",
                    }}
                  >
                    Save Note
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
