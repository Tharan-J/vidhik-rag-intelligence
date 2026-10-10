"use client";

import React from "react";
import { Matter, MatterStage } from "@/lib/types/matter";
import { ProvenanceBadge } from "./ProvenanceBadge";
import { Scale, Calendar, Clock, FileText, ArrowLeft, ShieldCheck, Tag } from "lucide-react";
import Link from "next/link";

interface MatterHeaderProps {
  matter: Matter;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "status", label: "Status" },
  { id: "timeline", label: "Timeline" },
  { id: "documents", label: "Documents" },
  { id: "issues", label: "Issues" },
  { id: "sections", label: "Sections" },
  { id: "authorities", label: "Authorities" },
  { id: "research", label: "Research" },
  { id: "evidence", label: "Evidence" },
  { id: "assistant", label: "AI Assistant" },
  { id: "notes", label: "Notes" },
];

export function MatterHeader({ matter, activeTab, onTabChange }: MatterHeaderProps) {
  const isSuoMotu =
    matter.proceedingType === "SUO_MOTU" ||
    matter.proceedingType === "IN_RE" ||
    matter.title.toLowerCase().includes("suo moto") ||
    matter.title.toLowerCase().includes("in re");

  return (
    <div
      style={{
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-rule)",
        borderRadius: "3px",
        marginBottom: "2rem",
        boxShadow: "var(--shadow-sheet)",
      }}
    >
      {/* Top Identification Bar */}
      <div
        style={{
          padding: "1.75rem 2rem 1.25rem 2rem",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "1rem",
            marginBottom: "0.85rem",
          }}
        >
          <div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.6rem",
                marginBottom: "0.5rem",
                flexWrap: "wrap",
              }}
            >
              <span
                style={{
                  fontSize: "0.75rem",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 700,
                  color: "var(--maroon)",
                  backgroundColor: "var(--maroon-faint)",
                  padding: "0.15rem 0.5rem",
                  borderRadius: "2px",
                  border: "1px solid var(--maroon-border)",
                }}
              >
                {matter.caseNumber}
              </span>
              <span
                style={{
                  fontSize: "0.82rem",
                  fontWeight: 600,
                  color: "var(--navy)",
                }}
              >
                {matter.court}
              </span>
              <span style={{ color: "var(--border-dark)" }}>•</span>
              <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                {matter.matterType}
              </span>

              {isSuoMotu && (
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 700,
                    color: "#6D28D9",
                    backgroundColor: "#F5F3FF",
                    border: "1px solid #DDD6FE",
                    borderRadius: "2px",
                    padding: "0.1rem 0.45rem",
                  }}
                >
                  SUO MOTU / IN RE JURISDICTION
                </span>
              )}

              <ProvenanceBadge
                type="SOURCE_EXPLICIT"
                sourceDoc={matter.documents[0]?.name}
                page={1}
                labelOverride="✓ SOURCE EXPLICIT"
              />
            </div>

            <h1
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1.85rem",
                fontWeight: 700,
                color: "var(--text-ink)",
                lineHeight: 1.25,
                margin: 0,
              }}
            >
              {matter.title}
            </h1>
          </div>

          {/* Current Stage Badge */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-end",
              gap: "0.35rem",
            }}
          >
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.45rem",
                padding: "0.35rem 0.85rem",
                backgroundColor: "var(--maroon)",
                color: "#FFFFFF",
                borderRadius: "2px",
                fontSize: "0.82rem",
                fontWeight: 700,
                letterSpacing: "0.05em",
                textTransform: "uppercase",
              }}
            >
              <Scale size={13} />
              <span>Stage: {matter.status}</span>
            </div>
            <span style={{ fontSize: "0.72rem", color: "var(--text-faint)" }}>
              Updated {matter.updatedAt}
            </span>
          </div>
        </div>

        {/* Quick Metadata Line with Field-Level Provenance */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "1.75rem",
            fontSize: "0.82rem",
            color: "var(--text-muted)",
            flexWrap: "wrap",
            paddingTop: "0.6rem",
          }}
        >
          <div style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
            <span style={{ fontWeight: 600, color: "var(--text-ink)" }}>Client: </span>
            <span>{matter.client || "Not specified"}</span>
            <ProvenanceBadge
              type={matter.client && matter.client !== "Not specified" ? "USER_PROVIDED" : "NOT_FOUND"}
              labelOverride={
                matter.client && matter.client !== "Not specified"
                  ? "✎ USER PROVIDED"
                  : "⊘ NOT SPECIFIED BY COUNSEL"
              }
            />
          </div>

          <div style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
            <span style={{ fontWeight: 600, color: "var(--text-ink)" }}>Filing Date: </span>
            <span>{matter.importantDates?.filingDate || "Not in record"}</span>
            <ProvenanceBadge
              type={
                matter.importantDates?.filingDate &&
                matter.importantDates.filingDate !== "Not specified in record" &&
                matter.importantDates.filingDate !== "Not in record" &&
                !matter.importantDates.filingDate.includes("Not specified")
                  ? "SOURCE_EXPLICIT"
                  : "NOT_FOUND"
              }
              labelOverride={
                matter.importantDates?.filingDate &&
                !matter.importantDates.filingDate.includes("Not")
                  ? "✓ SOURCE EXPLICIT"
                  : "⊘ NOT FOUND IN RECORD"
              }
            />
          </div>

          <div>
            <span style={{ fontWeight: 600, color: "var(--text-ink)" }}>Next Event: </span>
            <span style={{ color: "var(--navy)" }}>{matter.nextImportantEvent}</span>
          </div>

          <div>
            <span style={{ fontWeight: 600, color: "var(--text-ink)" }}>Documents: </span>
            <span>{matter.documents.length} Verified</span>
          </div>
        </div>
      </div>

      {/* Horizontal Navigation Tabs */}
      <nav
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.25rem",
          padding: "0 1.5rem",
          overflowX: "auto",
        }}
        aria-label="Matter Workspace Tabs"
      >
        {TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              style={{
                padding: "0.85rem 1.15rem",
                fontFamily: "var(--font-sans)",
                fontSize: "0.85rem",
                fontWeight: isActive ? 700 : 500,
                color: isActive ? "var(--maroon)" : "var(--text-muted)",
                borderBottom: `2.5px solid ${
                  isActive ? "var(--maroon)" : "transparent"
                }`,
                background: "none",
                cursor: "pointer",
                whiteSpace: "nowrap",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.color = "var(--text-ink)";
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.color = "var(--text-muted)";
              }}
            >
              {tab.label}
              {tab.id === "documents" && (
                <span
                  style={{
                    marginLeft: "0.35rem",
                    fontSize: "0.72rem",
                    padding: "0.1rem 0.4rem",
                    backgroundColor: "var(--bg-parchment)",
                    borderRadius: "10px",
                    color: "var(--text-faint)",
                  }}
                >
                  {matter.documents.length}
                </span>
              )}
              {tab.id === "issues" && (
                <span
                  style={{
                    marginLeft: "0.35rem",
                    fontSize: "0.72rem",
                    padding: "0.1rem 0.4rem",
                    backgroundColor: "var(--bg-parchment)",
                    borderRadius: "10px",
                    color: "var(--text-faint)",
                  }}
                >
                  {matter.issues.length}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
}
