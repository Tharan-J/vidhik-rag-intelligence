"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { StatusBadge } from "./StatusBadge";

export function Header() {
  const pathname = usePathname();
  const isApp = pathname === "/app";

  return (
    <header
      style={{
        backgroundColor: "var(--bg-surface)",
        borderBottom: "1px solid var(--border-rule)",
        padding: "0.85rem 2rem",
        position: "sticky",
        top: 0,
        zIndex: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}
    >
      {/* Brand Title */}
      <div style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
        <Link href="/" style={{ display: "flex", flexDirection: "column" }}>
          <span
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "1.35rem",
              fontWeight: 700,
              letterSpacing: "0.08em",
              color: "var(--text-ink)",
              lineHeight: 1.1,
            }}
          >
            VIDHIK
          </span>
          <span
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "0.62rem",
              fontWeight: 600,
              letterSpacing: "0.18em",
              color: "var(--maroon)",
              textTransform: "uppercase",
            }}
          >
            Indian Judicial Research
          </span>
        </Link>

        <div
          style={{
            height: "22px",
            width: "1px",
            backgroundColor: "var(--border-rule)",
            display: "inline-block",
          }}
        />

        <StatusBadge />
      </div>

      {/* Navigation */}
      <nav style={{ display: "flex", alignItems: "center", gap: "1.75rem" }}>
        <Link
          href="/"
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "0.85rem",
            fontWeight: 500,
            color: !isApp ? "var(--maroon)" : "var(--text-muted)",
            transition: "color 0.15s",
          }}
        >
          Overview
        </Link>
        <Link
          href="/#methodology"
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "0.85rem",
            fontWeight: 500,
            color: "var(--text-muted)",
            transition: "color 0.15s",
          }}
        >
          Methodology
        </Link>
        <Link
          href="/#hierarchy"
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "0.85rem",
            fontWeight: 500,
            color: "var(--text-muted)",
            transition: "color 0.15s",
          }}
        >
          Judicial Hierarchy
        </Link>

        {isApp ? (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
              backgroundColor: "var(--maroon-faint)",
              color: "var(--maroon)",
              border: "1px solid var(--maroon-border)",
              padding: "0.4rem 0.9rem",
              borderRadius: "2px",
              fontSize: "0.8rem",
              fontWeight: 600,
              fontFamily: "var(--font-sans)",
              letterSpacing: "0.04em",
            }}
          >
            Research Workspace
          </span>
        ) : (
          <Link
            href="/lawyer"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
              backgroundColor: "var(--maroon)",
              color: "#FFFFFF",
              padding: "0.45rem 1.15rem",
              borderRadius: "2px",
              fontSize: "0.82rem",
              fontWeight: 600,
              fontFamily: "var(--font-sans)",
              letterSpacing: "0.03em",
              transition: "background-color 0.15s",
            }}
          >
            Lawyer Workspace &rarr;
          </Link>
        )}
      </nav>
    </header>
  );
}
