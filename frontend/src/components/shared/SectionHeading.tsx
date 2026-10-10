import React from "react";

interface SectionHeadingProps {
  badge?: string;
  title: string | React.ReactNode;
  subtitle?: string | React.ReactNode;
  align?: "left" | "center";
  maxWidth?: string;
}

export function SectionHeading({
  badge,
  title,
  subtitle,
  align = "center",
  maxWidth = "720px",
}: SectionHeadingProps) {
  const isCenter = align === "center";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isCenter ? "center" : "flex-start",
        textAlign: isCenter ? "center" : "left",
        maxWidth,
        margin: isCenter ? "0 auto 3rem auto" : "0 0 2.5rem 0",
      }}
    >
      {badge && (
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.22rem 0.65rem",
            border: "1px solid var(--border-rule)",
            borderRadius: "2px",
            backgroundColor: "var(--bg-surface)",
            fontSize: "0.7rem",
            fontFamily: "var(--font-sans)",
            fontWeight: 700,
            letterSpacing: "0.15em",
            color: "var(--maroon)",
            textTransform: "uppercase",
            marginBottom: "1rem",
          }}
        >
          {badge}
        </div>
      )}

      <h2
        style={{
          fontFamily: "var(--font-serif)",
          fontSize: "2.35rem",
          lineHeight: 1.2,
          fontWeight: 700,
          color: "var(--text-ink)",
          letterSpacing: "-0.015em",
          marginBottom: subtitle ? "0.85rem" : 0,
        }}
      >
        {title}
      </h2>

      {subtitle && (
        <p
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "1.05rem",
            lineHeight: 1.65,
            color: "var(--text-muted)",
            maxWidth: "640px",
          }}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
}
