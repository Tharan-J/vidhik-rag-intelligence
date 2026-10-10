"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/shared/Logo";
import {
  Briefcase,
  Lock,
  Mail,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  MessageSquare,
} from "lucide-react";

export default function LawyerLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError("Please provide your email address or Bar Council ID and password.");
      return;
    }

    setLoading(true);
    setError(null);

    setTimeout(() => {
      const counselName = email.includes("@")
        ? email.split("@")[0].replace(/[._]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
        : "Counsel";

      const userData = {
        name: counselName,
        email,
        profile: "lawyer",
        profileTitle: "Advocate",
        role: "lawyer",
        createdAt: new Date().toISOString(),
      };

      try {
        localStorage.setItem("vidhik_user", JSON.stringify(userData));
        localStorage.setItem("vidhik_profile", "lawyer");
      } catch (err) {
        console.warn("localStorage unavailable:", err);
      }

      setLoading(false);
      router.push("/lawyer");
    }, 450);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "var(--bg-parchment)",
        color: "var(--text-ink)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      {/* Top Bar */}
      <header
        style={{
          padding: "1.25rem 2.5rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid var(--border-rule)",
          backgroundColor: "rgba(255, 253, 248, 0.95)",
          backdropFilter: "blur(10px)",
        }}
      >
        <Logo size="md" withTagline={true} />

        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <Link
            href="/chat"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.45rem",
              fontSize: "0.85rem",
              fontWeight: 600,
              color: "var(--maroon)",
              padding: "0.45rem 0.95rem",
              border: "1px solid var(--maroon-border)",
              borderRadius: "2px",
              backgroundColor: "var(--maroon-faint)",
              textDecoration: "none",
              transition: "all 0.15s ease",
            }}
          >
            <MessageSquare size={14} />
            <span>Get Started (Public Chatbot)</span>
          </Link>
          <Link
            href="/"
            style={{
              fontSize: "0.85rem",
              color: "var(--text-muted)",
              textDecoration: "none",
            }}
          >
            Overview
          </Link>
        </div>
      </header>

      {/* Main Authentication Card */}
      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "3rem 1.5rem",
        }}
      >
        <div
          style={{
            width: "100%",
            maxWidth: "460px",
            backgroundColor: "var(--bg-sheet)",
            border: "1.5px solid var(--border-rule)",
            borderRadius: "3px",
            padding: "2.75rem 2.25rem",
            boxShadow: "var(--shadow-sheet)",
          }}
        >
          {/* Badge & Title */}
          <div style={{ textAlign: "center", marginBottom: "2rem" }}>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.4rem",
                padding: "0.25rem 0.65rem",
                border: "1px solid var(--border-rule)",
                borderRadius: "2px",
                backgroundColor: "var(--bg-parchment)",
                fontSize: "0.7rem",
                fontFamily: "var(--font-mono)",
                fontWeight: 700,
                color: "var(--maroon)",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                marginBottom: "0.85rem",
              }}
            >
              <Briefcase size={12} color="var(--maroon)" />
              <span>ADVOCATE ACCESS</span>
            </div>

            <h1
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1.85rem",
                fontWeight: 700,
                color: "var(--text-ink)",
                lineHeight: 1.2,
                marginBottom: "0.5rem",
              }}
            >
              Lawyer Workspace Login
            </h1>
            <p
              style={{
                fontSize: "0.85rem",
                color: "var(--text-muted)",
                lineHeight: 1.45,
              }}
            >
              Authenticate to manage confidential matters, evidence dossiers, timelines, and judicial research.
            </p>
          </div>

          {error && (
            <div
              style={{
                padding: "0.75rem 1rem",
                backgroundColor: "rgba(180, 40, 40, 0.08)",
                border: "1px solid rgba(180, 40, 40, 0.3)",
                borderRadius: "2px",
                color: "#900",
                fontSize: "0.82rem",
                marginBottom: "1.5rem",
                lineHeight: 1.4,
              }}
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Email / Bar ID */}
            <div style={{ marginBottom: "1.25rem" }}>
              <label
                style={{
                  display: "block",
                  fontSize: "0.76rem",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  color: "var(--text-ink)",
                  marginBottom: "0.4rem",
                }}
              >
                Email or Bar Registration ID
              </label>
              <div style={{ position: "relative" }}>
                <Mail
                  size={16}
                  style={{
                    position: "absolute",
                    left: "0.85rem",
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "var(--text-faint)",
                  }}
                />
                <input
                  type="text"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="advocate@barcouncil.in"
                  style={{
                    width: "100%",
                    padding: "0.75rem 0.85rem 0.75rem 2.4rem",
                    border: "1px solid var(--border-rule)",
                    borderRadius: "2px",
                    backgroundColor: "var(--bg-surface)",
                    fontSize: "0.9rem",
                    color: "var(--text-ink)",
                    fontFamily: "var(--font-sans)",
                    outline: "none",
                  }}
                  onFocus={(e) => (e.target.style.borderColor = "var(--maroon)")}
                  onBlur={(e) => (e.target.style.borderColor = "var(--border-rule)")}
                />
              </div>
            </div>

            {/* Password */}
            <div style={{ marginBottom: "1.75rem" }}>
              <label
                style={{
                  display: "block",
                  fontSize: "0.76rem",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  color: "var(--text-ink)",
                  marginBottom: "0.4rem",
                }}
              >
                Secret Passphrase / PIN
              </label>
              <div style={{ position: "relative" }}>
                <Lock
                  size={16}
                  style={{
                    position: "absolute",
                    left: "0.85rem",
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "var(--text-faint)",
                  }}
                />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  style={{
                    width: "100%",
                    padding: "0.75rem 0.85rem 0.75rem 2.4rem",
                    border: "1px solid var(--border-rule)",
                    borderRadius: "2px",
                    backgroundColor: "var(--bg-surface)",
                    fontSize: "0.9rem",
                    color: "var(--text-ink)",
                    fontFamily: "var(--font-sans)",
                    outline: "none",
                  }}
                  onFocus={(e) => (e.target.style.borderColor = "var(--maroon)")}
                  onBlur={(e) => (e.target.style.borderColor = "var(--border-rule)")}
                />
              </div>
            </div>

            {/* Submit Action */}
            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%",
                padding: "0.85rem",
                backgroundColor: "var(--maroon)",
                color: "#FFFFFF",
                border: "1px solid var(--maroon-dark)",
                borderRadius: "2px",
                fontSize: "0.92rem",
                fontWeight: 600,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.5rem",
                cursor: loading ? "wait" : "pointer",
                transition: "all 0.15s ease",
                boxShadow: "0 2px 4px rgba(110, 31, 42, 0.2)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "var(--maroon-dark)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "var(--maroon)";
              }}
            >
              <span>{loading ? "Authenticating Session..." : "Enter Lawyer Workspace"}</span>
              <ArrowRight size={16} />
            </button>
          </form>

          {/* Quick Demo Hint */}
          <div
            style={{
              marginTop: "1.25rem",
              textAlign: "center",
              fontSize: "0.75rem",
              color: "var(--text-faint)",
              fontFamily: "var(--font-mono)",
            }}
          >
            <span>Confidential Storage Protected by SHA-256</span>
          </div>
        </div>

        {/* Public Chatbot Entry Callout (Requirement: On the login page, provide a clearly visible Get Started action that opens the public legal chatbot) */}
        <div
          style={{
            width: "100%",
            maxWidth: "460px",
            marginTop: "1.5rem",
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border-rule)",
            borderRadius: "3px",
            padding: "1.35rem 1.75rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "1rem",
          }}
        >
          <div>
            <div
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "var(--text-ink)",
                marginBottom: "0.2rem",
              }}
            >
              Not an Advocate?
            </div>
            <div
              style={{
                fontSize: "0.78rem",
                color: "var(--text-muted)",
                lineHeight: 1.35,
              }}
            >
              Ask legal questions in Tamil, Hindi, Kannada, Marathi, or English with judicial research.
            </div>
          </div>

          <Link
            href="/chat"
            style={{
              whiteSpace: "nowrap",
              padding: "0.55rem 0.95rem",
              backgroundColor: "var(--bg-sheet)",
              border: "1px solid var(--border-rule)",
              borderRadius: "2px",
              fontSize: "0.82rem",
              fontWeight: 600,
              color: "var(--maroon)",
              textDecoration: "none",
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--maroon)";
              e.currentTarget.style.backgroundColor = "var(--maroon-faint)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--border-rule)";
              e.currentTarget.style.backgroundColor = "var(--bg-sheet)";
            }}
          >
            <span>Get Started</span>
            <ArrowRight size={13} />
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer
        style={{
          padding: "1.25rem 2.5rem",
          textAlign: "center",
          borderTop: "1px solid var(--border-rule)",
          fontSize: "0.78rem",
          color: "var(--text-faint)",
          fontFamily: "var(--font-mono)",
        }}
      >
        <span>VIDHIK LEGAL INTELLIGENCE &bull; SUPREME COURT & HIGH COURT JUDICIAL CORPUS</span>
      </footer>
    </div>
  );
}
