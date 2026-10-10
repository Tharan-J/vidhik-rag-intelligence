"use client";

import React, { useEffect, useState } from "react";
import { fetchStatus } from "../lib/api";
import { SystemStatusResponse } from "../lib/types";

export function StatusBadge() {
  const [statusData, setStatusData] = useState<SystemStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadStatus() {
      try {
        const res = await fetchStatus();
        if (isMounted) setStatusData(res);
      } catch (e) {
        // Handled silently
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadStatus();
    const interval = setInterval(loadStatus, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const isReady = statusData?.status === "ready";
  const pointsCount = statusData?.components?.qdrant?.details?.points_count || 29156;

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.5rem",
        padding: "0.25rem 0.65rem",
        borderRadius: "2px",
        border: "1px solid var(--border-rule)",
        backgroundColor: "var(--bg-surface)",
        fontSize: "0.75rem",
        fontFamily: "var(--font-sans)",
        color: "var(--text-muted)",
        letterSpacing: "0.02em",
      }}
      title={`Qdrant Vector Points: ${pointsCount.toLocaleString()} | BM25 Chunks: 29,156 | Model: BGE-M3 + Qwen`}
    >
      <span
        style={{
          width: "6px",
          height: "6px",
          borderRadius: "50%",
          backgroundColor: isReady ? "#2E7D32" : "#F57C00",
          display: "inline-block",
        }}
      />
      <span>
        {loading ? (
          "Checking archive..."
        ) : isReady ? (
          <span>
            <strong style={{ color: "var(--text-ink)", fontWeight: 600 }}>Corpus Active</strong> &bull; {pointsCount.toLocaleString()} Passages
          </span>
        ) : (
          <span>Degraded Mode</span>
        )}
      </span>
    </div>
  );
}
