"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Logo } from "@/components/shared/Logo";
import { Scale } from "lucide-react";

export default function CommonPersonWorkspacePage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/chat");
  }, [router]);

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "var(--bg-parchment)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        textAlign: "center",
      }}
    >
      <Logo size="lg" withTagline={true} />
      <div style={{ marginTop: "1.5rem", fontSize: "0.95rem", color: "var(--text-muted)" }}>
        Common person workspace has been consolidated into the Public Multilingual Legal Assistant.
      </div>
      <Link
        href="/chat"
        style={{
          marginTop: "1.25rem",
          padding: "0.6rem 1.25rem",
          backgroundColor: "var(--maroon)",
          color: "#FFF",
          borderRadius: "2px",
          textDecoration: "none",
          fontSize: "0.88rem",
          fontWeight: 600,
          display: "inline-flex",
          alignItems: "center",
          gap: "0.4rem",
        }}
      >
        <Scale size={14} />
        <span>Open Public Legal Assistant</span>
      </Link>
    </div>
  );
}
