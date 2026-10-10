"use client";

import React from "react";
import { ProvenanceBadgeType, FieldProvenanceStatus } from "@/lib/types/matter";
import {
  CheckCircle2,
  AlertTriangle,
  Edit3,
  HelpCircle,
  Slash,
  GitBranch,
  SearchCheck,
  Zap,
} from "lucide-react";

interface ProvenanceBadgeProps {
  type?: ProvenanceBadgeType | FieldProvenanceStatus | string;
  sourceDoc?: string;
  page?: string | number;
  paragraph?: string | number;
  labelOverride?: string;
  onViewSource?: () => void;
}

export function ProvenanceBadge({
  type = "SOURCE_EXPLICIT",
  sourceDoc,
  page,
  paragraph,
  labelOverride,
  onViewSource,
}: ProvenanceBadgeProps) {
  let badgeLabel = "✓ SOURCE EXPLICIT";
  let icon = <CheckCircle2 size={11} />;
  let color = "#10754A";
  let bg = "#EBF7F0";
  let border = "#B4E3CB";

  const normType = String(type || "SOURCE_EXPLICIT");

  if (
    normType === "SOURCE_EXPLICIT" ||
    normType === "court_explicit" ||
    normType === "VERIFIED_FROM_SOURCE"
  ) {
    badgeLabel = "✓ SOURCE EXPLICIT";
    icon = <CheckCircle2 size={11} />;
    color = "#10754A";
    bg = "#EBF7F0";
    border = "#B4E3CB";
  } else if (normType === "SOURCE_DERIVED" || normType === "source_derived") {
    badgeLabel = "◒ SOURCE DERIVED";
    icon = <GitBranch size={11} />;
    color = "#0F766E";
    bg = "#F0FDFA";
    border = "#99F6E4";
  } else if (
    normType === "INDEPENDENTLY_VERIFIED" ||
    normType === "verified_in_judgment"
  ) {
    badgeLabel = "✓ INDEPENDENTLY VERIFIED";
    icon = <SearchCheck size={11} />;
    color = "#0369A1";
    bg = "#F0F9FF";
    border = "#BAE6FD";
  } else if (normType === "party_argument") {
    badgeLabel = "✎ PARTY ARGUMENT";
    icon = <Edit3 size={11} />;
    color = "#4338CA";
    bg = "#EEF2FF";
    border = "#C7D2FE";
  } else if (
    normType === "AI_ANALYSIS" ||
    normType === "ai_analysis" ||
    normType === "ai_suggestion"
  ) {
    badgeLabel = "⚠ AI ANALYSIS";
    icon = <AlertTriangle size={11} />;
    color = "#B45309";
    bg = "#FFFBEB";
    border = "#FDE68A";
  } else if (
    normType === "USER_PROVIDED" ||
    normType === "user_specified" ||
    normType === "lawyer"
  ) {
    badgeLabel = "✎ USER PROVIDED";
    icon = <Edit3 size={11} />;
    color = "#1D4ED8";
    bg = "#EFF6FF";
    border = "#BFDBFE";
  } else if (normType === "CONFLICTING_SOURCE") {
    badgeLabel = "⚡ CONFLICTING SOURCE";
    icon = <Zap size={11} />;
    color = "#BE123C";
    bg = "#FFF1F2";
    border = "#FECDD3";
  } else if (normType === "NOT_FOUND") {
    badgeLabel = "⊘ NOT FOUND IN SOURCE";
    icon = <Slash size={11} />;
    color = "#475569";
    bg = "#F1F5F9";
    border = "#CBD5E1";
  } else if (
    normType === "flagged_hallucination" ||
    normType === "FLAGGED_HALLUCINATION" ||
    normType === "FLAGGED_FAKE"
  ) {
    badgeLabel = "⚠ FLAGGED AS FAKE CITATION IN RECORD";
    icon = <AlertTriangle size={11} />;
    color = "#B91C1C";
    bg = "#FEF2F2";
    border = "#FECACA";
  } else {
    // NOT_VERIFIED, unverified, unsupported
    badgeLabel = "? NOT VERIFIED FROM SOURCE";
    icon = <HelpCircle size={11} />;
    color = "#4B5563";
    bg = "#F3F4F6";
    border = "#E5E7EB";
  }

  if (labelOverride) {
    badgeLabel = labelOverride;
  }

  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.3rem",
          fontSize: "0.68rem",
          fontWeight: 700,
          fontFamily: "var(--font-mono)",
          color,
          backgroundColor: bg,
          border: `1px solid ${border}`,
          borderRadius: "2px",
          padding: "0.15rem 0.45rem",
          letterSpacing: "0.03em",
        }}
      >
        {icon}
        <span>{badgeLabel}</span>
      </span>

      {(sourceDoc || page || paragraph) && (
        <span
          style={{
            fontSize: "0.68rem",
            color: "var(--text-faint)",
            fontFamily: "var(--font-mono)",
          }}
        >
          [{sourceDoc ? sourceDoc : ""}{page ? ` · Page ${page}` : ""}{paragraph ? ` · Para ${paragraph}` : ""}]
        </span>
      )}

      {onViewSource && (
        <button
          onClick={onViewSource}
          style={{
            background: "none",
            border: "none",
            padding: 0,
            fontSize: "0.68rem",
            fontWeight: 600,
            color: "var(--maroon)",
            cursor: "pointer",
            textDecoration: "underline",
          }}
        >
          [View Source]
        </button>
      )}
    </div>
  );
}
