"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Logo } from "../shared/Logo";
import {
  Briefcase,
  BookOpen,
  HelpCircle,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Shield,
  Layers,
  Sparkles,
} from "lucide-react";

interface ProfilePlaceholderProps {
  profileKey: "lawyer" | "student" | "common";
  title: string;
  concept: string;
  description: string;
  tags: string[];
}

export function ProfilePlaceholder({
  profileKey,
  title,
  concept,
  description,
  tags,
}: ProfilePlaceholderProps) {
  const router = useRouter();
  const [userName, setUserName] = useState<string>("Advocate / Researcher");
  const [userEmail, setUserEmail] = useState<string>("user@vidhik.in");

  useEffect(() => {
    try {
      const stored = localStorage.getItem("vidhik_user");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.name) setUserName(parsed.name);
        if (parsed.email) setUserEmail(parsed.email);
      }
    } catch (e) {
      // fallback
    }
  }, []);

  const getIcon = () => {
    switch (profileKey) {
      case "lawyer":
        return <Briefcase size={24} color="var(--maroon)" />;
      case "student":
        return <BookOpen size={24} color="var(--maroon)" />;
      case "common":
        return <HelpCircle size={24} color="var(--maroon)" />;
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "var(--bg-parchment)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Institutional Top Bar */}
      <header
        style={{
          backgroundColor: "var(--bg-surface)",
          borderBottom: "1px solid var(--border-rule)",
          padding: "0.85rem 2rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
          <Logo size="sm" withTagline={false} />
          <div
            style={{
              height: "20px",
              width: "1px",
              backgroundColor: "var(--border-rule)",
            }}
          />
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.45rem",
              padding: "0.2rem 0.6rem",
              backgroundColor: "var(--maroon-faint)",
              border: "1px solid var(--maroon-border)",
              borderRadius: "2px",
              fontSize: "0.75rem",
              fontWeight: 700,
              color: "var(--maroon)",
              letterSpacing: "0.05em",
            }}
          >
            {getIcon()}
            <span>{title.toUpperCase()} WORKSPACE</span>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div
            style={{
              fontSize: "0.82rem",
              fontFamily: "var(--font-sans)",
              color: "var(--text-ink)",
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-end",
            }}
          >
            <span style={{ fontWeight: 600 }}>{userName}</span>
            <span style={{ fontSize: "0.72rem", color: "var(--text-faint)" }}>
              {userEmail}
            </span>
          </div>

          <Link
            href="/"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
              fontSize: "0.8rem",
              color: "var(--text-muted)",
              padding: "0.4rem 0.75rem",
              border: "1px solid var(--border-rule)",
              borderRadius: "2px",
              backgroundColor: "var(--bg-surface)",
              textDecoration: "none",
            }}
          >
            <ArrowLeft size={13} />
            <span>Switch Profile</span>
          </Link>
        </div>
      </header>

      {/* Main Placeholder Container */}
      <main
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "3rem 1.5rem",
        }}
      >
        <div
          className="paper-card"
          style={{
            maxWidth: "680px",
            width: "100%",
            backgroundColor: "var(--bg-sheet)",
            border: "2px solid var(--border-rule)",
            borderRadius: "4px",
            padding: "3rem 2.5rem",
            boxShadow: "var(--shadow-layered)",
            textAlign: "center",
          }}
        >
          {/* Institutional Icon */}
          <div
            style={{
              width: "68px",
              height: "68px",
              borderRadius: "50%",
              backgroundColor: "var(--maroon-faint)",
              border: "2px solid var(--maroon-border)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 1.5rem auto",
            }}
          >
            {getIcon()}
          </div>

          {/* Section Heading */}
          <div
            style={{
              display: "inline-block",
              padding: "0.2rem 0.65rem",
              backgroundColor: "var(--bg-parchment)",
              border: "1px solid var(--border-rule)",
              borderRadius: "2px",
              fontSize: "0.72rem",
              fontWeight: 700,
              letterSpacing: "0.12em",
              color: "var(--navy)",
              textTransform: "uppercase",
              marginBottom: "1rem",
            }}
          >
            {concept}
          </div>

          <h1
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "2.25rem",
              lineHeight: 1.25,
              fontWeight: 700,
              color: "var(--text-ink)",
              marginBottom: "1rem",
            }}
          >
            Your personalized Vidhik workspace is being prepared.
          </h1>

          <p
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "1rem",
              lineHeight: 1.6,
              color: "var(--text-muted)",
              maxWidth: "520px",
              margin: "0 auto 2rem auto",
            }}
          >
            {description}
          </p>

          {/* Feature Pillars Preview */}
          <div
            style={{
              backgroundColor: "var(--bg-parchment)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "3px",
              padding: "1.25rem",
              marginBottom: "2.25rem",
              textAlign: "left",
            }}
          >
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.72rem",
                fontWeight: 700,
                color: "var(--maroon)",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                marginBottom: "0.75rem",
              }}
            >
              Configured Workspace Modules
            </div>

            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "0.5rem",
              }}
            >
              {tags.map((tag) => (
                <span
                  key={tag}
                  style={{
                    fontSize: "0.8rem",
                    padding: "0.25rem 0.65rem",
                    backgroundColor: "var(--bg-surface)",
                    border: "1px solid var(--border-rule)",
                    borderRadius: "2px",
                    color: "var(--navy)",
                    fontWeight: 500,
                  }}
                >
                  ✓ {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Institutional Status Notice */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.6rem",
              fontSize: "0.85rem",
              color: "var(--text-faint)",
              marginBottom: "2rem",
            }}
          >
            <Clock size={16} />
            <span>
              Phase 1 profile routing established. Phase 2 internal workspace in progress.
            </span>
          </div>

          {/* Back button */}
          <Link
            href="/"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              backgroundColor: "var(--navy)",
              color: "#FFFFFF",
              padding: "0.75rem 1.6rem",
              borderRadius: "2px",
              fontSize: "0.9rem",
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            <ArrowLeft size={15} />
            <span>Return to Vidhik Overview</span>
          </Link>
        </div>
      </main>
    </div>
  );
}
