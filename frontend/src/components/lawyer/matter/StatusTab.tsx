"use client";

import React from "react";
import { Matter, MatterStage } from "@/lib/types/matter";
import { CheckCircle2, Clock, AlertCircle, Scale, ShieldCheck } from "lucide-react";

interface StatusTabProps {
  matter: Matter;
  onUpdateStatus?: (status: MatterStage) => void;
}

const STAGE_ORDER: MatterStage[] = [
  "Filed",
  "Notice",
  "Pleadings",
  "Evidence",
  "Arguments",
  "Judgment",
  "Disposed",
];

export function StatusTab({ matter, onUpdateStatus }: StatusTabProps) {
  const currentIndex = STAGE_ORDER.findIndex((s) => s.toLowerCase() === matter.status.toLowerCase());
  const activeIdx = currentIndex === -1 ? 4 : currentIndex;

  const handleStageSelect = (stage: MatterStage) => {
    if (onUpdateStatus && stage.toLowerCase() !== matter.status.toLowerCase()) {
      onUpdateStatus(stage);
    }
  };

  const getStageDetails = (stage: MatterStage) => {
    switch (stage) {
      case "Filed":
        return {
          title: "Matter Lodged & Registered",
          description: `${matter.caseNumber} presented and numbered before the ${matter.court}. Initiated by ${matter.parties.petitioner}.`,
        };
      case "Notice":
        return {
          title: "Process & Judicial Notice",
          description: `Judicial notice issued to ${matter.parties.respondent}. Service of process and appearances entered.`,
        };
      case "Pleadings":
        return {
          title: "Pleadings & Affidavits Completed",
          description: `Pleadings formally exchanged. Petitions, counter affidavits, and rejoinders placed on judicial record.`,
        };
      case "Evidence":
        return {
          title: "Documentary Evidence & Record Inspection",
          description: `Lower court records and documentary exhibits verified before the bench. Interlocutory orders active.`,
        };
      case "Arguments":
        return {
          title: "Substantive Oral & Written Arguments",
          description: `Hearing of substantive legal submissions. Counsel: ${matter.parties.counsel}. Coram: ${matter.parties.court}.`,
        };
      case "Judgment":
        return {
          title: "Judicial Pronouncement & Disposal",
          description: `Reserved for judgment or final decision rendered by the ${matter.court}.`,
        };
      default:
        return {
          title: stage,
          description: `Procedural step in ${matter.caseNumber}.`,
        };
    }
  };

  return (
    <div style={{ maxWidth: "920px" }}>
      <div
        className="paper-card"
        style={{
          padding: "2rem",
          backgroundColor: "var(--bg-sheet)",
          borderRadius: "3px",
          marginBottom: "2rem",
        }}
      >
        <div style={{ marginBottom: "1.75rem" }}>
          <h3
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "1.45rem",
              fontWeight: 700,
              color: "var(--text-ink)",
              marginBottom: "0.35rem",
            }}
          >
            Procedural Stage Progression
          </h3>
          <p style={{ fontSize: "0.88rem", color: "var(--text-muted)", margin: 0 }}>
            Visual tracking of {matter.caseNumber} through statutory milestones before the {matter.court}.
          </p>
        </div>

        {/* Vertical Step Progression Track */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {STAGE_ORDER.map((stage, index) => {
            const isCompleted = index < activeIdx;
            const isCurrent = index === activeIdx;
            const isPending = index > activeIdx;
            const details = getStageDetails(stage);

            return (
              <div
                key={stage}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "1.25rem",
                  position: "relative",
                }}
              >
                {/* Connecting rule line */}
                {index < STAGE_ORDER.length - 1 && (
                  <div
                    style={{
                      position: "absolute",
                      left: "17px",
                      top: "34px",
                      bottom: "-24px",
                      width: "2px",
                      backgroundColor: isCompleted
                        ? "var(--maroon)"
                        : "var(--border-rule)",
                    }}
                  />
                )}

                {/* Node Icon */}
                <div
                  style={{
                    width: "36px",
                    height: "36px",
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    zIndex: 2,
                    backgroundColor: isCompleted
                      ? "var(--maroon)"
                      : isCurrent
                      ? "var(--bg-sheet)"
                      : "var(--bg-parchment)",
                    border: isCurrent
                      ? "2px solid var(--maroon)"
                      : isCompleted
                      ? "2px solid var(--maroon)"
                      : "2px solid var(--border-rule)",
                    color: isCompleted
                      ? "#FFFFFF"
                      : isCurrent
                      ? "var(--maroon)"
                      : "var(--text-faint)",
                  }}
                >
                  {isCompleted ? (
                    <CheckCircle2 size={18} />
                  ) : isCurrent ? (
                    <Clock size={18} />
                  ) : (
                    <span style={{ fontSize: "0.8rem", fontWeight: 700 }}>{index + 1}</span>
                  )}
                </div>

                {/* Node Text & Status Description */}
                <div
                  style={{
                    flex: 1,
                    padding: "0.85rem 1.25rem",
                    backgroundColor: isCurrent ? "var(--bg-parchment)" : "transparent",
                    border: isCurrent ? "1px solid var(--border-rule)" : "none",
                    borderRadius: "2px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: "0.25rem",
                    }}
                  >
                    <span
                      style={{
                        fontFamily: "var(--font-serif)",
                        fontSize: "1.05rem",
                        fontWeight: 700,
                        color: isPending ? "var(--text-muted)" : "var(--text-ink)",
                      }}
                    >
                      {details.title}
                    </span>

                    <span
                      style={{
                        fontSize: "0.7rem",
                        fontFamily: "var(--font-mono)",
                        fontWeight: 700,
                        letterSpacing: "0.06em",
                        textTransform: "uppercase",
                        color: isCompleted
                          ? "var(--status-supported-text)"
                          : isCurrent
                          ? "var(--maroon)"
                          : "var(--text-faint)",
                      }}
                    >
                      {isCompleted ? "COMPLETED" : isCurrent ? "CURRENT STAGE" : "UPCOMING"}
                    </span>
                  </div>

                  <p
                    style={{
                      fontSize: "0.86rem",
                      color: isPending ? "var(--text-faint)" : "var(--text-muted)",
                      lineHeight: 1.5,
                      margin: 0,
                    }}
                  >
                    {isCurrent && matter.lastKnownEvent
                      ? `${details.description} Latest: ${matter.lastKnownEvent}`
                      : details.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Immediate Next Step Card */}
      <div
        className="paper-card"
        style={{
          padding: "1.5rem 1.75rem",
          backgroundColor: "var(--bg-sheet)",
          border: "1px solid var(--maroon-border)",
          borderLeft: "4px solid var(--maroon)",
          borderRadius: "3px",
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-start", gap: "0.85rem" }}>
          <AlertCircle size={20} color="var(--maroon)" style={{ marginTop: "0.15rem", flexShrink: 0 }} />
          <div>
            <h4
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1.1rem",
                fontWeight: 700,
                color: "var(--text-ink)",
                margin: "0 0 0.35rem 0",
              }}
            >
              Next Critical Milestone
            </h4>
            <p style={{ fontSize: "0.88rem", color: "var(--text-muted)", margin: "0 0 0.75rem 0", lineHeight: 1.5 }}>
              {matter.nextImportantEvent || "Oral submissions scheduled before the Bench."}
            </p>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
                fontSize: "0.74rem",
                fontFamily: "var(--font-mono)",
                color: "var(--navy)",
                fontWeight: 600,
              }}
            >
              <span>Bench: {matter.parties.court}</span>
              <span>•</span>
              <span>Next Hearing: {matter.importantDates.nextHearing || "Listed as per Cause List"}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
