import React from "react";
import Link from "next/link";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  withTagline?: boolean;
  href?: string;
}

export function Logo({ size = "md", withTagline = true, href = "/" }: LogoProps) {
  const isSmall = size === "sm";
  const isLarge = size === "lg";

  return (
    <Link
      href={href}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: isSmall ? "0.6rem" : "0.85rem",
        textDecoration: "none",
        transition: "opacity 0.2s ease",
      }}
    >
      {/* Institutional Seal Medallion */}
      <div
        style={{
          width: isSmall ? "30px" : isLarge ? "46px" : "38px",
          height: isSmall ? "30px" : isLarge ? "46px" : "38px",
          border: "1.5px solid var(--maroon)",
          borderRadius: "6px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "var(--maroon)",
          boxShadow: "0 2px 8px rgba(110, 31, 42, 0.22), inset 0 1px 1px rgba(255, 255, 255, 0.3)",
          position: "relative",
          flexShrink: 0,
          background: "linear-gradient(135deg, #7A1C28 0%, #541620 100%)",
        }}
      >
        {/* Inner Gold Frame */}
        <div
          style={{
            position: "absolute",
            inset: "2px",
            border: "1px solid rgba(194, 159, 98, 0.45)",
            borderRadius: "4px",
            pointerEvents: "none",
          }}
        />
        <span
          style={{
            fontFamily: "var(--font-brand)",
            fontWeight: 800,
            fontSize: isSmall ? "0.95rem" : isLarge ? "1.45rem" : "1.2rem",
            color: "#FFF9EE",
            lineHeight: 1,
            letterSpacing: "0.02em",
            textShadow: "0 1px 2px rgba(0,0,0,0.4)",
          }}
        >
          V
        </span>
      </div>

      <div style={{ display: "flex", flexDirection: "column" }}>
        <span
          style={{
            fontFamily: "var(--font-brand)",
            fontSize: isSmall ? "1.15rem" : isLarge ? "1.75rem" : "1.42rem",
            fontWeight: 800,
            letterSpacing: "0.14em",
            color: "var(--text-ink)",
            lineHeight: 1.05,
          }}
        >
          VIDHIK
        </span>
        {withTagline && (
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: isSmall ? "0.55rem" : "0.62rem",
              fontWeight: 700,
              letterSpacing: "0.22em",
              color: "var(--brass)",
              textTransform: "uppercase",
              marginTop: "3px",
            }}
          >
            JUDICIAL INTELLIGENCE
          </span>
        )}
      </div>
    </Link>
  );
}
