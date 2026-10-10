"use client";

import React, { useState } from "react";
import { Matter, TimelineEvent } from "@/lib/types/matter";
import { ProvenanceBadge } from "./ProvenanceBadge";
import {
  Calendar,
  FileText,
  Plus,
  Clock,
  Sparkles,
  CheckCircle,
  ArrowUpDown,
} from "lucide-react";

interface TimelineTabProps {
  matter: Matter;
  onAddTimelineEvent?: (event: TimelineEvent) => void;
}

export function TimelineTab({ matter, onAddTimelineEvent }: TimelineTabProps) {
  const [events, setEvents] = useState<TimelineEvent[]>(matter.timeline);
  const [sortAsc, setSortAsc] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  // New event form state
  const [newDate, setNewDate] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newDoc, setNewDoc] = useState("");

  const sortedEvents = [...events].sort((a, b) => {
    return sortAsc
      ? new Date(a.date).getTime() - new Date(b.date).getTime()
      : new Date(b.date).getTime() - new Date(a.date).getTime();
  });

  const handleCreateEvent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDate || !newTitle) return;

    const created: TimelineEvent = {
      id: `TL-NEW-${Date.now()}`,
      matterId: matter.id,
      date: newDate,
      title: newTitle,
      description: newDesc,
      sourceDocumentName: newDoc || undefined,
      source: "lawyer",
    };

    setEvents((prev) => [...prev, created]);
    if (onAddTimelineEvent) onAddTimelineEvent(created);
    setShowAddModal(false);
    setNewDate("");
    setNewTitle("");
    setNewDesc("");
    setNewDoc("");
  };

  return (
    <div style={{ maxWidth: "980px" }}>
      {/* Top Controls */}
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
            Chronological Matter Timeline
          </h3>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: 0 }}>
            Court events and procedural steps linked to verified case documents.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <button
            onClick={() => setSortAsc(!sortAsc)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
              padding: "0.45rem 0.85rem",
              fontSize: "0.8rem",
              border: "1px solid var(--border-rule)",
              borderRadius: "2px",
              backgroundColor: "var(--bg-sheet)",
              color: "var(--text-ink)",
              cursor: "pointer",
            }}
          >
            <ArrowUpDown size={13} />
            <span>{sortAsc ? "Oldest First" : "Newest First"}</span>
          </button>

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
            <Plus size={14} />
            <span>Record Court Event</span>
          </button>
        </div>
      </div>

      {/* Timeline Stream */}
      <div style={{ position: "relative", paddingLeft: "2.5rem" }}>
        {/* Continuous vertical line */}
        <div
          style={{
            position: "absolute",
            left: "11px",
            top: "8px",
            bottom: "8px",
            width: "2px",
            backgroundColor: "var(--border-rule)",
          }}
        />

        <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
          {sortedEvents.map((evt) => {
            const isAiExtracted = evt.source === "ai_extraction";

            return (
              <div key={evt.id} style={{ position: "relative" }}>
                {/* Node pin */}
                <div
                  style={{
                    position: "absolute",
                    left: "-2.5rem",
                    top: "3px",
                    width: "24px",
                    height: "24px",
                    borderRadius: "50%",
                    backgroundColor: "var(--bg-sheet)",
                    border: "2px solid var(--maroon)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <div
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      backgroundColor: "var(--maroon)",
                    }}
                  />
                </div>

                {/* Timeline Card */}
                <div
                  className="paper-card"
                  style={{
                    padding: "1.35rem 1.6rem",
                    backgroundColor: "var(--bg-sheet)",
                    borderRadius: "3px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: "0.5rem",
                      flexWrap: "wrap",
                      gap: "0.5rem",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
                      <span
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.85rem",
                          fontWeight: 700,
                          color: "var(--maroon)",
                        }}
                      >
                        {evt.date}
                      </span>

                      {evt.eventType && (
                        <span
                          style={{
                            fontSize: "0.65rem",
                            fontWeight: 700,
                            fontFamily: "var(--font-mono)",
                            padding: "0.15rem 0.45rem",
                            borderRadius: "2px",
                            backgroundColor:
                              evt.eventType === "JUDGMENT_PRONOUNCED" || evt.eventType === "MATTER_DISPOSED"
                                ? "#D1FAE5"
                                : evt.eventType === "INTERIM_ORDER" || evt.eventType === "CURRENT_EVENT"
                                ? "#FEF3C7"
                                : evt.eventType === "DIRECTION_ISSUED" || evt.eventType === "REPORT_DUE" || evt.eventType === "FUTURE_EVENT"
                                ? "#EEF2FF"
                                : evt.eventType === "NOTICE_ISSUED"
                                ? "#DBEAFE"
                                : "var(--bg-parchment)",
                            color:
                              evt.eventType === "JUDGMENT_PRONOUNCED" || evt.eventType === "MATTER_DISPOSED"
                                ? "#065F46"
                                : evt.eventType === "INTERIM_ORDER" || evt.eventType === "CURRENT_EVENT"
                                ? "#92400E"
                                : evt.eventType === "DIRECTION_ISSUED" || evt.eventType === "REPORT_DUE" || evt.eventType === "FUTURE_EVENT"
                                ? "#4338CA"
                                : evt.eventType === "NOTICE_ISSUED"
                                ? "#1E40AF"
                                : "var(--text-muted)",
                            border: "1px solid var(--border-subtle)",
                            letterSpacing: "0.03em",
                          }}
                        >
                          {String(evt.eventType).replace(/_/g, " ")}
                        </span>
                      )}

                      {evt.status === "DIRECTED_NOT_COMPLETED" && (
                        <span
                          style={{
                            fontSize: "0.63rem",
                            fontWeight: 700,
                            fontFamily: "var(--font-mono)",
                            padding: "0.1rem 0.4rem",
                            borderRadius: "2px",
                            backgroundColor: "#FEF2F2",
                            color: "#991B1B",
                            border: "1px solid #FECACA",
                          }}
                        >
                          DIRECTED NOT COMPLETED
                        </span>
                      )}
                    </div>

                    {/* Source Status Provenance */}
                    <ProvenanceBadge
                      type={
                        evt.provenance ||
                        (evt.source === "court_record"
                          ? "SOURCE_EXPLICIT"
                          : evt.source === "ai_extraction"
                          ? "AI_ANALYSIS"
                          : "USER_PROVIDED")
                      }
                      sourceDoc={evt.sourceDocumentName}
                      page={evt.page}
                      paragraph={evt.paragraph}
                    />
                  </div>

                  <h4
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontSize: "1.15rem",
                      fontWeight: 700,
                      color: "var(--text-ink)",
                      marginBottom: "0.35rem",
                    }}
                  >
                    {evt.title}
                  </h4>

                  {evt.description && (
                    <p
                      style={{
                        fontSize: "0.88rem",
                        lineHeight: 1.55,
                        color: "var(--text-muted)",
                        marginBottom: evt.sourceDocumentName ? "0.75rem" : 0,
                      }}
                    >
                      {evt.description}
                    </p>
                  )}

                  {evt.sourceDocumentName && (
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.4rem",
                        fontSize: "0.76rem",
                        color: "var(--navy)",
                        paddingTop: "0.5rem",
                        borderTop: "1px solid var(--border-subtle)",
                      }}
                    >
                      <FileText size={13} color="var(--maroon)" />
                      <span>Document: {evt.sourceDocumentName}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Modal: Record Event */}
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
              maxWidth: "520px",
              width: "100%",
              backgroundColor: "var(--bg-sheet)",
              borderRadius: "4px",
              padding: "2rem",
              boxShadow: "var(--shadow-modal)",
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
              Record Court / Matter Event
            </h3>

            <form onSubmit={handleCreateEvent}>
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.8rem",
                      fontWeight: 600,
                      marginBottom: "0.3rem",
                    }}
                  >
                    Event Date
                  </label>
                  <input
                    type="date"
                    required
                    value={newDate}
                    onChange={(e) => setNewDate(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "0.6rem 0.75rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      fontSize: "0.88rem",
                    }}
                  />
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.8rem",
                      fontWeight: 600,
                      marginBottom: "0.3rem",
                    }}
                  >
                    Event Title
                  </label>
                  <input
                    type="text"
                    required
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g. Counter Affidavit Filed by Respondent"
                    style={{
                      width: "100%",
                      padding: "0.6rem 0.75rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      fontSize: "0.88rem",
                    }}
                  />
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.8rem",
                      fontWeight: 600,
                      marginBottom: "0.3rem",
                    }}
                  >
                    Description / Holding
                  </label>
                  <textarea
                    rows={3}
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    placeholder="Brief description of the order or filing..."
                    style={{
                      width: "100%",
                      padding: "0.6rem 0.75rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      fontSize: "0.88rem",
                    }}
                  />
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.8rem",
                      fontWeight: 600,
                      marginBottom: "0.3rem",
                    }}
                  >
                    Source Document (Optional)
                  </label>
                  <input
                    type="text"
                    value={newDoc}
                    onChange={(e) => setNewDoc(e.target.value)}
                    placeholder="e.g. Order_2025_01_12.pdf"
                    style={{
                      width: "100%",
                      padding: "0.6rem 0.75rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      fontSize: "0.88rem",
                    }}
                  />
                </div>

                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-end",
                    gap: "0.75rem",
                    marginTop: "0.75rem",
                  }}
                >
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    style={{
                      padding: "0.6rem 1rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      background: "none",
                      fontSize: "0.85rem",
                      cursor: "pointer",
                    }}
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    style={{
                      padding: "0.6rem 1.25rem",
                      backgroundColor: "var(--maroon)",
                      color: "#FFFFFF",
                      borderRadius: "2px",
                      fontSize: "0.85rem",
                      fontWeight: 600,
                      border: "none",
                      cursor: "pointer",
                    }}
                  >
                    Save Event
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
