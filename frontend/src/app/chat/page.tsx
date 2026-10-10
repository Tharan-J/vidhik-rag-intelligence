"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Logo } from "@/components/shared/Logo";
import {
  Send,
  RotateCcw,
  Sparkles,
  Search,
  BookOpen,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  ShieldCheck,
  Languages,
  CheckCircle2,
  Info,
  Scale,
  Briefcase,
  Copy,
  Check,
  Gavel,
  BookMarked,
  FileText,
  CornerDownRight,
  HelpCircle,
  Compass,
} from "lucide-react";

interface EvidenceItem {
  evidence_id: string;
  document_id: string;
  court: string;
  case_title: string;
  score: number;
  text: string;
  relevantExcerpt: string;
  is_source_verified: boolean;
  verification_status: string;
}

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  originalEnglishText?: string;
  showingOriginalEnglish?: boolean;
  researchMode: boolean;
  targetLanguage: string;
  evidence?: EvidenceItem[];
  claims?: any[];
  contrary_evidence?: any[];
  grounded?: boolean;
  confidence?: string;
  limitations?: string;
  retrievalStatus?: string;
  translationWarning?: string;
  timestamp: string;
}

const SUPPORTED_LANGUAGES = [
  { code: "en", label: "English", native: "English", hint: "Authoritative Original" },
  { code: "ta", label: "Tamil", native: "தமிழ்", hint: "IndicTrans2 Powered" },
  { code: "hi", label: "Hindi", native: "हिन्दी", hint: "IndicTrans2 Powered" },
  { code: "kn", label: "Kannada", native: "ಕನ್ನಡ", hint: "IndicTrans2 Powered" },
  { code: "mr", label: "Marathi", native: "मराठी", hint: "IndicTrans2 Powered" },
];

const DOMAIN_CARDS = [
  {
    category: "CONSTITUTIONAL LAW",
    icon: Scale,
    title: "Basic Structure & Fundamental Rights",
    description: "Explore Article 21 personal liberty, privacy jurisprudence, and judicial review doctrines.",
    sampleQuery: "Explain the doctrine of Basic Structure under Kesavananda Bharati.",
    badge: "Articles 14, 19, 21",
  },
  {
    category: "CRIMINAL PROCEDURE",
    icon: Gavel,
    title: "Anticipatory Bail & Criminal Defense",
    description: "Procedures for pre-arrest bail under Section 438 CrPC / Section 482 BNSS 2023.",
    sampleQuery: "What is the procedure for anticipatory bail under BNSS / CrPC?",
    badge: "Section 438 / 482",
  },
  {
    category: "CIVIL & PROPERTY DISPUTES",
    icon: BookMarked,
    title: "Plantation & Devaswom Land Rights",
    description: "Appellate rulings on estate ownership, boundary demarcation, and trust administration.",
    sampleQuery: "Do you know anything about the Hill Plantation case (Emoor Bhagavathy Devaswom vs M/S Hill Top Plantations)?",
    badge: "2026:KER:2989 Precedent",
  },
  {
    category: "FAMILY & MATRIMONIAL",
    icon: FileText,
    title: "Statutory Grounds for Matrimonial Relief",
    description: "Grounds for judicial separation and dissolution under Section 13 Hindu Marriage Act.",
    sampleQuery: "What are the grounds for decree of divorce under Hindu Marriage Act Section 13?",
    badge: "Section 13 HMA",
  },
];

const QUICK_FOLLOW_UPS = [
  "What are the statutory exceptions?",
  "Explain in simpler citizen terms",
  "Are there landmark Supreme Court precedents?",
  "What is the limitation period for filing?",
];

