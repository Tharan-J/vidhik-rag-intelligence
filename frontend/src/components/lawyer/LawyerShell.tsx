"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Logo } from "../shared/Logo";
import {
  Briefcase,
  ChevronRight,
  LogOut,
  ShieldCheck,
} from "lucide-react";

interface LawyerShellProps {
  children: React.ReactNode;
  matterTitle?: string;
  matterCaseNumber?: string;
}

function LawyerShellInner({
  children,
  matterTitle,
  matterCaseNumber,
}: LawyerShellProps) {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    try {
      localStorage.removeItem("vidhik_user");
    } catch (e) {}
    router.push("/");
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        backgroundColor: "var(--bg-parchment)",
        color: "var(--text-ink)",
      }}
    >
      {/* =====================================================================
          TOP NAVIGATION BAR (NO SIDEBAR — LOGOUT & WORKSPACE CONTROLS IN NAVBAR)
          ===================================================================== */}
      <header
        style={{
          height: "62px",
          backgroundColor: "var(--bg-surface)",
          borderBottom: "1px solid var(--border-rule)",
          padding: "0 2rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          position: "sticky",
          top: 0,
          zIndex: 40,
          boxShadow: "0 1px 3px rgba(0, 0, 0, 0.02)",
        }}
      >
        {/* Left: Brand Identity & Breadcrumb */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.85rem", minWidth: 0 }}>
          <Logo size="sm" withTagline={false} href="/lawyer" />

          <div
            style={{
              width: "1px",
              height: "20px",
              backgroundColor: "var(--border-rule)",
            }}
          />

          {!matterTitle ? (
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.4rem",
                fontSize: "0.72rem",
                fontWeight: 700,
                color: "var(--maroon)",
                backgroundColor: "var(--maroon-faint)",
                padding: "0.2rem 0.55rem",
                borderRadius: "2px",
                border: "1px solid var(--maroon-border)",
                letterSpacing: "0.06em",
                textTransform: "uppercase",
              }}
            >
              <Briefcase size={12} />
              <span>Advocate Workspace</span>
            </div>
          ) : (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.55rem",
                minWidth: 0,
              }}
            >
              <Link
                href="/lawyer"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.35rem",
                  fontSize: "0.82rem",
                  fontWeight: 600,
                  color: "var(--text-muted)",
                  textDecoration: "none",
                  transition: "color 0.15s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--maroon)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
              >
                <Briefcase size={13} />
                <span>Matters</span>
              </Link>

              <ChevronRight size={14} color="var(--border-dark)" />

              <span
                style={{
                  fontSize: "0.85rem",
                  fontWeight: 700,
                  color: "var(--text-ink)",
                  maxWidth: "420px",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {matterTitle}
              </span>

              {matterCaseNumber && (
                <span
                  style={{
                    fontSize: "0.72rem",
                    fontFamily: "var(--font-mono)",
                    color: "var(--maroon)",
                    backgroundColor: "var(--maroon-faint)",
                    padding: "0.15rem 0.5rem",
                    borderRadius: "2px",
                    border: "1px solid var(--maroon-border)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {matterCaseNumber}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Right: Subsystem Health, Profile & Logout */}
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {/* Subsystem Health Badge */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.45rem",
              fontSize: "0.72rem",
              color: "var(--status-supported-text)",
              backgroundColor: "var(--status-supported-bg)",
              border: "1px solid var(--status-supported-border)",
              padding: "0.25rem 0.65rem",
              borderRadius: "2px",
            }}
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                backgroundColor: "var(--status-supported-text)",
                display: "inline-block",
              }}
            />
            <span style={{ fontWeight: 600 }}>RAG & Gemini Connected</span>
          </div>

          {/* Quick link to All Matters if in matter workspace */}
          {matterTitle && (
            <Link
              href="/lawyer"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.4rem",
                fontSize: "0.8rem",
                fontWeight: 600,
                padding: "0.35rem 0.75rem",
                border: "1px solid var(--border-rule)",
                borderRadius: "2px",
                backgroundColor: "var(--bg-parchment)",
                color: "var(--text-ink)",
                textDecoration: "none",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "var(--bg-card-hover)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "var(--bg-parchment)";
              }}
            >
              <Briefcase size={13} color="var(--maroon)" />
              <span>All Matters</span>
            </Link>
          )}

          {/* User Profile Pill */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.55rem",
              padding: "0.25rem 0.65rem 0.25rem 0.35rem",
              borderRadius: "2px",
              border: "1px solid var(--border-rule)",
              backgroundColor: "var(--bg-parchment)",
            }}
          >
            <div
              style={{
                width: "28px",
                height: "28px",
                borderRadius: "50%",
                backgroundColor: "var(--navy)",
                color: "#FFFFFF",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "0.76rem",
                fontWeight: 700,
              }}
            >
              RS
            </div>
            <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.15 }}>
              <span
                style={{
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  color: "var(--text-ink)",
                }}
              >
                Adv. Rajesh Sharma
              </span>
              <span style={{ fontSize: "0.66rem", color: "var(--text-faint)" }}>
                Madras High Court Bar
              </span>
            </div>
          </div>

          {/* Logout Button in Navbar */}
          <button
            onClick={handleLogout}
            title="Sign out of workspace"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.45rem",
              padding: "0.42rem 0.9rem",
              borderRadius: "2px",
              border: "1px solid var(--border-dark)",
              backgroundColor: "var(--bg-surface)",
              color: "var(--text-ink)",
              fontSize: "0.8rem",
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "var(--maroon-faint)";
              e.currentTarget.style.borderColor = "var(--maroon-border)";
              e.currentTarget.style.color = "var(--maroon)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "var(--bg-surface)";
              e.currentTarget.style.borderColor = "var(--border-dark)";
              e.currentTarget.style.color = "var(--text-ink)";
            }}
          >
            <LogOut size={14} />
            <span>Logout</span>
          </button>
        </div>
      </header>

      {/* =====================================================================
          MAIN DASHBOARD & WORKSPACE CONTENT (FULL WIDTH)
          ===================================================================== */}
      <main
        style={{
          flex: 1,
          width: "100%",
          maxWidth: "1480px",
          margin: "0 auto",
          padding: "2rem 2.5rem 4rem 2.5rem",
        }}
      >
        {children}
      </main>
    </div>
  );
}

export function LawyerShell(props: LawyerShellProps) {
  return (
    <React.Suspense
      fallback={
        <div style={{ minHeight: "100vh", backgroundColor: "var(--bg-parchment)" }}>
          {props.children}
        </div>
      }
    >
      <LawyerShellInner {...props} />
    </React.Suspense>
  );
}
