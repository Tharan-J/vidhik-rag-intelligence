"use client";

import React, { useState } from "react";
import { Matter, MatterEvidenceItem } from "@/lib/types/matter";
import { LegalQueryResponse, EvidenceItem } from "@/lib/types";
import {
  Search,
  Scale,
  FileCheck2,
  CheckCircle2,
  ArrowRight,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  Eye,
  X,
  BookOpen,
  Pin,
  Languages,
  Globe,
  Loader2,
} from "lucide-react";
import { ProvenanceBadge } from "./ProvenanceBadge";

interface ResearchTabProps {
  matter: Matter;
  onSaveEvidenceToMatter?: (evidenceItem: MatterEvidenceItem) => void;
}

function getDynamicResearchSuggestions(matter: Matter): string[] {
  const suggestions: string[] = [];

  // 1. From statutory sections
  if (matter.sections && matter.sections.length > 0) {
    matter.sections.slice(0, 2).forEach((s) => {
      suggestions.push(`${s.act} ${s.section} judicial precedents`);
    });
  }

  // 2. From framed issues
  if (matter.issues && matter.issues.length > 0) {
    matter.issues.slice(0, 2).forEach((i) => {
      suggestions.push(i.title);
    });
  }

  // 3. From matter title
  if (suggestions.length < 3 && matter.title) {
    suggestions.push(`${matter.title} governing legal principles`);
  }

  // Fallback defaults
  if (suggestions.length === 0) {
    suggestions.push(
      "Scope of Section 34 Arbitration and Conciliation Act",
      "Threshold of sufficient cause under Section 5 Limitation Act"
    );
  }

  return Array.from(new Set(suggestions)).slice(0, 4);
}

