"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { SectionHeading } from "../shared/SectionHeading";
import {
  Briefcase,
  Scale,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Languages,
} from "lucide-react";

const TWO_JOURNEYS = [
  {
    key: "lawyer",
    badge: "ADVOCATE ACCESS",
    title: "Lawyer Matter Workspace",
    verb: "AUTHENTICATE",
    concept: "Confidential Matter-Centric Intelligence",
    description: "Designed for Advocates, Law Firms, and In-House Counsel. Ingest private court records, manage procedural timelines, track framed issues, and verify evidence coordinates.",
    route: "/login",
    actionLabel: "Sign In to Lawyer Workspace",
    features: [
      "Confidential Private Document Intake & SHA-256 Storage",
      "Dynamic Case File Dossier & Matter Timeline",
      "Field-Level Source Provenance & Authority Binders",
      "Matter Intelligence Assistant with Full Workspace Context",
    ],
    icon: <Briefcase size={26} />,
  },
  {
    key: "public",
    badge: "PUBLIC ACCESS",
    title: "Public Multilingual Legal Chatbot",
    verb: "FREE ACCESS",
    concept: "Conversational Precedent & Statutory Guidance",
    description: "Accessible to citizens and researchers without requiring an advocate account. Ask legal questions in Tamil, Hindi, Kannada, Marathi, or English with optional judicial research grounding.",
    route: "/chat",
    actionLabel: "Get Started with Public Chatbot",
    features: [
      "No Account or Login Required &bull; Free Instant Access",
      "5 Supported Languages via IndicTrans2 with Entity Preservation",
      "Research Mode Toggle (BM25 + BGE-M3 + Qdrant Cloud + Qwen)",
      "Strict Abstention when Authoritative Judicial Evidence is Insufficient",
    ],
    icon: <Scale size={26} />,
  },
];

export function ProfileEntry() {
  const router = useRouter();

  return (
    <section
      id="workspace-profiles"
      style={{
        padding: "5.5rem 2rem 6.5rem 2rem",
        backgroundColor: "var(--bg-parchment)",
        borderTop: "1px solid var(--border-rule)",
        position: "relative",
      }}
      aria-label="Vidhik Two User Journeys"
    >
      <div style={{ maxWidth: "1280px", margin: "0 auto" }}>
        <SectionHeading
          badge="TWO ACCESS JOURNEYS"
          title="One legal intelligence engine. Two distinct journeys."
          subtitle="Choose between an authenticated matter workspace for practicing advocates or an open multilingual legal-information chatbot for citizens."
          align="center"
        />

        {/* 2 Editorial Journey Cards */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, 1fr)",
            gap: "2.5rem",
            marginTop: "3.5rem",
            marginBottom: "3.5rem",
          }}
          className="two-journeys-grid"
        >
          {TWO_JOURNEYS.map((journey) => (
            <div
              key={journey.key}
              className="paper-card"
              style={{
                padding: "2.5rem 2.25rem",
                borderRadius: "3px",
                backgroundColor: "var(--bg-sheet)",
                border: "1.5px solid var(--border-rule)",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                cursor: "pointer",
                transition: "all 0.2s ease",
                boxShadow: "var(--shadow-sheet)",
              }}
              onClick={() => router.push(journey.route)}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--maroon)";
                e.currentTarget.style.transform = "translateY(-2px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border-rule)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              <div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "1.5rem",
                  }}
                >
                  <div
                    style={{
                      width: "52px",
                      height: "52px",
                      borderRadius: "50%",
                      backgroundColor: "var(--maroon-faint)",
                      border: "1.5px solid var(--maroon-border)",
                      color: "var(--maroon)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    {journey.icon}
                  </div>

                  <span
                    style={{
                      fontSize: "0.72rem",
                      fontFamily: "var(--font-mono)",
                      fontWeight: 700,
                      letterSpacing: "0.12em",
                      textTransform: "uppercase",
                      color: "var(--maroon)",
                      backgroundColor: "var(--maroon-faint)",
                      padding: "0.25rem 0.65rem",
                      borderRadius: "2px",
                      border: "1px solid var(--maroon-border)",
                    }}
                  >
                    {journey.badge}
                  </span>
                </div>

                <h3
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.65rem",
                    fontWeight: 700,
                    color: "var(--text-ink)",
                    marginBottom: "0.35rem",
                  }}
                >
                  {journey.title}
                </h3>

                <div
                  style={{
                    fontSize: "0.78rem",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 700,
                    color: "var(--maroon)",
                    letterSpacing: "0.06em",
                    textTransform: "uppercase",
                    marginBottom: "1rem",
                  }}
                >
                  {journey.concept}
                </div>

                <p
                  style={{
                    fontSize: "0.9rem",
                    lineHeight: 1.6,
                    color: "var(--text-muted)",
                    marginBottom: "1.5rem",
                  }}
                >
                  {journey.description}
                </p>

                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.55rem",
                    marginBottom: "2rem",
                  }}
                >
                  {journey.features.map((feat, i) => (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: "0.5rem",
                        fontSize: "0.82rem",
                        color: "var(--text-ink)",
                      }}
                    >
                      <CheckCircle2
                        size={15}
                        color="var(--maroon)"
                        style={{ flexShrink: 0, marginTop: "2px" }}
                      />
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div
                style={{
                  paddingTop: "1.25rem",
                  borderTop: "1px solid var(--border-subtle)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-sans)",
                    fontSize: "0.92rem",
                    fontWeight: 600,
                    color: "var(--maroon)",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.4rem",
                  }}
                >
                  {journey.actionLabel}
                  <ArrowRight size={15} />
                </span>

                <span
                  style={{
                    fontSize: "0.72rem",
                    fontFamily: "var(--font-mono)",
                    color: "var(--text-faint)",
                  }}
                >
                  {journey.verb}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