export default function PublicChatbotPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [researchMode, setResearchMode] = useState(false);
  const [targetLanguage, setTargetLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [expandedEvidenceIds, setExpandedEvidenceIds] = useState<Record<string, boolean>>({});
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const toggleEvidenceExpand = (key: string) => {
    setExpandedEvidenceIds((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleClearConversation = () => {
    setMessages([]);
    setError(null);
    if (textareaRef.current) textareaRef.current.focus();
  };

  const handleCopyText = (msgId: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMessageId(msgId);
    setTimeout(() => {
      setCopiedMessageId((prev) => (prev === msgId ? null : prev));
    }, 2000);
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputText).trim();
    if (!query || loading) return;

    setError(null);
    setInputText("");

    const userMessage: Message = {
      id: `USR-${Date.now()}`,
      sender: "user",
      text: query,
      researchMode,
      targetLanguage,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setLoadingStep(
      researchMode
        ? "Retrieving verified judicial precedents from Qdrant Cloud..."
        : "Formulating legal overview with local Qwen legal intelligence..."
    );

    try {
      const historyContext = messages.slice(-4).map((m) => ({
        sender: m.sender,
        text: m.text,
      }));

      const res = await fetch("/api/public/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          researchMode,
          targetLanguage,
          conversationHistory: historyContext,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Service returned status ${res.status}`);
      }

      const data = await res.json();

      const assistantMessage: Message = {
        id: `AST-${Date.now()}`,
        sender: "assistant",
        text: data.answer,
        originalEnglishText: data.originalEnglishAnswer,
        showingOriginalEnglish: false,
        researchMode: Boolean(data.researchMode),
        targetLanguage: data.targetLanguage || "en",
        evidence: data.evidence || [],
        claims: data.claims || [],
        contrary_evidence: data.contrary_evidence || [],
        grounded: Boolean(data.grounded),
        confidence: data.confidence,
        limitations: data.limitations,
        retrievalStatus: data.retrievalStatus,
        translationWarning: data.translationWarning,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setError(err.message || "Failed to receive response from legal service.");
    } finally {
      setLoading(false);
      setLoadingStep("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleLanguageView = (msgId: string) => {
    setMessages((prev) =>
      prev.map((m) => {
        if (m.id === msgId) {
          return {
            ...m,
            showingOriginalEnglish: !m.showingOriginalEnglish,
          };
        }
        return m;
      })
    );
  };

  // Helper function to render text with formatted paragraphs and legal highlighting
  const renderFormattedLegalText = (content: string) => {
    if (!content) return null;
    const paragraphs = content.split(/\n\n+/);

    return (
      <div className="legal-prose" style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
        {paragraphs.map((p, i) => {
          const trimmed = p.trim();
          if (!trimmed) return null;

          // Check if bullet point or numbered item
          if (/^(\d+\.|\*|-|•)\s+/.test(trimmed)) {
            const lines = trimmed.split("\n");
            return (
              <ul key={i} style={{ paddingLeft: "1.4rem", margin: 0, display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                {lines.map((line, liIdx) => (
                  <li key={liIdx} style={{ lineHeight: 1.65 }}>
                    {line.replace(/^(\d+\.|\*|-|•)\s+/, "")}
                  </li>
                ))}
              </ul>
            );
          }

          // Regular paragraph with generous editorial line-height
          return (
            <p key={i} style={{ margin: 0, lineHeight: 1.7, fontSize: "0.95rem" }}>
              {trimmed}
            </p>
          );
        })}
      </div>
    );
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        backgroundColor: "var(--bg-parchment)",
        color: "var(--text-ink)",
        position: "relative",
      }}
    >
      {/* =====================================================================
          1. INSTITUTIONAL TOP BAR
          ===================================================================== */}
      <header
        style={{
          height: "70px",
          backgroundColor: "rgba(255, 253, 248, 0.95)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
          borderBottom: "1px solid var(--border-rule)",
          boxShadow: "0 4px 20px rgba(30, 32, 36, 0.04), inset 0 -1px 0 rgba(194, 159, 98, 0.25)",
          padding: "0 2.25rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          position: "sticky",
          top: 0,
          zIndex: 40,
        }}
      >
        {/* Left: Brand & Insignia */}
        <div style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
          <Logo size="md" withTagline={false} />
          <div
            style={{
              height: "22px",
              width: "1px",
              backgroundColor: "rgba(194, 159, 98, 0.4)",
            }}
          />
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.28rem 0.75rem",
              background: "linear-gradient(135deg, var(--brass-faint) 0%, rgba(253, 249, 240, 0.9) 100%)",
              border: "1px solid var(--brass-light)",
              borderRadius: "4px",
              fontSize: "0.72rem",
              fontFamily: "var(--font-mono)",
              fontWeight: 700,
              color: "var(--brass)",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              boxShadow: "0 1px 3px rgba(162, 123, 63, 0.08)",
            }}
          >
            <Scale size={14} color="var(--brass)" />
            <span>PUBLIC LEGAL ASSISTANT</span>
          </div>
        </div>

        {/* Right: Language, Reset & Lawyer Portal Entry */}
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {/* Custom Styled Language Selector */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              backgroundColor: "var(--bg-sheet)",
              border: "1px solid var(--border-rule)",
              borderRadius: "20px",
              padding: "0.28rem 0.75rem",
              boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
              transition: "border-color 0.15s ease",
            }}
          >
            <Languages size={15} color="var(--maroon)" />
            <select
              value={targetLanguage}
              onChange={(e) => setTargetLanguage(e.target.value)}
              style={{
                border: "none",
                outline: "none",
                background: "transparent",
                fontSize: "0.82rem",
                fontWeight: 600,
                fontFamily: "var(--font-sans)",
                color: "var(--text-ink)",
                cursor: "pointer",
                paddingRight: "0.25rem",
              }}
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.native} &bull; {lang.label}
                </option>
              ))}
            </select>
          </div>

          {/* New Chat Button */}
          {messages.length > 0 && (
            <button
              onClick={handleClearConversation}
              title="Start a new legal session"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.4rem",
                padding: "0.45rem 0.85rem",
                fontSize: "0.8rem",
                fontWeight: 600,
                backgroundColor: "var(--bg-sheet)",
                border: "1px solid var(--border-rule)",
                borderRadius: "20px",
                color: "var(--text-muted)",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--maroon)";
                e.currentTarget.style.color = "var(--maroon)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border-rule)";
                e.currentTarget.style.color = "var(--text-muted)";
              }}
            >
              <RotateCcw size={13} />
              <span>Reset</span>
            </button>
          )}

          {/* Lawyer Workspace Link */}
          <Link
            href="/login"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              fontSize: "0.82rem",
              fontWeight: 700,
              color: "#FFF9EE",
              padding: "0.48rem 1.1rem",
              borderRadius: "4px",
              background: "linear-gradient(135deg, #7A1C28 0%, #541620 100%)",
              border: "1px solid rgba(194, 159, 98, 0.4)",
              boxShadow: "0 2px 6px rgba(110, 31, 42, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.2)",
              textDecoration: "none",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-1px)";
              e.currentTarget.style.boxShadow = "0 4px 12px rgba(110, 31, 42, 0.35)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateY(0px)";
              e.currentTarget.style.boxShadow = "0 2px 6px rgba(110, 31, 42, 0.25)";
            }}
          >
            <Briefcase size={14} />
            <span>Lawyer Workspace</span>
          </Link>
        </div>
      </header>

      {/* =====================================================================
          2. RESEARCH INTELLIGENCE CONTROL BAR
          ===================================================================== */}
      <div
        style={{
          backgroundColor: researchMode ? "rgba(110, 31, 42, 0.05)" : "var(--bg-surface)",
          borderBottom: researchMode ? "1px solid var(--maroon-border)" : "1px solid var(--border-rule)",
          padding: "0.85rem 2rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "1rem",
          transition: "all 0.25s ease",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "1.25rem", flexWrap: "wrap" }}>
          {/* Research Toggle Controller */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              backgroundColor: "var(--bg-sheet)",
              padding: "0.35rem 0.85rem",
              borderRadius: "20px",
              border: `1.5px solid ${researchMode ? "var(--maroon)" : "var(--border-rule)"}`,
              boxShadow: researchMode ? "0 2px 8px rgba(110, 31, 42, 0.1)" : "none",
              transition: "all 0.2s ease",
            }}
          >
            <span
              style={{
                fontSize: "0.78rem",
                fontFamily: "var(--font-mono)",
                fontWeight: 700,
                color: researchMode ? "var(--maroon)" : "var(--text-muted)",
                letterSpacing: "0.06em",
              }}
            >
              RESEARCH MODE:
            </span>

            <button
              onClick={() => setResearchMode(!researchMode)}
              style={{
                position: "relative",
                width: "48px",
                height: "24px",
                borderRadius: "12px",
                backgroundColor: researchMode ? "var(--maroon)" : "#D5CEC2",
                border: "none",
                cursor: "pointer",
                transition: "background-color 0.25s ease",
                padding: "2px",
                display: "flex",
                alignItems: "center",
              }}
              title={
                researchMode
                  ? "Research ON: Grounded in Supreme Court & High Court precedents via Qdrant Cloud"
                  : "Research OFF: Fast conversational explanation via local Qwen"
              }
            >
              <div
                style={{
                  width: "20px",
                  height: "20px",
                  borderRadius: "50%",
                  backgroundColor: "#FFFFFF",
                  transform: researchMode ? "translateX(24px)" : "translateX(2px)",
                  transition: "transform 0.25s cubic-bezier(0.18, 0.89, 0.32, 1.28)",
                  boxShadow: "0 2px 4px rgba(0,0,0,0.25)",
                }}
              />
            </button>

            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 700,
                fontFamily: "var(--font-mono)",
                color: researchMode ? "var(--maroon)" : "var(--text-muted)",
              }}
            >
              {researchMode ? "ON" : "OFF"}
            </span>
          </div>

          {/* Mode Explanation & Status Chip */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            {researchMode ? (
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.45rem",
                  fontSize: "0.82rem",
                  color: "var(--maroon)",
                  fontWeight: 600,
                }}
              >
                <span
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: "var(--maroon)",
                    boxShadow: "0 0 0 3px rgba(110, 31, 42, 0.2)",
                    animation: "pulseDot 1.8s infinite",
                  }}
                />
                <Search size={14} color="var(--maroon)" />
                <span>Judicial Precedent Retrieval Active &bull; Verified against Qdrant Cloud Corpus</span>
              </div>
            ) : (
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.45rem",
                  fontSize: "0.82rem",
                  color: "var(--text-muted)",
                  fontWeight: 500,
                }}
              >
                <Sparkles size={14} color="var(--brass)" />
                <span>Conversational Legal Overview &bull; General Explanations via Local Qwen 4B</span>
              </div>
            )}
          </div>
        </div>

        {/* Legal Information Safeguard Notice */}
        <div
          style={{
            fontSize: "0.74rem",
            color: "var(--text-muted)",
            fontFamily: "var(--font-mono)",
            display: "inline-flex",
            alignItems: "center",
            gap: "0.35rem",
          }}
        >
          <ShieldCheck size={14} color="var(--brass)" />
          <span>NON-ADVISORY &bull; CITIZEN LEGAL EDUCATION</span>
        </div>
      </div>

      {/* =====================================================================
          3. MAIN CONVERSATION AREA
          ===================================================================== */}
      <main
        style={{
          flex: 1,
          maxWidth: "1020px",
          width: "100%",
          margin: "0 auto",
          padding: "2rem 1.5rem",
          display: "flex",
          flexDirection: "column",
          gap: "1.75rem",
        }}
      >
        {/* Welcome Chamber View (When No Messages) */}
        {messages.length === 0 && (
          <div
            style={{
              backgroundColor: "var(--bg-sheet)",
              border: "1.5px solid var(--border-rule)",
              borderRadius: "6px",
              padding: "3rem 2.5rem",
              boxShadow: "var(--shadow-sheet)",
              position: "relative",
              overflow: "hidden",
            }}
          >
            {/* Archival Decorative Accent Rule */}
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                height: "4px",
                background: "linear-gradient(90deg, var(--maroon) 0%, var(--brass) 50%, var(--navy) 100%)",
              }}
            />

            {/* Emblem / Scale Icon Badge */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                marginBottom: "1.25rem",
              }}
            >
              <div
                style={{
                  width: "44px",
                  height: "44px",
                  borderRadius: "8px",
                  backgroundColor: "var(--maroon-faint)",
                  border: "1px solid var(--maroon-border)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--maroon)",
                }}
              >
                <Scale size={24} />
              </div>
              <div>
                <span
                  style={{
                    fontSize: "0.74rem",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 700,
                    color: "var(--brass)",
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                  }}
                >
                  INSTITUTIONAL JURISPRUDENCE SYSTEM
                </span>
                <h1
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "2rem",
                    fontWeight: 700,
                    color: "var(--text-ink)",
                    lineHeight: 1.2,
                    margin: "0.15rem 0 0 0",
                  }}
                >
                  Public Multilingual Legal Assistant
                </h1>
              </div>
            </div>

            <p
              style={{
                fontSize: "1rem",
                color: "var(--text-muted)",
                lineHeight: 1.65,
                maxWidth: "760px",
                marginBottom: "1.75rem",
              }}
            >
              Access accurate, multilingual explanations of Indian statutes, fundamental rights, and judicial rulings in{" "}
              <strong style={{ color: "var(--text-ink)" }}>English, Tamil, Hindi, Kannada, and Marathi</strong>.
              All inquiries are processed locally with Qwen legal intelligence and IndicTrans2 entity protection.
            </p>

            {/* Statutory Disclaimer Box */}
            <div
              style={{
                padding: "1rem 1.25rem",
                backgroundColor: "var(--bg-parchment)",
                borderLeft: "4px solid var(--maroon)",
                borderRadius: "3px",
                marginBottom: "2.25rem",
                boxShadow: "inset 0 1px 3px rgba(0,0,0,0.02)",
              }}
            >
              <div
                style={{
                  fontSize: "0.82rem",
                  fontWeight: 700,
                  color: "var(--maroon)",
                  marginBottom: "0.3rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.4rem",
                }}
              >
                <ShieldCheck size={16} />
                <span>Statutory Notice & Scope Limitation</span>
              </div>
              <p
                style={{
                  fontSize: "0.84rem",
                  color: "var(--text-ink)",
                  lineHeight: 1.5,
                  margin: 0,
                }}
              >
                This assistant provides informational legal guidance only and is not a substitute for counsel from a qualified
                Advocate. In Research Mode, statements strictly require backing from judicial precedents in the repository;
                when precedents are unavailable, the model explicitly abstains.
              </p>
            </div>

            {/* Explore Common Legal Domains Cards */}
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "1rem",
                }}
              >
                <div
                  style={{
                    fontSize: "0.78rem",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 700,
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.4rem",
                  }}
                >
                  <Compass size={14} color="var(--brass)" />
                  <span>SELECT A LEGAL INQUIRY OR TOPIC:</span>
                </div>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
                  gap: "1rem",
                }}
              >
                {DOMAIN_CARDS.map((card, idx) => {
                  const Icon = card.icon;
                  return (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(card.sampleQuery)}
                      style={{
                        textAlign: "left",
                        padding: "1.25rem",
                        backgroundColor: "var(--bg-surface)",
                        border: "1px solid var(--border-rule)",
                        borderRadius: "5px",
                        cursor: "pointer",
                        transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
                        display: "flex",
                        flexDirection: "column",
                        justifyContent: "space-between",
                        boxShadow: "0 1px 3px rgba(0,0,0,0.02)",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = "var(--maroon)";
                        e.currentTarget.style.backgroundColor = "var(--bg-sheet)";
                        e.currentTarget.style.transform = "translateY(-2px)";
                        e.currentTarget.style.boxShadow = "var(--shadow-sheet)";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = "var(--border-rule)";
                        e.currentTarget.style.backgroundColor = "var(--bg-surface)";
                        e.currentTarget.style.transform = "translateY(0px)";
                        e.currentTarget.style.boxShadow = "0 1px 3px rgba(0,0,0,0.02)";
                      }}
                    >
                      <div>
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            marginBottom: "0.6rem",
                          }}
                        >
                          <span
                            style={{
                              fontSize: "0.68rem",
                              fontFamily: "var(--font-mono)",
                              fontWeight: 700,
                              color: "var(--brass)",
                              letterSpacing: "0.06em",
                            }}
                          >
                            {card.category}
                          </span>
                          <span
                            style={{
                              fontSize: "0.7rem",
                              fontFamily: "var(--font-mono)",
                              fontWeight: 600,
                              color: "var(--maroon)",
                              backgroundColor: "var(--maroon-faint)",
                              padding: "0.15rem 0.45rem",
                              borderRadius: "2px",
                            }}
                          >
                            {card.badge}
                          </span>
                        </div>
                        <h4
                          style={{
                            fontSize: "0.98rem",
                            fontWeight: 700,
                            color: "var(--text-ink)",
                            marginBottom: "0.35rem",
                            fontFamily: "var(--font-serif)",
                          }}
                        >
                          {card.title}
                        </h4>
                        <p
                          style={{
                            fontSize: "0.82rem",
                            color: "var(--text-muted)",
                            lineHeight: 1.45,
                            margin: 0,
                          }}
                        >
                          {card.description}
                        </p>
                      </div>

                      <div
                        style={{
                          marginTop: "0.85rem",
                          paddingTop: "0.65rem",
                          borderTop: "1px dashed var(--border-subtle)",
                          fontSize: "0.78rem",
                          color: "var(--maroon)",
                          fontWeight: 600,
                          display: "flex",
                          alignItems: "center",
                          gap: "0.35rem",
                        }}
                      >
                        <CornerDownRight size={13} />
                        <span>Query: &ldquo;{card.sampleQuery}&rdquo;</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Message Stream */}
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: msg.sender === "user" ? "flex-end" : "flex-start",
              width: "100%",
            }}
          >
            {/* Conversation Row with Avatar */}
            <div
              style={{
                display: "flex",
                gap: "1rem",
                maxWidth: msg.sender === "user" ? "82%" : "100%",
                flexDirection: msg.sender === "user" ? "row-reverse" : "row",
              }}
            >
              {/* Avatar Insignia */}
              <div
                style={{
                  width: "38px",
                  height: "38px",
                  borderRadius: "50%",
                  backgroundColor: msg.sender === "user" ? "var(--navy)" : "var(--maroon)",
                  color: "#FFFFFF",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  boxShadow: "0 2px 6px rgba(0,0,0,0.12)",
                  marginTop: "0.25rem",
                }}
              >
                {msg.sender === "user" ? (
                  <span style={{ fontSize: "0.82rem", fontWeight: 700, fontFamily: "var(--font-mono)" }}>YOU</span>
                ) : (
                  <Scale size={20} color="#FAF4EB" />
                )}
              </div>

              {/* Bubble Body */}
              <div
                style={{
                  backgroundColor: msg.sender === "user" ? "var(--bg-sheet)" : "var(--bg-sheet)",
                  border: msg.sender === "user" ? "1.5px solid var(--border-rule)" : "1.5px solid var(--border-rule)",
                  borderRadius: msg.sender === "user" ? "8px 2px 8px 8px" : "2px 8px 8px 8px",
                  padding: "1.4rem 1.6rem",
                  boxShadow: "var(--shadow-sheet)",
                  boxSizing: "border-box",
                  overflowWrap: "anywhere",
                  wordBreak: "break-word",
                  position: "relative",
                  width: "100%",
                }}
              >
                {/* Assistant Metadata Header */}
                {msg.sender === "assistant" && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      flexWrap: "wrap",
                      gap: "0.6rem",
                      marginBottom: "1rem",
                      paddingBottom: "0.75rem",
                      borderBottom: "1px solid var(--border-subtle)",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
                      {msg.researchMode ? (
                        <span
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "0.35rem",
                            fontSize: "0.72rem",
                            fontFamily: "var(--font-mono)",
                            fontWeight: 700,
                            padding: "0.2rem 0.55rem",
                            backgroundColor: msg.grounded ? "rgba(34, 92, 48, 0.08)" : "rgba(138, 35, 46, 0.08)",
                            color: msg.grounded ? "var(--status-supported-text)" : "var(--status-insufficient-text)",
                            border: `1px solid ${msg.grounded ? "var(--status-supported-border)" : "var(--status-insufficient-border)"}`,
                            borderRadius: "3px",
                            textTransform: "uppercase",
                          }}
                        >
                          {msg.grounded ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}
                          <span>
                            {msg.grounded
                              ? `VERIFIED JUDICIAL PRECEDENT (${msg.evidence?.length || 0} AUTHORITIES)`
                              : "INSUFFICIENT EVIDENCE (ABSTENTION)"}
                          </span>
                        </span>
                      ) : (
                        <span
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "0.35rem",
                            fontSize: "0.72rem",
                            fontFamily: "var(--font-mono)",
                            fontWeight: 700,
                            padding: "0.2rem 0.55rem",
                            backgroundColor: "var(--bg-parchment)",
                            color: "var(--text-muted)",
                            border: "1px solid var(--border-rule)",
                            borderRadius: "3px",
                            textTransform: "uppercase",
                          }}
                        >
                          <Sparkles size={12} color="var(--brass)" />
                          <span>CONVERSATIONAL LEGAL OVERVIEW</span>
                        </span>
                      )}

                      {msg.targetLanguage !== "en" && (
                        <span
                          style={{
                            fontSize: "0.72rem",
                            fontFamily: "var(--font-mono)",
                            fontWeight: 600,
                            padding: "0.2rem 0.55rem",
                            backgroundColor: "var(--brass-faint)",
                            color: "var(--brass)",
                            border: "1px solid var(--brass-light)",
                            borderRadius: "3px",
                          }}
                        >
                          IndicTrans2 &bull; {msg.targetLanguage.toUpperCase()}
                        </span>
                      )}
                    </div>

                    {/* Actions: Copy & Toggle Original English */}
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      {msg.targetLanguage !== "en" && msg.originalEnglishText && (
                        <button
                          onClick={() => toggleLanguageView(msg.id)}
                          style={{
                            background: "var(--bg-surface)",
                            border: "1px solid var(--border-subtle)",
                            borderRadius: "3px",
                            padding: "0.25rem 0.55rem",
                            fontSize: "0.74rem",
                            fontFamily: "var(--font-mono)",
                            color: "var(--text-muted)",
                            cursor: "pointer",
                            transition: "all 0.15s ease",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.color = "var(--text-ink)";
                            e.currentTarget.style.borderColor = "var(--border-rule)";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.color = "var(--text-muted)";
                            e.currentTarget.style.borderColor = "var(--border-subtle)";
                          }}
                        >
                          {msg.showingOriginalEnglish ? "Show Translation" : "View English Original"}
                        </button>
                      )}

                      <button
                        onClick={() => handleCopyText(msg.id, msg.showingOriginalEnglish ? (msg.originalEnglishText || msg.text) : msg.text)}
                        title="Copy answer to clipboard"
                        style={{
                          background: "var(--bg-surface)",
                          border: "1px solid var(--border-subtle)",
                          borderRadius: "3px",
                          padding: "0.25rem 0.55rem",
                          fontSize: "0.74rem",
                          fontFamily: "var(--font-mono)",
                          color: copiedMessageId === msg.id ? "var(--status-supported-text)" : "var(--text-muted)",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.3rem",
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                        }}
                      >
                        {copiedMessageId === msg.id ? (
                          <>
                            <Check size={12} color="var(--status-supported-text)" />
                            <span>Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy size={12} />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}

                {/* Message Body Content */}
                <div
                  style={{
                    color: "var(--text-ink)",
                    fontFamily: msg.sender === "user" ? "var(--font-sans)" : "var(--font-serif)",
                    fontSize: msg.sender === "user" ? "0.95rem" : "1.02rem",
                    lineHeight: 1.7,
                  }}
                >
                  {renderFormattedLegalText(msg.showingOriginalEnglish ? (msg.originalEnglishText || msg.text) : msg.text)}
                </div>

                {/* Translation Warning Notice if IndicTrans2 fell back */}
                {msg.translationWarning && (
                  <div
                    style={{
                      marginTop: "1rem",
                      padding: "0.6rem 0.85rem",
                      backgroundColor: "rgba(180, 120, 20, 0.08)",
                      border: "1px solid rgba(180, 120, 20, 0.3)",
                      borderRadius: "3px",
                      fontSize: "0.78rem",
                      color: "#8a5800",
                    }}
                  >
                    {msg.translationWarning}
                  </div>
                )}

                {/* Expandable Evidence Passages (in Research Mode) */}
                {msg.researchMode && msg.evidence && msg.evidence.length > 0 && (
                  <div
                    style={{
                      marginTop: "1.5rem",
                      paddingTop: "1.25rem",
                      borderTop: "1px solid var(--border-rule)",
                    }}
                  >
                    <div
                      style={{
                        fontSize: "0.78rem",
                        fontFamily: "var(--font-mono)",
                        fontWeight: 700,
                        color: "var(--maroon)",
                        textTransform: "uppercase",
                        letterSpacing: "0.06em",
                        marginBottom: "0.85rem",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.45rem",
                      }}
                    >
                      <BookOpen size={15} />
                      <span>RETRIEVED JUDICIAL EVIDENCE & AUTHORITIES ({msg.evidence.length})</span>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                      {msg.evidence.map((ev) => {
                        const expandKey = `${msg.id}-${ev.evidence_id}`;
                        const isExpanded = Boolean(expandedEvidenceIds[expandKey]);

                        return (
                          <div
                            key={ev.evidence_id}
                            style={{
                              border: "1px solid var(--border-rule)",
                              borderRadius: "4px",
                              backgroundColor: "var(--bg-surface)",
                              padding: "0.85rem 1.15rem",
                              transition: "all 0.15s ease",
                            }}
                          >
                            <div
                              onClick={() => toggleEvidenceExpand(expandKey)}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                                cursor: "pointer",
                                userSelect: "none",
                              }}
                            >
                              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
                                <span
                                  style={{
                                    fontSize: "0.72rem",
                                    fontFamily: "var(--font-mono)",
                                    fontWeight: 700,
                                    backgroundColor: "var(--maroon-faint)",
                                    color: "var(--maroon)",
                                    border: "1px solid var(--maroon-border)",
                                    padding: "0.15rem 0.45rem",
                                    borderRadius: "3px",
                                  }}
                                >
                                  {ev.evidence_id}
                                </span>
                                <span
                                  style={{
                                    fontSize: "0.88rem",
                                    fontWeight: 700,
                                    fontFamily: "var(--font-serif)",
                                    color: "var(--text-ink)",
                                  }}
                                >
                                  {ev.case_title || ev.document_id}
                                </span>
                                <span
                                  style={{
                                    fontSize: "0.78rem",
                                    color: "var(--text-muted)",
                                    backgroundColor: "var(--bg-parchment)",
                                    padding: "0.1rem 0.4rem",
                                    borderRadius: "2px",
                                  }}
                                >
                                  {ev.court}
                                </span>
                              </div>

                              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                                <span
                                  style={{
                                    fontSize: "0.72rem",
                                    fontFamily: "var(--font-mono)",
                                    color: "var(--brass)",
                                    fontWeight: 600,
                                  }}
                                >
                                  Verified Point
                                </span>
                                {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                              </div>
                            </div>

                            {/* Collapsible passage content */}
                            {isExpanded && (
                              <div
                                style={{
                                  marginTop: "0.85rem",
                                  paddingTop: "0.75rem",
                                  borderTop: "1px dashed var(--border-rule)",
                                  fontSize: "0.84rem",
                                  color: "var(--text-ink)",
                                  lineHeight: 1.6,
                                }}
                              >
                                <div
                                  style={{
                                    fontSize: "0.72rem",
                                    fontFamily: "var(--font-mono)",
                                    color: "var(--text-faint)",
                                    marginBottom: "0.45rem",
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "space-between",
                                  }}
                                >
                                  <span>VERBATIM STATUTORY / JUDICIAL EXCERPT:</span>
                                  <span>Match Relevance Score: {ev.score}</span>
                                </div>
                                <blockquote
                                  style={{
                                    margin: 0,
                                    padding: "0.75rem 1rem",
                                    backgroundColor: "var(--bg-parchment)",
                                    borderLeft: "3px solid var(--maroon)",
                                    borderRadius: "0 3px 3px 0",
                                    fontStyle: "normal",
                                    color: "var(--text-ink)",
                                    fontFamily: "var(--font-serif)",
                                  }}
                                >
                                  {ev.text}
                                </blockquote>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Timestamp Under Bubble */}
            <div
              style={{
                fontSize: "0.72rem",
                color: "var(--text-faint)",
                fontFamily: "var(--font-mono)",
                marginTop: "0.35rem",
                padding: "0 3.2rem",
              }}
            >
              {msg.timestamp}
            </div>
          </div>
        ))}

        {/* Loading State Spinner */}
        {loading && (
          <div
            style={{
              padding: "1.25rem 1.75rem",
              backgroundColor: "var(--bg-sheet)",
              border: "1.5px solid var(--border-rule)",
              borderRadius: "6px",
              display: "flex",
              alignItems: "center",
              gap: "1rem",
              width: "fit-content",
              boxShadow: "var(--shadow-sheet)",
            }}
          >
            <div
              style={{
                width: "20px",
                height: "20px",
                border: "2px solid var(--border-subtle)",
                borderTopColor: "var(--maroon)",
                borderRadius: "50%",
                animation: "spin 0.8s linear infinite",
              }}
            />
            <div>
              <div
                style={{
                  fontSize: "0.86rem",
                  fontWeight: 600,
                  color: "var(--text-ink)",
                }}
              >
                Synthesizing Legal Intelligence...
              </div>
              <div
                style={{
                  fontSize: "0.75rem",
                  color: "var(--text-muted)",
                  fontFamily: "var(--font-mono)",
                }}
              >
                {loadingStep || "Consulting local inference engine..."}
              </div>
            </div>
          </div>
        )}

        {/* Error State Notice */}
        {error && (
          <div
            style={{
              padding: "1.2rem 1.5rem",
              backgroundColor: "var(--status-insufficient-bg)",
              border: "1.5px solid var(--status-insufficient-border)",
              borderRadius: "6px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "1rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <AlertCircle size={18} color="var(--status-insufficient-text)" />
              <span style={{ fontSize: "0.88rem", color: "var(--status-insufficient-text)", fontWeight: 500 }}>
                {error}
              </span>
            </div>
            <button
              onClick={() => handleSendMessage()}
              style={{
                padding: "0.4rem 0.85rem",
                backgroundColor: "#FFFFFF",
                border: "1px solid var(--status-insufficient-border)",
                borderRadius: "3px",
                fontSize: "0.8rem",
                fontWeight: 600,
                color: "var(--status-insufficient-text)",
                cursor: "pointer",
              }}
            >
              Retry Inquiry
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* =====================================================================
          4. ELEVATED FLOATING DOCKET COMPOSER
          ===================================================================== */}
      <footer
        style={{
          position: "sticky",
          bottom: 0,
          backgroundColor: "rgba(255, 253, 248, 0.94)",
          backdropFilter: "blur(14px)",
          borderTop: "1px solid var(--border-rule)",
          padding: "1.25rem 2rem 1.5rem 2rem",
          zIndex: 30,
        }}
      >
        <div style={{ maxWidth: "1020px", margin: "0 auto" }}>
          {/* Quick Follow-up Chips when conversation has active messages */}
          {messages.length > 0 && !loading && (
            <div
              style={{
                display: "flex",
                gap: "0.5rem",
                marginBottom: "0.85rem",
                overflowX: "auto",
                paddingBottom: "0.25rem",
              }}
            >
              <span
                style={{
                  fontSize: "0.72rem",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 700,
                  color: "var(--text-faint)",
                  alignSelf: "center",
                  whiteSpace: "nowrap",
                  marginRight: "0.25rem",
                }}
              >
                QUICK FOLLOW-UPS:
              </span>
              {QUICK_FOLLOW_UPS.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(q)}
                  style={{
                    whiteSpace: "nowrap",
                    padding: "0.3rem 0.75rem",
                    backgroundColor: "var(--bg-sheet)",
                    border: "1px solid var(--border-rule)",
                    borderRadius: "14px",
                    fontSize: "0.78rem",
                    color: "var(--text-muted)",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = "var(--maroon)";
                    e.currentTarget.style.color = "var(--maroon)";
                    e.currentTarget.style.backgroundColor = "var(--maroon-faint)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "var(--border-rule)";
                    e.currentTarget.style.color = "var(--text-muted)";
                    e.currentTarget.style.backgroundColor = "var(--bg-sheet)";
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Composer Card Container */}
          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              gap: "0.85rem",
              backgroundColor: "var(--bg-sheet)",
              border: "1.5px solid var(--border-rule)",
              borderRadius: "8px",
              padding: "0.85rem 1.15rem",
              boxShadow: "0 4px 16px rgba(30, 32, 36, 0.06)",
              transition: "border-color 0.2s ease",
            }}
          >
            <textarea
              ref={textareaRef}
              rows={2}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                researchMode
                  ? "Enter your legal inquiry to search Supreme Court & High Court precedents... (Press Enter to send, Shift+Enter for newline)"
                  : "Ask a legal question for general statutory explanation... (Press Enter to send, Shift+Enter for newline)"
              }
              style={{
                flex: 1,
                border: "none",
                outline: "none",
                backgroundColor: "transparent",
                color: "var(--text-ink)",
                fontSize: "0.95rem",
                lineHeight: 1.5,
                fontFamily: "var(--font-sans)",
                resize: "none",
                maxHeight: "180px",
              }}
            />

            <button
              onClick={() => handleSendMessage()}
              disabled={loading || !inputText.trim()}
              title="Submit your legal inquiry (Enter)"
              style={{
                height: "46px",
                padding: "0 1.35rem",
                borderRadius: "23px",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.55rem",
                fontSize: "0.88rem",
                fontWeight: 700,
                letterSpacing: "0.02em",
                fontFamily: "var(--font-sans)",
                cursor: inputText.trim() && !loading ? "pointer" : "not-allowed",
                transition: "all 0.22s cubic-bezier(0.16, 1, 0.3, 1)",
                background:
                  inputText.trim() && !loading
                    ? "linear-gradient(135deg, #7A1C28 0%, #541620 100%)"
                    : "var(--bg-surface)",
                color: inputText.trim() && !loading ? "#FFF9EE" : "var(--text-faint)",
                border:
                  inputText.trim() && !loading
                    ? "1px solid rgba(194, 159, 98, 0.6)"
                    : "1px solid var(--border-rule)",
                boxShadow:
                  inputText.trim() && !loading
                    ? "0 4px 14px rgba(110, 31, 42, 0.32), inset 0 1px 1px rgba(255, 255, 255, 0.35)"
                    : "none",
                flexShrink: 0,
              }}
              onMouseEnter={(e) => {
                if (inputText.trim() && !loading) {
                  e.currentTarget.style.transform = "translateY(-1.5px) scale(1.02)";
                  e.currentTarget.style.boxShadow =
                    "0 6px 18px rgba(110, 31, 42, 0.42), inset 0 1px 1px rgba(255, 255, 255, 0.45)";
                }
              }}
              onMouseLeave={(e) => {
                if (inputText.trim() && !loading) {
                  e.currentTarget.style.transform = "translateY(0px) scale(1)";
                  e.currentTarget.style.boxShadow =
                    "0 4px 14px rgba(110, 31, 42, 0.32), inset 0 1px 1px rgba(255, 255, 255, 0.35)";
                }
              }}
            >
              <span>{loading ? "Searching..." : "Inquire"}</span>
              <div
                style={{
                  width: "24px",
                  height: "24px",
                  borderRadius: "50%",
                  backgroundColor: inputText.trim() && !loading ? "rgba(255,255,255,0.18)" : "transparent",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "transform 0.2s ease",
                }}
              >
                <Send size={13} style={{ transform: "translateX(1px)" }} />
              </div>
            </button>
          </div>

          {/* Institutional Subtext */}
          <div
            style={{
              marginTop: "0.6rem",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              fontSize: "0.72rem",
              color: "var(--text-faint)",
              fontFamily: "var(--font-mono)",
            }}
          >
            <span>Vidhik Public Assistant &bull; Local Qwen Legal Reasoning &bull; IndicTrans2 Multilingual Representation</span>
            <span>Press Enter to Submit &bull; Shift+Enter for Linebreak</span>
          </div>
        </div>
      </footer>

      {/* Global CSS animations for Pulse & Spin */}
      <style jsx global>{`
        @keyframes spin {
          0% {
            transform: rotate(0deg);
          }
          100% {
            transform: rotate(360deg);
          }
        }
        @keyframes pulseDot {
          0% {
            box-shadow: 0 0 0 0 rgba(110, 31, 42, 0.4);
          }
          70% {
            box-shadow: 0 0 0 6px rgba(110, 31, 42, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(110, 31, 42, 0);
          }
        }
      `}</style>
    </div>
  );
}
