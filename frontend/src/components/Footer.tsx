"use client";

import React from "react";
import Link from "next/link";

export function Footer() {
  return (
    <footer
      style={{
        backgroundColor: "var(--bg-surface)",
        borderTop: "1px solid var(--border-rule)",
        padding: "3.5rem 2rem 2.5rem 2rem",
        marginTop: "auto",
      }}
    >
      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          display: "grid",
          gridTemplateColumns: "2fr 1fr 1fr",
          gap: "3rem",
        }}
      >
        <div>
          <span
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "1.4rem",
              fontWeight: 700,
              letterSpacing: "0.06em",
              color: "var(--text-ink)",
              display: "block",
              marginBottom: "0.4rem",
            }}
          >
            VIDHIK
          </span>
          <p
            style={{
              fontFamily: "var(--font-serif)",
              fontStyle: "italic",
              fontSize: "1rem",
              color: "var(--maroon)",
              marginBottom: "0.75rem",
            }}
          >
            Research the law. Trace every authority.
          </p>
          <p
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "0.85rem",
              color: "var(--text-muted)",
              lineHeight: 1.6,
              maxWidth: "420px",
            }}
          >
            An Indian legal research system grounded in certified judgments,
            evidence verification, and structural provenance across the Supreme Court of
            India, High Courts, and District Courts.
          </p>
        </div>

        <div>
          <h4
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "0.75rem",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.12em",
              color: "var(--text-faint)",
              marginBottom: "1rem",
            }}
          >
            Judicial Architecture
          </h4>
          <ul
            style={{
              listStyle: "none",
              display: "flex",
              flexDirection: "column",
              gap: "0.55rem",
              fontSize: "0.85rem",
              color: "var(--text-muted)",
            }}
          >
            <li>Supreme Court of India (Apex)</li>
            <li>High Courts (State Jurisdictions)</li>
            <li>District Courts (Trial Level)</li>
            <li>29,156 Verified Legal Passages</li>
          </ul>
        </div>

        <div>
          <h4
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "0.75rem",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.12em",
              color: "var(--text-faint)",
              marginBottom: "1rem",
            }}
          >
            Methodology
          </h4>
          <ul
            style={{
              listStyle: "none",
              display: "flex",
              flexDirection: "column",
              gap: "0.55rem",
              fontSize: "0.85rem",
              color: "var(--text-muted)",
            }}
          >
            <li>
              <Link href="/#methodology">
                Hybrid RRF Retrieval
              </Link>
            </li>
            <li>
              <Link href="/#principle">
                Evidence Selection
              </Link>
            </li>
            <li>
              <Link href="/#evidence">
                Claim-to-Authority Provenance
              </Link>
            </li>
            <li>
              <Link href="/lawyer" style={{ color: "var(--maroon)", fontWeight: 600 }}>
                Lawyer Workspace &rarr;
              </Link>
            </li>
          </ul>
        </div>
      </div>

      <div
        style={{
          maxWidth: "1200px",
          margin: "2.5rem auto 0 auto",
          paddingTop: "1.5rem",
          borderTop: "1px solid var(--border-subtle)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "0.75rem",
          color: "var(--text-faint)",
          fontFamily: "var(--font-sans)",
        }}
      >
        <span>&copy; 2024 Vidhik Judicial Research. Certified Indian Legal Corpus.</span>
        <span>Institutional Edition &bull; Grounded Evidence Model</span>
      </div>
    </footer>
  );
}
