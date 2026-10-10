"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/landing/Navbar";
import { Hero } from "@/components/landing/Hero";
import { ProductExplanation } from "@/components/landing/ProductExplanation";
import { EvidenceFlow } from "@/components/landing/EvidenceFlow";
import { ResearchMetrics } from "@/components/landing/ResearchMetrics";
import { ArchitectureFlow } from "@/components/landing/ArchitectureFlow";
import { ProfileEntry } from "@/components/landing/ProfileEntry";
import { LandingFooter } from "@/components/landing/Footer";

export default function VidhikLandingPage() {
  const router = useRouter();

  const handleNavigateGetStarted = () => {
    router.push("/chat");
  };

  const handleNavigateSignIn = () => {
    router.push("/login");
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
      {/* 1. Minimal Institutional Sticky Navbar */}
      <Navbar
        onGetStartedClick={handleNavigateGetStarted}
        onSignInClick={handleNavigateSignIn}
      />

      <main style={{ flex: 1 }}>
        {/* 2. Hero Section: Editorial Typography + Traceability Animation */}
        <Hero
          onGetStartedClick={handleNavigateGetStarted}
          onSignInClick={handleNavigateSignIn}
        />

        {/* 3. What is Vidhik? Legal information is more than finding a document */}
        <ProductExplanation />

        {/* 4. Why Evidence Matters: Interactive Claim → Evidence → Judgment → Para → Source */}
        <EvidenceFlow />

        {/* 5. Research / Experimentation: 1,361 Verified Corpus + DC Pipeline + Retrieval Audit */}
        <ResearchMetrics />

        {/* 6. Simplified Visual Architecture: More than PDF → LLM → Answer */}
        <ArchitectureFlow />

        {/* 7. Product Experience / Profile Selection: Three Circular Nodes → Morph to Signup */}
        <ProfileEntry />
      </main>

      {/* 8. Institutional Editorial Footer */}
      <LandingFooter />
    </div>
  );
}
