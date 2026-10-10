"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Logo } from "../shared/Logo";

interface NavbarProps {
  onGetStartedClick?: () => void;
  onSignInClick?: () => void;
}

export function Navbar({ onGetStartedClick, onSignInClick }: NavbarProps) {
  const router = useRouter();
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToSection = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault();
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

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

  return (
    <header
      className={isScrolled ? "glass-nav" : ""}
      style={{
        position: "sticky",
        top: 0,
        zIndex: 100,
        backgroundColor: isScrolled
          ? "rgba(255, 253, 248, 0.94)"
          : "rgba(247, 244, 238, 0.92)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
        borderBottom: `1px solid ${isScrolled ? "var(--border-rule)" : "rgba(217, 210, 197, 0.6)"}`,
        boxShadow: isScrolled
          ? "0 4px 24px rgba(30, 32, 36, 0.05), inset 0 -1px 0 rgba(194, 159, 98, 0.15)"
          : "none",
        transition: "all 0.25s ease-in-out",
        padding: "0.85rem 2.25rem",
      }}
    >
      <div
        style={{
          maxWidth: "1320px",
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        {/* Left: Brand Identity */}
        <Logo size="md" withTagline={true} />

        {/* Right Navigation */}
        <nav
          style={{
            display: "flex",
            alignItems: "center",
            gap: "2.25rem",
          }}
          aria-label="Main Navigation"
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "2rem",
            }}
          >
            <a
              href="#what-is-vidhik"
              onClick={(e) => scrollToSection(e, "what-is-vidhik")}
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.88rem",
                fontWeight: 600,
                color: "var(--text-ink)",
                textDecoration: "none",
                position: "relative",
                padding: "0.25rem 0",
                transition: "color 0.15s ease",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--maroon)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-ink)")}
            >
              Product
            </a>

            <a
              href="#evidence-matters"
              onClick={(e) => scrollToSection(e, "evidence-matters")}
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.88rem",
                fontWeight: 600,
                color: "var(--text-ink)",
                textDecoration: "none",
                position: "relative",
                padding: "0.25rem 0",
                transition: "color 0.15s ease",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--maroon)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-ink)")}
            >
              How it Works
            </a>

            <a
              href="#research-metrics"
              onClick={(e) => scrollToSection(e, "research-metrics")}
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.88rem",
                fontWeight: 600,
                color: "var(--text-ink)",
                textDecoration: "none",
                position: "relative",
                padding: "0.25rem 0",
                transition: "color 0.15s ease",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--maroon)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-ink)")}
            >
              Research
            </a>

            {/* Lawyer Sign In Portal Button */}
            <button
              onClick={handleSignIn}
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "0.84rem",
                fontWeight: 600,
                color: "var(--text-ink)",
                backgroundColor: "var(--bg-sheet)",
                border: "1px solid var(--border-rule)",
                borderRadius: "4px",
                cursor: "pointer",
                padding: "0.45rem 0.95rem",
                transition: "all 0.18s ease",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.4rem",
                boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--maroon)";
                e.currentTarget.style.color = "var(--maroon)";
                e.currentTarget.style.backgroundColor = "var(--maroon-faint)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border-rule)";
                e.currentTarget.style.color = "var(--text-ink)";
                e.currentTarget.style.backgroundColor = "var(--bg-sheet)";
              }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <rect width="20" height="14" x="2" y="7" rx="2" ry="2"/>
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
              </svg>
              <span>Lawyer Login</span>
            </button>
          </div>

          {/* Primary CTA: Get Started with Public Chatbot */}
          <button
            onClick={handleGetStarted}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.55rem",
              background: "linear-gradient(135deg, #7A1C28 0%, #541620 100%)",
              color: "#FFF9EE",
              padding: "0.58rem 1.35rem",
              borderRadius: "4px",
              fontFamily: "var(--font-sans)",
              fontSize: "0.88rem",
              fontWeight: 700,
              letterSpacing: "0.02em",
              border: "1px solid rgba(194, 159, 98, 0.4)",
              boxShadow: "0 2px 8px rgba(110, 31, 42, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.25)",
              transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
              cursor: "pointer",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-1px)";
              e.currentTarget.style.boxShadow = "0 4px 14px rgba(110, 31, 42, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.35)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateY(0px)";
              e.currentTarget.style.boxShadow = "0 2px 8px rgba(110, 31, 42, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.25)";
            }}
          >
            <span>Public Chatbot</span>
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
        </nav>
      </div>
    </header>
  );
}