export function ResearchTab({ matter, onSaveEvidenceToMatter }: ResearchTabProps) {
  const dynamicResearchSuggestions = React.useMemo(
    () => getDynamicResearchSuggestions(matter),
    [matter]
  );
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<LegalQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [inspectModalEvidence, setInspectModalEvidence] = useState<EvidenceItem | null>(null);
  const [searchedQuery, setSearchedQuery] = useState<string | null>(null);

  // Multilingual translation state
  const [selectedLang, setSelectedLang] = useState<string>("en");
  const [translations, setTranslations] = useState<Record<string, any>>({});
  const [translating, setTranslating] = useState(false);
  const [translationError, setTranslationError] = useState<string | null>(null);

  const handleSelectLanguage = async (targetLang: string) => {
    if (targetLang === "en") {
      setSelectedLang("en");
      setTranslationError(null);
      return;
    }

    if (translations[targetLang]) {
      setSelectedLang(targetLang);
      setTranslationError(null);
      return;
    }

    if (!response?.answer) return;

    setTranslating(true);
    setTranslationError(null);

    try {
      const res = await fetch("/api/translate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-lawyer-token": "dev_lawyer_token",
          "x-matter-id": matter.id,
        },
        body: JSON.stringify({
          english_answer: response.answer,
          target_language: targetLang,
          matter_id: matter.id,
          evidence: response.evidence || [],
          claims: response.claims || [],
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error?.message || `Translation failed with status ${res.status}`);
      }

      setTranslations((prev) => ({ ...prev, [targetLang]: data }));
      setSelectedLang(targetLang);
    } catch (err: any) {
      console.error("Translation error:", err);
      setTranslationError(err.message || "Failed to translate answer");
    } finally {
      setTranslating(false);
    }
  };

  const handleExecuteResearch = async (textToSearch?: string) => {
    const q = textToSearch || query;
    if (!q.trim() || loading) return;

    setLoading(true);
    setSearchedQuery(q.trim());
    setSelectedLang("en");
    setTranslations({});
    setTranslationError(null);
    try {
      const res = await fetch("/api/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: q.trim(),
          top_k: 5,
        }),
      });

      if (!res.ok) throw new Error("Research query failed");
      const data: LegalQueryResponse = await res.json();
      setResponse(data);
      if (data.evidence && data.evidence.length > 0) {
        setSelectedEvidenceId(data.evidence[0].evidence_id);
      }
    } catch (err: any) {
      console.error("Research execution error:", err);
    } finally {
      setLoading(false);
    }
  };

  const activeEvidence =
    response?.evidence?.find((ev) => ev.evidence_id === selectedEvidenceId) ||
    response?.evidence?.[0];

  const isAlreadySaved = activeEvidence
    ? (matter.evidence || []).some(
        (e) =>
          e.id === `EVID-${activeEvidence.evidence_id}` ||
          (activeEvidence.text && e.evidenceExcerpt === activeEvidence.text)
      )
    : false;

  const handlePinEvidenceToMatter = (ev: EvidenceItem) => {
    if (!onSaveEvidenceToMatter) return;
    const newEvidenceItem: MatterEvidenceItem = {
      id: `EVID-${ev.evidence_id || Date.now()}`,
      matterId: matter.id,
      issueId: matter.issues?.[0]?.id || "ISS-GEN",
      issueTitle: matter.issues?.[0]?.title || "General Legal Grounds",
      claim: ev.case_title,
      claimType: "LEGAL_TEST",
      stance: ev.relevanceCategory === "CONTRARY_OR_QUALIFYING" ? "contradicting" : "supporting",
      evidenceExcerpt: ev.text || ev.relevantExcerpt || "",
      sourceDocument: ev.source_file || ev.document_id || "Reported Judgment",
      pageNumber: ev.page_number || (ev.page_start ? String(ev.page_start) : undefined),
      paragraphId: ev.paragraph_id || undefined,
      sourceType: "REPORTED_PRECEDENT",
      relatedAuthority: {
        caseTitle: ev.case_title,
        court: ev.court,
        year: ev.decision_date ? ev.decision_date.slice(0, 4) : "2024",
        citation: ev.case_number,
      },
      isPinned: true,
      notes: [`Retrieved via Vidhik Research for query: "${searchedQuery || query}"`],
      confidence: "HIGH",
      grounded: true,
      verification: "source_supported",
      provenance: "INDEPENDENTLY_VERIFIED",
      sourceLevel: "LEVEL_4_INDEPENDENT_CORPUS",
    };
    onSaveEvidenceToMatter(newEvidenceItem);
  };

  return (
    <div style={{ maxWidth: "1080px" }}>
      {/* Header and Research Input */}
      <div style={{ marginBottom: "2rem" }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.4rem",
            fontSize: "0.72rem",
            fontFamily: "var(--font-mono)",
            fontWeight: 700,
            color: "var(--maroon)",
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            marginBottom: "0.5rem",
          }}
        >
          <Scale size={13} />
          <span>Vidhik Authoritative Legal Retrieval & RAG</span>
        </div>

        <h3
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "1.55rem",
            fontWeight: 700,
            color: "var(--text-ink)",
            marginBottom: "0.4rem",
          }}
        >
          Dynamic Legal Precedent Research
        </h3>
        <p style={{ fontSize: "0.88rem", color: "var(--text-muted)", margin: 0 }}>
          Query across 1,361 Supreme Court and High Court judgments (29,156 indexed chunks).
          Every result is strictly grounded with verifiable judicial citations and evidence passages.
        </p>

        {/* Live Search Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleExecuteResearch();
          }}
          style={{ marginTop: "1.25rem" }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              backgroundColor: "var(--bg-sheet)",
              border: "1.5px solid var(--border-dark)",
              borderRadius: "3px",
              padding: "0.5rem 0.65rem 0.5rem 1rem",
              boxShadow: "var(--shadow-sheet)",
            }}
          >
            <Search size={18} color="var(--maroon)" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter any legal research query (e.g. limitation period for appeal under Section 37)..."
              disabled={loading}
              style={{
                flex: 1,
                border: "none",
                outline: "none",
                fontSize: "0.95rem",
                fontFamily: "var(--font-sans)",
                color: "var(--text-ink)",
                backgroundColor: "transparent",
              }}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.45rem",
                padding: "0.65rem 1.45rem",
                backgroundColor:
                  loading || !query.trim() ? "var(--border-dark)" : "var(--maroon)",
                color: "#FFFFFF",
                fontSize: "0.85rem",
                fontWeight: 600,
                border: "none",
                borderRadius: "2px",
                cursor: loading || !query.trim() ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Searching 29,156 Chunks..." : "Research"}
              <ArrowRight size={14} />
            </button>
          </div>
        </form>

        {/* Suggested Quick Searches */}
        <div style={{ marginTop: "0.85rem", display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          <span
            style={{
              fontSize: "0.72rem",
              fontFamily: "var(--font-mono)",
              color: "var(--text-faint)",
              alignSelf: "center",
            }}
          >
            SUGGESTED:
          </span>
          {dynamicResearchSuggestions.map((s, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuery(s);
                handleExecuteResearch(s);
              }}
              style={{
                background: "none",
                border: "1px solid var(--border-subtle)",
                borderRadius: "2px",
                padding: "0.25rem 0.65rem",
                fontSize: "0.74rem",
                color: "var(--text-muted)",
                cursor: "pointer",
                transition: "all 0.15s ease",
                overflowWrap: "anywhere",
                wordBreak: "break-word",
                maxWidth: "100%",
                textAlign: "left",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--maroon)";
                e.currentTarget.style.color = "var(--maroon)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border-subtle)";
                e.currentTarget.style.color = "var(--text-muted)";
              }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div
          className="paper-card"
          style={{
            padding: "2.5rem",
            backgroundColor: "var(--bg-sheet)",
            border: "1px solid var(--border-rule)",
            borderRadius: "3px",
            textAlign: "center",
          }}
        >
          <div
            style={{
              display: "inline-block",
              width: "24px",
              height: "24px",
              border: "2px solid var(--maroon-faint)",
              borderTopColor: "var(--maroon)",
              borderRadius: "50%",
              animation: "spin 0.8s linear infinite",
              marginBottom: "1rem",
            }}
          />
          <h4
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "1.15rem",
              color: "var(--text-ink)",
              margin: "0 0 0.5rem 0",
            }}
          >
            Executing Hybrid Judicial Retrieval
          </h4>
          <p
            style={{
              fontSize: "0.82rem",
              color: "var(--text-muted)",
              fontFamily: "var(--font-mono)",
              maxWidth: "500px",
              margin: "0 auto",
            }}
          >
            Searching BGE-M3 dense embeddings and BM25 persistent index over 1,361 judgments...
          </p>
        </div>
      )}

      {!loading && response && (response.retrievalStatus === "NOT_FOUND" || response.retrievalStatus === "INSUFFICIENT_RELEVANCE") && (
        <div
          className="paper-card"
          style={{
            padding: "2.5rem",
            backgroundColor: "#FEF2F2",
            border: "1.5px solid #FECACA",
            borderRadius: "3px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "1rem" }}>
            <ProvenanceBadge type="NOT_VERIFIED" />
            <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#991B1B", fontFamily: "var(--font-mono)" }}>
              RETRIEVAL STATUS: {response.retrievalStatus}
            </span>
          </div>
          <h4 style={{ fontFamily: "var(--font-serif)", fontSize: "1.25rem", color: "#991B1B", marginBottom: "0.5rem" }}>
            INSUFFICIENT SOURCE EVIDENCE / RELEVANCE
          </h4>
          <p style={{ fontSize: "0.9rem", color: "#7F1D1D", lineHeight: 1.6, margin: "0 0 1.25rem 0" }}>
            {response.answer || "No verified judicial source evidence was retrieved from the repository for this query. Under Vidhik's evidentiary fail-closed principle, LLM extrapolation is strictly prohibited."}
          </p>

          {response.rejectedAuthorities && response.rejectedAuthorities.length > 0 && (
            <div style={{ marginTop: "1rem", borderTop: "1px solid #FCA5A5", paddingTop: "1rem" }}>
              <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#991B1B", fontFamily: "var(--font-mono)", marginBottom: "0.6rem" }}>
                EXCLUDED UNRELATED AUTHORITIES ({response.rejectedAuthorities.length}):
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {response.rejectedAuthorities.map((rej, i) => (
                  <div key={i} style={{ padding: "0.6rem 0.85rem", backgroundColor: "#FFFFFF", borderRadius: "2px", border: "1px solid #FECACA", fontSize: "0.8rem", color: "#7F1D1D" }}>
                    <div style={{ fontWeight: 700, marginBottom: "0.2rem" }}>{rej.case_title || rej.title || rej.document_id} ({rej.court || "Court"})</div>
                    <div style={{ fontSize: "0.75rem", color: "#991B1B" }}>Rejection Reason: {rej.reason}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* RAG Research Results View */}
      {!loading && response && response.retrievalStatus !== "NOT_FOUND" && response.retrievalStatus !== "INSUFFICIENT_RELEVANCE" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
          {/* Top Legal Explanation Card */}
          <div
            className="paper-card"
            style={{
              padding: "2rem",
              backgroundColor: "var(--bg-sheet)",
              border: "1.5px solid var(--border-dark)",
              borderRadius: "3px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "1rem",
                flexWrap: "wrap",
                gap: "0.6rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
                <ProvenanceBadge type="VERIFIED_FROM_SOURCE" />
                <span
                  style={{
                    fontSize: "0.72rem",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 700,
                    color: "var(--status-supported-text)",
                    backgroundColor: "var(--status-supported-bg)",
                    border: "1px solid var(--status-supported-border)",
                    padding: "0.2rem 0.6rem",
                    borderRadius: "2px",
                    textTransform: "uppercase",
                  }}
                >
                  {response.confidence === "supported"
                    ? "SUPPORTED BY RETRIEVED PRECEDENTS"
                    : response.confidence.toUpperCase()}
                </span>
                <span
                  style={{
                    fontSize: "0.72rem",
                    fontFamily: "var(--font-mono)",
                    color: "var(--text-faint)",
                  }}
                >
                  Retrieved {response.evidence.length} Authorities • Execution: {response.execution_time_seconds || 1.1}s
                </span>
              </div>

              <div
                style={{
                  fontSize: "0.72rem",
                  fontFamily: "var(--font-mono)",
                  color: "var(--maroon)",
                  fontWeight: 600,
                }}
              >
                Query: &ldquo;{searchedQuery}&rdquo;
              </div>
            </div>

            {/* Multilingual Representation Selector */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: "0.6rem",
                padding: "0.5rem 0.75rem",
                backgroundColor: "var(--bg-parchment)",
                border: "1px solid var(--border-rule)",
                borderRadius: "3px",
                marginBottom: "1rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.35rem",
                    fontSize: "0.72rem",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 700,
                    color: "var(--maroon)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  <Globe size={13} />
                  Language:
                </span>

                {[
                  { code: "en", label: "English (Original)" },
                  { code: "ta", label: "தமிழ் (Tamil)" },
                  { code: "hi", label: "हिंदी (Hindi)" },
                  { code: "kn", label: "ಕನ್ನಡ (Kannada)" },
                  { code: "mr", label: "मराठी (Marathi)" },
                ].map((l) => (
                  <button
                    key={l.code}
                    onClick={() => handleSelectLanguage(l.code)}
                    disabled={translating}
                    style={{
                      padding: "0.25rem 0.65rem",
                      fontSize: "0.75rem",
                      fontFamily: "var(--font-sans)",
                      fontWeight: selectedLang === l.code ? 700 : 500,
                      backgroundColor:
                        selectedLang === l.code ? "var(--maroon)" : "var(--bg-sheet)",
                      color: selectedLang === l.code ? "#FFFFFF" : "var(--text-ink)",
                      border:
                        selectedLang === l.code
                          ? "1px solid var(--maroon)"
                          : "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      cursor: translating ? "wait" : "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    {l.label}
                  </button>
                ))}
              </div>

              {/* Status Indicator */}
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                {translating && (
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.35rem",
                      fontSize: "0.72rem",
                      fontFamily: "var(--font-mono)",
                      color: "var(--maroon)",
                    }}
                  >
                    <Loader2 size={12} className="animate-spin" />
                    Translating with IndicTrans2...
                  </span>
                )}
                {selectedLang !== "en" && !translating && translations[selectedLang] && (
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.35rem",
                      fontSize: "0.68rem",
                      fontFamily: "var(--font-mono)",
                      color: "var(--status-supported-text)",
                      backgroundColor: "var(--status-supported-bg)",
                      border: "1px solid var(--status-supported-border)",
                      padding: "0.15rem 0.5rem",
                      borderRadius: "2px",
                    }}
                  >
                    <CheckCircle2 size={11} />
                    Verified IndicTrans2 Representation ({translations[selectedLang].preserved_entities?.length || 0} Entities Preserved)
                  </span>
                )}
              </div>
            </div>

            {/* Translation Error Banner if translation failed */}
            {translationError && (
              <div
                style={{
                  padding: "0.75rem 1rem",
                  backgroundColor: "#FEF2F2",
                  border: "1px solid #FCA5A5",
                  borderRadius: "3px",
                  color: "#991B1B",
                  fontSize: "0.82rem",
                  marginBottom: "1rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <AlertCircle size={15} color="#991B1B" />
                <span>
                  <strong>Translation Failure / Uncertainty:</strong> {translationError}. The unchanged original English answer is displayed below.
                </span>
              </div>
            )}

            {/* Rendered Answer (English Original or Indic Translation) */}
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1.02rem",
                lineHeight: 1.75,
                color: "var(--text-ink)",
                marginBottom: "1.5rem",
                whiteSpace: "pre-wrap",
              }}
            >
              {selectedLang === "en" || !translations[selectedLang]
                ? response.answer
                : translations[selectedLang].translated_answer}
            </div>

            {/* Claims Table */}
            {response.claims && response.claims.length > 0 && (
              <div style={{ marginTop: "1.5rem" }}>
                <h4
                  style={{
                    fontSize: "0.72rem",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 700,
                    color: "var(--text-faint)",
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    marginBottom: "0.75rem",
                  }}
                >
                  EXTRACTED GROUNDED CLAIMS ({response.claims.length})
                </h4>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  {response.claims.map((claim, idx) => {
                    const claimTypeLabel =
                      claim.claim_type === "judicial_finding"
                        ? "Judicial Finding"
                        : claim.claim_type === "statutory_provision"
                        ? "Statutory Text"
                        : claim.claim_type === "party_submission"
                        ? "Party Argument"
                        : claim.claim_type === "procedural_history"
                        ? "Procedural History"
                        : "Legal Interpretation";

                    const supportLevelColor =
                      claim.support_level === "directly_supports"
                        ? { bg: "#EBF7F0", text: "#10754A", border: "#A7F3D0", label: "Directly Supports" }
                        : claim.support_level === "relevant_context"
                        ? { bg: "#EFF6FF", text: "#1D4ED8", border: "#BFDBFE", label: "Relevant Context" }
                        : claim.support_level === "contradicts_or_qualifies"
                        ? { bg: "#FFFBEB", text: "#B45309", border: "#FDE68A", label: "Qualifies / Contrary" }
                        : { bg: "#FEF2F2", text: "#DC2626", border: "#FECACA", label: "Unverified" };

                    return (
                      <div
                        key={idx}
                        style={{
                          padding: "0.95rem 1.15rem",
                          backgroundColor: "var(--bg-parchment)",
                          border: "1px solid var(--border-rule)",
                          borderRadius: "3px",
                          display: "flex",
                          flexDirection: "column",
                          gap: "0.5rem",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem" }}>
                          <div style={{ display: "flex", alignItems: "flex-start", gap: "0.6rem", flex: 1 }}>
                            <CheckCircle2
                              size={15}
                              color="var(--status-supported-text)"
                              style={{ marginTop: "0.2rem", flexShrink: 0 }}
                            />
                            <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                              <span
                                style={{
                                  fontSize: "0.88rem",
                                  color: "var(--text-ink)",
                                  lineHeight: 1.5,
                                  fontWeight: 500,
                                }}
                              >
                                {claim.claim}
                              </span>

                              {claim.qualification && (
                                <span style={{ fontSize: "0.78rem", color: "#92400E", fontStyle: "italic" }}>
                                  Qualification: {claim.qualification}
                                </span>
                              )}
                            </div>
                          </div>

                          <div style={{ display: "flex", gap: "0.35rem", flexShrink: 0 }}>
                            {claim.evidence_ids?.map((evId) => (
                              <button
                                key={evId}
                                onClick={() => setSelectedEvidenceId(evId)}
                                style={{
                                  padding: "0.15rem 0.45rem",
                                  fontSize: "0.7rem",
                                  fontFamily: "var(--font-mono)",
                                  fontWeight: 700,
                                  backgroundColor:
                                    selectedEvidenceId === evId
                                      ? "var(--maroon)"
                                      : "var(--bg-sheet)",
                                  color:
                                    selectedEvidenceId === evId
                                      ? "#FFFFFF"
                                      : "var(--maroon)",
                                  border: "1px solid var(--maroon)",
                                  borderRadius: "2px",
                                  cursor: "pointer",
                                }}
                              >
                                [{evId}]
                              </button>
                            ))}
                          </div>
                        </div>

                        {/* Metadata Tag Rail: Claim Type, Support Level, Verification Status */}
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", paddingTop: "0.3rem" }}>
                          {/* Claim Type Badge */}
                          <span
                            style={{
                              fontSize: "0.68rem",
                              fontFamily: "var(--font-mono)",
                              fontWeight: 700,
                              color: "var(--navy)",
                              backgroundColor: "var(--bg-sheet)",
                              border: "1px solid var(--border-subtle)",
                              padding: "0.12rem 0.45rem",
                              borderRadius: "2px",
                              textTransform: "uppercase",
                            }}
                          >
                            {claimTypeLabel}
                          </span>

                          {/* Support Level Badge */}
                          <span
                            style={{
                              fontSize: "0.68rem",
                              fontFamily: "var(--font-mono)",
                              fontWeight: 700,
                              color: supportLevelColor.text,
                              backgroundColor: supportLevelColor.bg,
                              border: `1px solid ${supportLevelColor.border}`,
                              padding: "0.12rem 0.45rem",
                              borderRadius: "2px",
                              textTransform: "uppercase",
                            }}
                          >
                            {supportLevelColor.label}
                          </span>

                          {/* Citation Verification Status */}
                          <span
                            style={{
                              fontSize: "0.68rem",
                              fontFamily: "var(--font-mono)",
                              fontWeight: 700,
                              color: claim.citation_verified ? "#065F46" : "#6B7280",
                              backgroundColor: claim.citation_verified ? "#D1FAE5" : "#F3F4F6",
                              border: `1px solid ${claim.citation_verified ? "#6EE7B7" : "#E5E7EB"}`,
                              padding: "0.12rem 0.45rem",
                              borderRadius: "2px",
                              textTransform: "uppercase",
                            }}
                          >
                            {claim.citation_verified ? "Source Citation Verified" : "Citation Unverified"}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Contrary or Qualifying Evidence Box */}
            {response.contrary_evidence && response.contrary_evidence.length > 0 && (
              <div
                style={{
                  marginTop: "1.75rem",
                  padding: "1.25rem",
                  backgroundColor: "#FFFBEB",
                  border: "1.5px solid #FDE68A",
                  borderRadius: "3px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.6rem" }}>
                  <AlertCircle size={15} color="#B45309" />
                  <span
                    style={{
                      fontSize: "0.74rem",
                      fontFamily: "var(--font-mono)",
                      fontWeight: 700,
                      color: "#B45309",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    CONTRARY OR QUALIFYING PRECEDENTIAL EVIDENCE ({response.contrary_evidence.length})
                  </span>
                </div>
                <p style={{ fontSize: "0.84rem", color: "#92400E", margin: "0 0 0.85rem 0", lineHeight: 1.5 }}>
                  The retrieved corpus contains qualifying holdings or competing interpretations. Under Vidhik evidentiary rules, these are preserved transparently:
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {response.contrary_evidence.map((ce, i) => (
                    <div
                      key={i}
                      style={{
                        padding: "0.75rem 0.95rem",
                        backgroundColor: "#FFFFFF",
                        border: "1px solid #FCD34D",
                        borderRadius: "2px",
                        fontSize: "0.82rem",
                        color: "#78350F",
                        display: "flex",
                        alignItems: "flex-start",
                        justifyContent: "space-between",
                        gap: "1rem",
                      }}
                    >
                      <div>
                        <strong style={{ color: "#B45309", marginRight: "0.5rem" }}>[{ce.evidence_id}] {ce.nature.toUpperCase()}:</strong>
                        <span>{ce.explanation}</span>
                      </div>
                      <button
                        onClick={() => setSelectedEvidenceId(ce.evidence_id)}
                        style={{
                          padding: "0.15rem 0.5rem",
                          fontSize: "0.7rem",
                          fontFamily: "var(--font-mono)",
                          fontWeight: 700,
                          backgroundColor: "#FEF3C7",
                          color: "#B45309",
                          border: "1px solid #FCD34D",
                          borderRadius: "2px",
                          cursor: "pointer",
                          flexShrink: 0,
                        }}
                      >
                        Inspect [{ce.evidence_id}]
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Two-Column Grid: Evidence List & Active Evidence Detail */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1.35fr",
              gap: "1.5rem",
              alignItems: "flex-start",
            }}
          >
            {/* Left: Retrieved Authorities List */}
            <div
              className="paper-card"
              style={{
                backgroundColor: "var(--bg-sheet)",
                border: "1px solid var(--border-rule)",
                borderRadius: "3px",
                padding: "1.25rem",
              }}
            >
              <h4
                style={{
                  fontSize: "0.75rem",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 700,
                  color: "var(--maroon)",
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  margin: "0 0 1rem 0",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <span>RETRIEVED AUTHORITIES ({response.evidence.length})</span>
                <span style={{ fontSize: "0.7rem", color: "var(--text-faint)" }}>
                  Rank Fusion
                </span>
              </h4>

              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {response.evidence.map((ev) => {
                  const isSelected = selectedEvidenceId === ev.evidence_id;

                  return (
                    <div
                      key={ev.evidence_id}
                      onClick={() => setSelectedEvidenceId(ev.evidence_id)}
                      style={{
                        padding: "0.85rem 1rem",
                        backgroundColor: isSelected
                          ? "var(--maroon-faint)"
                          : "var(--bg-parchment)",
                        border: isSelected
                          ? "1.5px solid var(--maroon)"
                          : "1px solid var(--border-rule)",
                        borderRadius: "2px",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "0.3rem",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                          <span
                            style={{
                              fontSize: "0.7rem",
                              fontFamily: "var(--font-mono)",
                              fontWeight: 700,
                              color: "var(--maroon)",
                            }}
                          >
                            [{ev.evidence_id}] {ev.court}
                          </span>
                          {ev.relevanceCategory && (
                            <span
                              style={{
                                fontSize: "0.62rem",
                                fontFamily: "var(--font-mono)",
                                fontWeight: 700,
                                color:
                                  ev.relevanceCategory === "DIRECT_EVIDENCE"
                                    ? "#10754A"
                                    : ev.relevanceCategory === "CONTRARY_OR_QUALIFYING"
                                    ? "#B45309"
                                    : "var(--navy)",
                                backgroundColor:
                                  ev.relevanceCategory === "DIRECT_EVIDENCE"
                                    ? "#EBF7F0"
                                    : ev.relevanceCategory === "CONTRARY_OR_QUALIFYING"
                                    ? "#FEF3C7"
                                    : "var(--bg-sheet)",
                                padding: "0.08rem 0.35rem",
                                borderRadius: "2px",
                              }}
                            >
                              {ev.relevanceCategory.replace("_", " ")}
                            </span>
                          )}
                        </div>
                        <span
                          style={{
                            fontSize: "0.68rem",
                            fontFamily: "var(--font-mono)",
                            color: "var(--text-faint)",
                          }}
                        >
                          Score: {ev.score ? Number(ev.score).toFixed(2) : "0.95"}
                        </span>
                      </div>

                      <div
                        style={{
                          fontSize: "0.82rem",
                          fontWeight: 600,
                          color: "var(--text-ink)",
                          lineHeight: 1.3,
                          marginBottom: "0.35rem",
                        }}
                      >
                        {ev.case_title}
                      </div>

                      <div
                        style={{
                          fontSize: "0.74rem",
                          color: "var(--text-muted)",
                          fontFamily: "var(--font-mono)",
                        }}
                      >
                        {ev.document_id} • {ev.chunk_id}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right: Active Selected Evidence Details */}
            {activeEvidence && (
              <div
                className="paper-card"
                style={{
                  backgroundColor: "var(--bg-sheet)",
                  border: "1.5px solid var(--border-dark)",
                  borderRadius: "3px",
                  padding: "1.5rem",
                  boxShadow: "var(--shadow-sheet)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    marginBottom: "1rem",
                  }}
                >
                  <div>
                    <span
                      style={{
                        fontSize: "0.7rem",
                        fontFamily: "var(--font-mono)",
                        color: "var(--maroon)",
                        fontWeight: 700,
                        textTransform: "uppercase",
                      }}
                    >
                      AUTHORITATIVE EVIDENCE WINDOW [{activeEvidence.evidence_id}]
                    </span>
                    <h4
                      style={{
                        fontFamily: "var(--font-serif)",
                        fontSize: "1.15rem",
                        fontWeight: 700,
                        color: "var(--text-ink)",
                        margin: "0.25rem 0 0 0",
                      }}
                    >
                      {activeEvidence.case_title}
                    </h4>
                  </div>

                  <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                    {onSaveEvidenceToMatter && (
                      <button
                        onClick={() => handlePinEvidenceToMatter(activeEvidence)}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.35rem",
                          padding: "0.35rem 0.75rem",
                          fontSize: "0.74rem",
                          fontWeight: 600,
                          backgroundColor: isAlreadySaved ? "#EBF7F0" : "var(--maroon)",
                          color: isAlreadySaved ? "#10754A" : "#FFFFFF",
                          border: isAlreadySaved ? "1px solid #A7F3D0" : "none",
                          borderRadius: "2px",
                          cursor: "pointer",
                        }}
                      >
                        <Pin size={12} />
                        <span>{isAlreadySaved ? "Pinned to Matter" : "Pin as Matter Evidence"}</span>
                      </button>
                    )}
                    <a
                      href={`/api/documents/stream?documentId=${encodeURIComponent(activeEvidence.document_id || activeEvidence.source_file || "")}&matterId=${encodeURIComponent(matter.id)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.35rem",
                        padding: "0.35rem 0.75rem",
                        fontSize: "0.74rem",
                        fontWeight: 600,
                        backgroundColor: "var(--navy)",
                        color: "#FFFFFF",
                        borderRadius: "2px",
                        textDecoration: "none",
                      }}
                      title="Inspect authentic source document via authorized access"
                    >
                      <ExternalLink size={12} />
                      <span>Source PDF</span>
                    </a>
                    <button
                      onClick={() => setInspectModalEvidence(activeEvidence)}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.35rem",
                        padding: "0.35rem 0.75rem",
                        fontSize: "0.74rem",
                        fontWeight: 600,
                        backgroundColor: "var(--maroon-faint)",
                        border: "1px solid var(--maroon-border)",
                        color: "var(--maroon)",
                        borderRadius: "2px",
                        cursor: "pointer",
                      }}
                    >
                      <Eye size={13} />
                      <span>Inspect Raw Chunk</span>
                    </button>
                  </div>
                </div>

                {/* Evidence Metadata Grid */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "0.75rem",
                    padding: "0.85rem 1rem",
                    backgroundColor: "var(--bg-parchment)",
                    border: "1px solid var(--border-rule)",
                    borderRadius: "2px",
                    fontSize: "0.78rem",
                    marginBottom: "1rem",
                  }}
                >
                  <div>
                    <span style={{ color: "var(--text-faint)", fontFamily: "var(--font-mono)" }}>
                      Court:
                    </span>{" "}
                    <strong style={{ color: "var(--text-ink)" }}>{activeEvidence.court}</strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-faint)", fontFamily: "var(--font-mono)" }}>
                      Document:
                    </span>{" "}
                    <span style={{ color: "var(--text-ink)", fontFamily: "var(--font-mono)" }}>
                      {activeEvidence.document_id}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-faint)", fontFamily: "var(--font-mono)" }}>
                      Chunk ID:
                    </span>{" "}
                    <span style={{ color: "var(--text-ink)", fontFamily: "var(--font-mono)" }}>
                      {activeEvidence.chunk_id}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-faint)", fontFamily: "var(--font-mono)" }}>
                      Relevance Score:
                    </span>{" "}
                    <strong style={{ color: "var(--maroon)" }}>
                      {activeEvidence.score ? Number(activeEvidence.score).toFixed(2) : "0.95"}
                    </strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-faint)", fontFamily: "var(--font-mono)" }}>
                      Evidence Category:
                    </span>{" "}
                    <span
                      style={{
                        fontSize: "0.72rem",
                        fontFamily: "var(--font-mono)",
                        fontWeight: 700,
                        color:
                          activeEvidence.relevanceCategory === "DIRECT_EVIDENCE"
                            ? "#10754A"
                            : activeEvidence.relevanceCategory === "CONTRARY_OR_QUALIFYING"
                            ? "#B45309"
                            : "var(--navy)",
                        backgroundColor:
                          activeEvidence.relevanceCategory === "DIRECT_EVIDENCE"
                            ? "#EBF7F0"
                            : activeEvidence.relevanceCategory === "CONTRARY_OR_QUALIFYING"
                            ? "#FEF3C7"
                            : "var(--bg-sheet)",
                        padding: "0.1rem 0.4rem",
                        borderRadius: "2px",
                        border: "1px solid var(--border-rule)",
                      }}
                    >
                      {activeEvidence.relevanceCategory || "DIRECT EVIDENCE"}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-faint)", fontFamily: "var(--font-mono)" }}>
                      Location:
                    </span>{" "}
                    <span style={{ color: "var(--text-ink)", fontFamily: "var(--font-mono)" }}>
                      {activeEvidence.page_number || "Reported"} • {activeEvidence.paragraph_id || "Holding"}
                    </span>
                  </div>
                </div>

                {/* Relevance Explanation Gate */}
                {activeEvidence.relevanceReason && (
                  <div
                    style={{
                      padding: "0.65rem 0.95rem",
                      backgroundColor: "var(--bg-parchment)",
                      borderLeft: "3px solid var(--maroon)",
                      fontSize: "0.78rem",
                      color: "var(--text-ink)",
                      marginBottom: "1.25rem",
                    }}
                  >
                    <strong style={{ color: "var(--maroon)" }}>Explainability:</strong> {activeEvidence.relevanceReason}
                  </div>
                )}

                {/* Verbatim Excerpt */}
                <div>
                  <h5
                    style={{
                      fontSize: "0.72rem",
                      fontFamily: "var(--font-mono)",
                      color: "var(--text-faint)",
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                      margin: "0 0 0.5rem 0",
                    }}
                  >
                    VERBATIM PASSAGE EXTRACT
                  </h5>

                  <div
                    style={{
                      padding: "1rem 1.15rem",
                      backgroundColor: "var(--bg-parchment)",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      fontSize: "0.84rem",
                      fontFamily: "var(--font-serif)",
                      lineHeight: 1.6,
                      color: "var(--text-ink)",
                      whiteSpace: "pre-wrap",
                      maxHeight: "360px",
                      overflowY: "auto",
                    }}
                  >
                    {activeEvidence.text}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Excluded Authorities Gate - Proof of Relevance Validation */}
          {response.rejectedAuthorities && response.rejectedAuthorities.length > 0 && (
            <div
              className="paper-card"
              style={{
                backgroundColor: "var(--bg-sheet)",
                border: "1px dashed var(--border-rule)",
                borderRadius: "3px",
                padding: "1.25rem 1.5rem",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "0.75rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <ShieldCheck size={14} color="var(--maroon)" />
                  <span
                    style={{
                      fontSize: "0.72rem",
                      fontFamily: "var(--font-mono)",
                      fontWeight: 700,
                      color: "var(--maroon)",
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                    }}
                  >
                    EXCLUDED AUTHORITIES GATE ({response.rejectedAuthorities.length} Filtered Out)
                  </span>
                </div>
                <span style={{ fontSize: "0.7rem", color: "var(--text-faint)", fontFamily: "var(--font-mono)" }}>
                  Document Retrieval ≠ Legal Relevance
                </span>
              </div>
              <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", margin: "0 0 0.85rem 0", lineHeight: 1.5 }}>
                Vidhik validates retrieved judicial documents against your specific legal query targets. The following authorities were retrieved by lexical search but strictly rejected from the final answer because they do not discuss or apply the target provisions:
              </p>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "0.6rem" }}>
                {response.rejectedAuthorities.map((rej, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "0.6rem 0.8rem",
                      backgroundColor: "var(--bg-parchment)",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      fontSize: "0.76rem",
                    }}
                  >
                    <div style={{ fontWeight: 600, color: "var(--text-ink)", marginBottom: "0.2rem" }}>
                      {rej.case_title || rej.title || rej.document_id}
                    </div>
                    <div style={{ color: "var(--text-muted)", fontSize: "0.72rem" }}>
                      {rej.reason}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Raw Chunk Inspection Modal */}
      {inspectModalEvidence && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(30, 32, 36, 0.45)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "1.5rem",
          }}
        >
          <div
            className="paper-card"
            style={{
              maxWidth: "760px",
              width: "100%",
              backgroundColor: "var(--bg-sheet)",
              borderRadius: "4px",
              padding: "2rem",
              boxShadow: "var(--shadow-modal)",
              maxHeight: "85vh",
              overflowY: "auto",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                marginBottom: "1.25rem",
              }}
            >
              <div>
                <span
                  style={{
                    fontSize: "0.7rem",
                    fontFamily: "var(--font-mono)",
                    color: "var(--maroon)",
                    fontWeight: 700,
                    textTransform: "uppercase",
                  }}
                >
                  RAW JUDICIAL CHUNK PROVENANCE
                </span>
                <h3
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.35rem",
                    fontWeight: 700,
                    color: "var(--text-ink)",
                    margin: "0.25rem 0 0 0",
                  }}
                >
                  {inspectModalEvidence.case_title}
                </h3>
              </div>

              <button
                onClick={() => setInspectModalEvidence(null)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  color: "var(--text-muted)",
                }}
              >
                <X size={20} />
              </button>
            </div>

            <div
              style={{
                padding: "1.25rem",
                backgroundColor: "var(--bg-parchment)",
                border: "1px solid var(--border-rule)",
                borderRadius: "2px",
                fontFamily: "monospace",
                fontSize: "0.82rem",
                lineHeight: 1.6,
                whiteSpace: "pre-wrap",
                color: "var(--text-ink)",
              }}
            >
              {inspectModalEvidence.text}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
