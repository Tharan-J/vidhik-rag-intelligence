"use client";

import React, { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Logo } from "@/components/shared/Logo";
import { ArrowRight, Scale, Briefcase } from "lucide-react";

function GetStartedRedirector() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    if (searchParams.get("mode") === "signin") {
      router.replace("/login");
    } else {
      router.replace("/chat");
    }
  }, [searchParams, router]);

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
      <div style={{ marginTop: "2rem", fontSize: "0.95rem", color: "var(--text-muted)" }}>
        Directing you to the appropriate Vidhik portal...
      </div>
      <div style={{ marginTop: "1.5rem", display: "flex", gap: "1rem" }}>
        <Link
          href="/chat"
          style={{
            padding: "0.6rem 1.2rem",
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
          <span>Public Legal Chatbot</span>
        </Link>
        <Link
          href="/login"
          style={{
            padding: "0.6rem 1.2rem",
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border-rule)",
            color: "var(--text-ink)",
            borderRadius: "2px",
            textDecoration: "none",
            fontSize: "0.88rem",
            fontWeight: 600,
            display: "inline-flex",
            alignItems: "center",
            gap: "0.4rem",
          }}
        >
          <Briefcase size={14} />
          <span>Lawyer Login</span>
        </Link>
      </div>
    </div>
  );
}

export default function GetStartedPage() {
  return (
    <Suspense fallback={<div>Loading Vidhik...</div>}>
      <GetStartedRedirector />
    </Suspense>
  );
}
