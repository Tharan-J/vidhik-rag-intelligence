"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, ChevronDown, ShieldCheck, Database, Layers } from "lucide-react";
import { HeroAnimation } from "./HeroAnimation";

interface HeroProps {
  onGetStartedClick?: () => void;
  onSignInClick?: () => void;
}

export function Hero({ onGetStartedClick, onSignInClick }: HeroProps) {
  const router = useRouter();

  const handleGetStarted = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onGetStartedClick) {
      onGetStartedClick();
    } else {
      router.push("/chat");
    }
  };

  const handleSignIn = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onSignInClick) {
      onSignInClick();
    } else {
      router.push("/login");
    }
  };

  const handleExplore = (e: React.MouseEvent) => {
    e.preventDefault();
    const el = document.getElementById("evidence-matters");
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section
      style={{
        padding: "3.5rem 2rem 5rem 2rem",
        maxWidth: "1280px",
        margin: "0 auto",
        position: "relative",
      }}
      aria-label="Vidhik Introduction & Core Positioning"
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.05fr 0.95fr",
          gap: "4rem",
          alignItems: "center",
        }}
        className="hero-grid"
      >
        {/* Left Column: Core Positioning & Typography */}
        <div>
          {/* Institutional Stamp Ribbon */}
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.25rem 0.65rem",
              border: "1px solid var(--border-rule)",
              borderRadius: "2px",
              backgroundColor: "var(--bg-surface)",
              fontSize: "0.72rem",
              fontFamily: "var(--font-sans)",
              fontWeight: 700,
              letterSpacing: "0.14em",
              color: "var(--maroon)",
              textTransform: "uppercase",
              marginBottom: "1.75rem",
            }}
          >
            <ShieldCheck size={14} color="var(--maroon)" />
            <span>INDIAN JUDICIAL INTELLIGENCE</span>
          </div>

          {/* Three-Line Signature Typography */}
          <h1
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "3.4rem",
              lineHeight: 1.12,
              color: "var(--text-ink)",
              fontWeight: 700,
              letterSpacing: "-0.025em",
              marginBottom: "1.5rem",
            }}
          >
            Find the law.
            <br />
            <span style={{ color: "var(--maroon)", fontStyle: "italic" }}>
              See the evidence.
            </span>
            <br />
            Understand the authority.
          </h1>

          {/* Supporting Description */}
          <p
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "1.2rem",
              lineHeight: 1.6,
              color: "var(--navy)",
              marginBottom: "1.25rem",
              maxWidth: "560px",
            }}
          >
            Vidhik is a personalized legal intelligence workspace built around
            Indian judicial documents, evidence-grounded retrieval and verifiable
            legal explanations.
          </p>

          <p
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "0.95rem",
              lineHeight: 1.65,
              color: "var(--text-muted)",
              marginBottom: "2.5rem",
              maxWidth: "520px",
            }}
          >
            The generated response is not the authority. Vidhik preserves the court,
            case citation, decision bench, page, and exact paragraph behind every legal claim.
          </p>

          {/* Action CTAs */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "1.25rem",
              flexWrap: "wrap",
              marginBottom: "3rem",
            }}
          >
            <button
              onClick={handleGetStarted}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.6rem",
                backgroundColor: "var(--maroon)",
                color: "#FFFFFF",
                padding: "0.85rem 1.75rem",
                borderRadius: "2px",
                fontFamily: "var(--font-sans)",
                fontSize: "0.95rem",
                fontWeight: 600,
                letterSpacing: "0.02em",
                border: "1px solid var(--maroon-dark)",
                boxShadow: "0 2px 6px rgba(110, 31, 42, 0.25)",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "var(--maroon-dark)";
                e.currentTarget.style.transform = "translateY(-1px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "var(--maroon)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              Get Started
              <ArrowRight size={16} />
            </button>

            <button
              onClick={handleExplore}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
                backgroundColor: "transparent",
                color: "var(--text-ink)",
                padding: "0.85rem 1.4rem",
                borderRadius: "2px",
                fontFamily: "var(--font-sans)",
                fontSize: "0.95rem",
                fontWeight: 500,
                border: "1px solid var(--border-rule)",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--border-dark)";
                e.currentTarget.style.backgroundColor = "var(--bg-surface)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border-rule)";
                e.currentTarget.style.backgroundColor = "transparent";
              }}
            >
              Explore how it works
              <ChevronDown size={16} color="var(--text-muted)" />
            </button>
          </div>

          {/* Quick Institutional Highlights */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "1.5rem",
              paddingTop: "1.75rem",
              borderTop: "1px solid var(--border-rule)",
              maxWidth: "540px",
            }}
          >
            <div>
              <div
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "1.2rem",
                  fontWeight: 700,
                  color: "var(--navy)",
                }}
              >
                1,361 Docs
              </div>
              <div
                style={{
                  fontFamily: "var(--font-sans)",
                  fontSize: "0.75rem",
                  color: "var(--text-muted)",
                }}
              >
                Verified Frozen Corpus
              </div>
            </div>

            <div>
              <div
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "1.2rem",
                  fontWeight: 700,
                  color: "var(--maroon)",
                }}
              >
                0%
              </div>
              <div
                style={{
                  fontFamily: "var(--font-sans)",
                  fontSize: "0.75rem",
                  color: "var(--text-muted)",
                }}
              >
                Evidence Contradiction
              </div>
            </div>

            <div>
              <div
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "1.2rem",
                  fontWeight: 700,
                  color: "var(--navy)",
                }}
              >
                81.6%
              </div>
              <div
                style={{
                  fontFamily: "var(--font-sans)",
                  fontSize: "0.75rem",
                  color: "var(--text-muted)",
                }}
              >
                Critical Facts Recovered
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Traceability Animated Pipeline */}
        <div>
          <HeroAnimation />
        </div>
      </div>
    </section>
  );
}
