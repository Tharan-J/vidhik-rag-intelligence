import React from "react";

interface MetricCardProps {
  value: string;
  unit?: string;
  label: string;
  description: string;
  benchmarkContext?: string;
}

export function MetricCard({
  value,
  unit,
  label,
  description,
  benchmarkContext = "Audited experimental benchmark",
}: MetricCardProps) {
  return (
    <div
      className="paper-card"
      style={{
        padding: "1.75rem 1.5rem",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        borderRadius: "3px",
        height: "100%",
        position: "relative",
        background: "var(--bg-surface)",
      }}
    >
      <div>
        {/* Top context badge */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.35rem",
            fontSize: "0.65rem",
            fontFamily: "var(--font-sans)",
            fontWeight: 600,
            color: "var(--text-faint)",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            marginBottom: "1rem",
          }}
        >
          <span
            style={{
              width: "5px",
              height: "5px",
              borderRadius: "50%",
              backgroundColor: "var(--brass)",
              display: "inline-block",
            }}
          />
          {benchmarkContext}
        </div>

        {/* Large Numeric Value */}
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: "0.35rem",
            marginBottom: "0.5rem",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "2.8rem",
              fontWeight: 700,
              color: "var(--navy)",
              lineHeight: 1,
              letterSpacing: "-0.02em",
            }}
          >
            {value}
          </span>
          {unit && (
            <span
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1.3rem",
                color: "var(--maroon)",
                fontWeight: 600,
              }}
            >
              {unit}
            </span>
          )}
        </div>

        {/* Metric Label */}
        <h3
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "1rem",
            fontWeight: 600,
            color: "var(--text-ink)",
            marginBottom: "0.6rem",
          }}
        >
          {label}
        </h3>

        {/* Supporting context */}
        <p
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "0.85rem",
            lineHeight: 1.55,
            color: "var(--text-muted)",
          }}
        >
          {description}
        </p>
      </div>

      <div
        style={{
          marginTop: "1.25rem",
          paddingTop: "0.85rem",
          borderTop: "1px solid var(--border-subtle)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <span
          style={{
            fontSize: "0.68rem",
            fontFamily: "var(--font-mono)",
            color: "var(--text-faint)",
          }}
        >
          VERIFIED DATASET
        </span>
        <span
          style={{
            fontSize: "0.68rem",
            fontWeight: 600,
            color: "var(--maroon)",
            letterSpacing: "0.04em",
          }}
        >
          FROZEN BENCHMARK
        </span>
      </div>
    </div>
  );
}
