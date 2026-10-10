"use client";

import React, { useState } from "react";

interface FilterRailProps {
  onSelectQueryPreset: (query: string) => void;
}

export function FilterRail({ onSelectQueryPreset }: FilterRailProps) {
  const [supremeCourt, setSupremeCourt] = useState(true);
  const [highCourt, setHighCourt] = useState(true);
  const [districtCourt, setDistrictCourt] = useState(true);
  const [selectedCourt, setSelectedCourt] = useState("All Courts");
  const [yearFrom, setYearFrom] = useState("1950");
  const [yearTo, setYearTo] = useState("2024");

  const queryPresets = [
    {
      label: "Limitation Period for Appeal",
      query: "What is the limitation period for filing an appeal?",
      court: "Supreme Court / High Courts",
    },
    {
      label: "Arbitration Delay Condonation",
      query: "Can delay beyond 30 days be condoned under Section 34 of the Arbitration Act?",
      court: "Supreme Court of India",
    },
    {
      label: "Special Law Exclusion of Limitation",
      query: "How does Section 29(2) of the Limitation Act apply when a special statute provides a distinct limitation period?",
      court: "High Courts & Supreme Court",
    },
    {
      label: "Pre-deposit in Central Excise Appeals",
      query: "What is the statutory limitation and condonation period for appeals under Section 35 of the Central Excise Act?",
      court: "Supreme Court of India",
    },
  ];

  return (
    <aside
      style={{
        backgroundColor: "var(--bg-surface)",
        borderRight: "1px solid var(--border-rule)",
        padding: "1.5rem 1.25rem",
        display: "flex",
        flexDirection: "column",
        gap: "1.75rem",
        overflowY: "auto",
        height: "100%",
        fontFamily: "var(--font-sans)",
      }}
    >
      {/* Title */}
      <div>
        <h3
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "0.72rem",
            fontWeight: 700,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: "var(--navy)",
            marginBottom: "0.35rem",
          }}
        >
          REFINE RESEARCH
        </h3>
        <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
          Constrain retrieval parameters across certified Indian judicial corpora.
        </p>
      </div>

      <hr className="legal-rule" style={{ margin: "0" }} />

      {/* Court Level */}
      <div>
        <label
          style={{
            fontSize: "0.68rem",
            fontWeight: 700,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "var(--text-faint)",
            display: "block",
            marginBottom: "0.65rem",
          }}
        >
          JUDICIAL HIERARCHY
        </label>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", fontSize: "0.82rem" }}>
          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={supremeCourt}
              onChange={(e) => setSupremeCourt(e.target.checked)}
              style={{ accentColor: "var(--maroon)" }}
            />
            <span>Supreme Court of India</span>
          </label>

          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={highCourt}
              onChange={(e) => setHighCourt(e.target.checked)}
              style={{ accentColor: "var(--maroon)" }}
            />
            <span>High Courts</span>
          </label>

          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={districtCourt}
              onChange={(e) => setDistrictCourt(e.target.checked)}
              style={{ accentColor: "var(--maroon)" }}
            />
            <span>District Courts</span>
          </label>
        </div>
      </div>

      {/* Specific Court Selection */}
      <div>
        <label
          style={{
            fontSize: "0.68rem",
            fontWeight: 700,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "var(--text-faint)",
            display: "block",
            marginBottom: "0.45rem",
          }}
        >
          JURISDICTION / FORUM
        </label>
        <select
          value={selectedCourt}
          onChange={(e) => setSelectedCourt(e.target.value)}
          style={{
            width: "100%",
            padding: "0.45rem 0.5rem",
            fontSize: "0.8rem",
            backgroundColor: "#FFFFFF",
            border: "1px solid var(--border-rule)",
            borderRadius: "2px",
            color: "var(--text-ink)",
          }}
        >
          <option value="All Courts">All Courts (Corpus Unified)</option>
          <option value="Supreme Court of India">Supreme Court of India</option>
          <option value="Delhi High Court">Delhi High Court</option>
          <option value="Karnataka High Court">Karnataka High Court</option>
          <option value="District Courts">District Courts (District Trial Level)</option>
        </select>
      </div>

      {/* Decision Year Range */}
      <div>
        <label
          style={{
            fontSize: "0.68rem",
            fontWeight: 700,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "var(--text-faint)",
            display: "block",
            marginBottom: "0.45rem",
          }}
        >
          YEAR OF JUDGMENT
        </label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
          <div>
            <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", display: "block" }}>From</span>
            <input
              type="number"
              value={yearFrom}
              onChange={(e) => setYearFrom(e.target.value)}
              style={{
                width: "100%",
                padding: "0.35rem 0.45rem",
                fontSize: "0.78rem",
                border: "1px solid var(--border-rule)",
                borderRadius: "2px",
                backgroundColor: "#FFFFFF",
              }}
            />
          </div>
          <div>
            <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", display: "block" }}>To</span>
            <input
              type="number"
              value={yearTo}
              onChange={(e) => setYearTo(e.target.value)}
              style={{
                width: "100%",
                padding: "0.35rem 0.45rem",
                fontSize: "0.78rem",
                border: "1px solid var(--border-rule)",
                borderRadius: "2px",
                backgroundColor: "#FFFFFF",
              }}
            />
          </div>
        </div>
      </div>

      {/* Preset Queries */}
      <div>
        <label
          style={{
            fontSize: "0.68rem",
            fontWeight: 700,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "var(--text-faint)",
            display: "block",
            marginBottom: "0.65rem",
          }}
        >
          BENCHMARK LEGAL QUESTIONS
        </label>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
          {queryPresets.map((item, idx) => (
            <button
              key={idx}
              onClick={() => onSelectQueryPreset(item.query)}
              style={{
                textAlign: "left",
                padding: "0.55rem 0.65rem",
                backgroundColor: "#FFFFFF",
                border: "1px solid var(--border-subtle)",
                borderRadius: "2px",
                cursor: "pointer",
                transition: "all 0.15s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--maroon)";
                e.currentTarget.style.backgroundColor = "var(--bg-parchment)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border-subtle)";
                e.currentTarget.style.backgroundColor = "#FFFFFF";
              }}
            >
              <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-ink)", marginBottom: "0.15rem" }}>
                {item.label}
              </div>
              <div style={{ fontSize: "0.68rem", color: "var(--text-faint)" }}>
                {item.court}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Corpus Footnote */}
      <div
        style={{
          marginTop: "auto",
          padding: "0.75rem",
          backgroundColor: "var(--bg-parchment)",
          border: "1px solid var(--border-rule)",
          borderRadius: "2px",
          fontSize: "0.7rem",
          color: "var(--text-muted)",
          lineHeight: 1.5,
        }}
      >
        <strong style={{ color: "var(--text-ink)", display: "block", marginBottom: "0.2rem" }}>
          VERIFIED ARCHIVE PARITY
        </strong>
        <span>
          29,156 passages indexed in exact parity across Qdrant Cloud (Dense) and BM25 (Lexical).
        </span>
      </div>
    </aside>
  );
}
