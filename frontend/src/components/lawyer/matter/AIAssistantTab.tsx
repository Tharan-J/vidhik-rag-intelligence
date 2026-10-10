"use client";

import React, { useState } from "react";
import { Matter } from "@/lib/types/matter";
import {
  Sparkles,
  Scale,
  Send,
  FileText,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Globe,
  Languages,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

interface AIAssistantTabProps {
  matter: Matter;
}

interface MessageItem {
  id: string;
  sender: "user" | "assistant";
  text: string;
  sourceBadge?: string;
  routeType?: "rag" | "ai";
  evidence?: any[];
  timestamp: string;
}

function getDynamicSuggestedQueries(matter: Matter): { title: string; query: string }[] {
  const list: { title: string; query: string }[] = [];

  // 1. Case Overview / Summary
  list.push({
    title: "Case Overview",
    query: "Tell me about this case and its current procedural stage.",
  });

  // 2. Framed Legal Issues (derived dynamically from matter.issues)
  if (matter.issues && matter.issues.length > 0) {
    const primaryIssue = matter.issues[0];
    list.push({
      title: "Framed Issue",
      query: `Analyze Issue 1: "${primaryIssue.title}" based on our case record.`,
    });
  } else {
    list.push({
      title: "Framed Issues",
      query: "What legal issues have been framed or are pending determination in this matter?",
    });
  }

  // 3. Statutory Provisions (derived dynamically from matter.sections)
  if (matter.sections && matter.sections.length > 0) {
    const primarySec = matter.sections[0];
    list.push({
      title: "Statutory Law",
      query: `How does ${primarySec.act} ${primarySec.section} apply to the facts of ${matter.title}?`,
    });
  } else {
    list.push({
      title: "Governing Law",
      query: "What statutory sections and legal grounds govern this matter?",
    });
  }

  // 4. Filed Documents or Timeline (derived from matter.documents or matter.timeline)
  if (matter.documents && matter.documents.length > 0) {
    const primaryDoc = matter.documents[0];
    list.push({
      title: "Document Record",
      query: `Summarize the key points in "${primaryDoc.name}" and our filed pleadings.`,
    });
  } else if (matter.timeline && matter.timeline.length > 0) {
    list.push({
      title: "Case Timeline",
      query: "Review our matter timeline and summarize the upcoming hearings and procedural milestones.",
    });
  } else {
    list.push({
      title: "Evidence & Record",
      query: "Review the evidence, parties, and procedural record of this matter.",
    });
  }

  return list;
}

export function AIAssistantTab({ matter }: AIAssistantTabProps) {
  const dynamicSuggestedQueries = React.useMemo(() => getDynamicSuggestedQueries(matter), [matter]);

  const [messages, setMessages] = useState<MessageItem[]>(() => [
    {
      id: `M-0-${matter.id}`,
      sender: "assistant",
      text: `Good day, Counsel. I am your Matter Intelligence Assistant for this workspace: "${matter.title}" (${matter.caseNumber || "Case Record"}), currently at the ${matter.status} stage before ${matter.court}.\n\nI am exclusively informed by this matter's case file—including our filed pleadings, procedural timeline, framed issues, governing statutes, and pinned evidence. Ask me to summarize this case, review our documents, or assess our legal grounds.`,
      sourceBadge: `Case File: ${matter.title}`,
      routeType: "ai",
      timestamp: "Just now",
    },
  ]);

  // Update greeting when user switches to a different matter workspace
  React.useEffect(() => {
    setMessages([
      {
        id: `M-0-${matter.id}`,
        sender: "assistant",
        text: `Good day, Counsel. I am your Matter Intelligence Assistant for this workspace: "${matter.title}" (${matter.caseNumber || "Case Record"}), currently at the ${matter.status} stage before ${matter.court}.\n\nI am exclusively informed by this matter's case file—including our filed pleadings, procedural timeline, framed issues, governing statutes, and pinned evidence. Ask me to summarize this case, review our documents, or assess our legal grounds.`,
        sourceBadge: `Case File: ${matter.title}`,
        routeType: "ai",
        timestamp: "Just now",
      },
    ]);
  }, [matter.id, matter.title, matter.caseNumber, matter.status, matter.court]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedEvidenceId, setExpandedEvidenceId] = useState<string | null>(null);

  // Multilingual translation state for assistant responses
  const [messageLangs, setMessageLangs] = useState<Record<string, string>>({});
  const [messageTranslations, setMessageTranslations] = useState<Record<string, Record<string, any>>>({});
  const [translatingMsgId, setTranslatingMsgId] = useState<string | null>(null);
  const [messageErrors, setMessageErrors] = useState<Record<string, string>>({});

  const handleTranslateMessage = async (msgId: string, originalText: string, targetLang: string) => {
    if (targetLang === "en") {
      setMessageLangs((prev) => ({ ...prev, [msgId]: "en" }));
      setMessageErrors((prev) => {
        const copy = { ...prev };
        delete copy[msgId];
        return copy;
      });
      return;
    }

    if (messageTranslations[msgId]?.[targetLang]) {
      setMessageLangs((prev) => ({ ...prev, [msgId]: targetLang }));
      setMessageErrors((prev) => {
        const copy = { ...prev };
        delete copy[msgId];
        return copy;
      });
      return;
    }

    setTranslatingMsgId(msgId);
    setMessageErrors((prev) => {
      const copy = { ...prev };
      delete copy[msgId];
      return copy;
    });

    try {
      const res = await fetch("/api/translate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-lawyer-token": "dev_lawyer_token",
          "x-matter-id": matter.id,
        },
        body: JSON.stringify({
          english_answer: originalText,
          target_language: targetLang,
          matter_id: matter.id,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error?.message || `Translation failed with status ${res.status}`);
      }

      setMessageTranslations((prev) => ({
        ...prev,
        [msgId]: { ...(prev[msgId] || {}), [targetLang]: data },
      }));
      setMessageLangs((prev) => ({ ...prev, [msgId]: targetLang }));
    } catch (err: any) {
      console.error("Message translation error:", err);
      setMessageErrors((prev) => ({ ...prev, [msgId]: err.message || "Failed to translate message" }));
    } finally {
      setTranslatingMsgId(null);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputText;
    if (!query.trim() || loading) return;

    const userMsg: MessageItem = {
      id: `USR-${Date.now()}`,
      sender: "user",
      text: query.trim(),
      timestamp: "Just now",
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText("");
    setLoading(true);

    try {
      const res = await fetch("/api/ai/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.trim(),
          matter,
        }),
      });

      if (!res.ok) throw new Error("Assistant request failed");
      const data = await res.json();

      const assistantMsg: MessageItem = {
        id: `AST-${Date.now()}`,
        sender: "assistant",
        text: data.answer || "No response received.",
        sourceBadge: data.sourceBadge || "Answered via AI",
        routeType: data.routeType || "ai",
        evidence: data.evidence || [],
        timestamp: "Just now",
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: MessageItem = {
        id: `ERR-${Date.now()}`,
        sender: "assistant",
        text: "I encountered a communication error while querying the intelligence pipeline. Please verify the query and try again.",
        sourceBadge: "Answered via AI",
        routeType: "ai",
        timestamp: "Just now",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "1080px" }}>
      {/* Header */}
      <div style={{ marginBottom: "1.75rem" }}>
        <h3
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "1.55rem",
            fontWeight: 700,
            color: "var(--text-ink)",
            marginBottom: "0.35rem",
          }}
        >
          Matter Intelligence Assistant
        </h3>
        <p style={{ fontSize: "0.88rem", color: "var(--text-muted)", margin: 0 }}>
          Assists with case comparisons, document analysis, statutory sections, and strategic case predictions.
        </p>
      </div>

      {/* Suggested Quick Prompts */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "0.75rem",
          marginBottom: "1.5rem",
        }}
      >
        {dynamicSuggestedQueries.map((item, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(item.query)}
            disabled={loading}
            style={{
              padding: "0.85rem 1rem",
              backgroundColor: "var(--bg-sheet)",
              border: "1px solid var(--border-rule)",
              borderRadius: "3px",
              textAlign: "left",
              cursor: loading ? "wait" : "pointer",
              transition: "all 0.15s ease",
              boxShadow: "var(--shadow-sheet)",
              minWidth: 0,
              maxWidth: "100%",
              boxSizing: "border-box",
              overflowWrap: "anywhere",
              wordBreak: "break-word",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--maroon)";
              e.currentTarget.style.backgroundColor = "var(--bg-parchment)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--border-rule)";
              e.currentTarget.style.backgroundColor = "var(--bg-sheet)";
            }}
          >
            <div
              style={{
                fontSize: "0.72rem",
                fontFamily: "var(--font-mono)",
                fontWeight: 700,
                color: "var(--maroon)",
                textTransform: "uppercase",
                marginBottom: "0.25rem",
                overflowWrap: "anywhere",
                wordBreak: "break-word",
              }}
            >
              {item.title}
            </div>
            <div
              style={{
                fontSize: "0.8rem",
                color: "var(--text-ink)",
                lineHeight: 1.35,
                overflowWrap: "anywhere",
                wordBreak: "break-word",
                whiteSpace: "normal",
              }}
            >
              {item.query}
            </div>
          </button>
        ))}
      </div>

      {/* Chat Messages Container */}
      <div
        className="paper-card"
        style={{
          backgroundColor: "var(--bg-sheet)",
          border: "1.5px solid var(--border-dark)",
          borderRadius: "3px",
          minHeight: "420px",
          display: "flex",
          flexDirection: "column",
          boxShadow: "var(--shadow-sheet)",
        }}
      >
        {/* Messages Stream */}
        <div
          style={{
            flex: 1,
            padding: "1.75rem",
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: "1.25rem",
            maxHeight: "560px",
          }}
        >
          {messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: msg.sender === "user" ? "flex-end" : "flex-start",
              }}
            >
              <div
                style={{
                  maxWidth: "85%",
                  backgroundColor:
                    msg.sender === "user"
                      ? "var(--maroon-faint)"
                      : "var(--bg-parchment)",
                  border:
                    msg.sender === "user"
                      ? "1px solid var(--maroon-border)"
                      : "1px solid var(--border-rule)",
                  borderRadius: "3px",
                  padding: "1.1rem 1.35rem",
                  boxSizing: "border-box",
                  minWidth: 0,
                  overflowWrap: "anywhere",
                  wordBreak: "break-word",
                }}
              >
                {/* Message Body */}
                <div
                  style={{
                    fontSize: "0.92rem",
                    color: "var(--text-ink)",
                    lineHeight: 1.6,
                    whiteSpace: "pre-wrap",
                    overflowWrap: "anywhere",
                    wordBreak: "break-word",
                    fontFamily:
                      msg.sender === "user"
                        ? "var(--font-sans)"
                        : "var(--font-serif)",
                  }}
                >
                  {(() => {
                    const currentLang = messageLangs[msg.id] || "en";
                    if (currentLang === "en" || !messageTranslations[msg.id]?.[currentLang]) {
                      return msg.text;
                    }
                    return messageTranslations[msg.id][currentLang].translated_answer;
                  })()}
                </div>

                {/* Multilingual Selector for Assistant Messages */}
                {msg.sender === "assistant" && (
                  <div
                    style={{
                      marginTop: "0.85rem",
                      paddingTop: "0.65rem",
                      borderTop: "1px solid var(--border-rule)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      flexWrap: "wrap",
                      gap: "0.4rem",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "0.35rem", flexWrap: "wrap" }}>
                      <span
                        style={{
                          fontSize: "0.68rem",
                          fontFamily: "var(--font-mono)",
                          fontWeight: 700,
                          color: "var(--maroon)",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.25rem",
                          textTransform: "uppercase",
                        }}
                      >
                        <Globe size={11} />
                        Language:
                      </span>
                      {[
                        { code: "en", label: "EN" },
                        { code: "ta", label: "தமிழ்" },
                        { code: "hi", label: "हिंदी" },
                        { code: "kn", label: "ಕನ್ನಡ" },
                        { code: "mr", label: "मराठी" },
                      ].map((l) => {
                        const currentLang = messageLangs[msg.id] || "en";
                        const isCurrent = currentLang === l.code;
                        return (
                          <button
                            key={l.code}
                            onClick={() => handleTranslateMessage(msg.id, msg.text, l.code)}
                            disabled={translatingMsgId === msg.id}
                            style={{
                              padding: "0.15rem 0.45rem",
                              fontSize: "0.7rem",
                              fontFamily: "var(--font-sans)",
                              fontWeight: isCurrent ? 700 : 500,
                              backgroundColor: isCurrent ? "var(--maroon)" : "#FFFFFF",
                              color: isCurrent ? "#FFFFFF" : "var(--text-ink)",
                              border: isCurrent
                                ? "1px solid var(--maroon)"
                                : "1px solid var(--border-rule)",
                              borderRadius: "2px",
                              cursor: translatingMsgId === msg.id ? "wait" : "pointer",
                            }}
                          >
                            {l.label}
                          </button>
                        );
                      })}
                    </div>

                    {translatingMsgId === msg.id && (
                      <span
                        style={{
                          fontSize: "0.68rem",
                          fontFamily: "var(--font-mono)",
                          color: "var(--maroon)",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.25rem",
                        }}
                      >
                        <Loader2 size={11} className="animate-spin" />
                        Translating...
                      </span>
                    )}

                    {messageLangs[msg.id] && messageLangs[msg.id] !== "en" && (
                      <span
                        style={{
                          fontSize: "0.65rem",
                          fontFamily: "var(--font-mono)",
                          color: "var(--status-supported-text)",
                          backgroundColor: "var(--status-supported-bg)",
                          border: "1px solid var(--status-supported-border)",
                          padding: "0.1rem 0.35rem",
                          borderRadius: "2px",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.25rem",
                        }}
                      >
                        <CheckCircle2 size={10} />
                        IndicTrans2
                      </span>
                    )}
                  </div>
                )}

                {/* Error Banner for Message Translation */}
                {messageErrors[msg.id] && (
                  <div
                    style={{
                      marginTop: "0.5rem",
                      padding: "0.4rem 0.6rem",
                      backgroundColor: "#FEF2F2",
                      border: "1px solid #FCA5A5",
                      borderRadius: "2px",
                      color: "#991B1B",
                      fontSize: "0.75rem",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.35rem",
                    }}
                  >
                    <AlertCircle size={12} />
                    <span>{messageErrors[msg.id]}</span>
                  </div>
                )}


                {/* Evidence Chunks Expandable (if returned) */}
                {msg.evidence && msg.evidence.length > 0 && (
                  <div
                    style={{
                      marginTop: "1rem",
                      paddingTop: "0.75rem",
                      borderTop: "1px solid var(--border-subtle)",
                    }}
                  >
                    <button
                      onClick={() =>
                        setExpandedEvidenceId(
                          expandedEvidenceId === msg.id ? null : msg.id
                        )
                      }
                      style={{
                        background: "none",
                        border: "none",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.4rem",
                        fontSize: "0.74rem",
                        fontFamily: "var(--font-mono)",
                        color: "var(--maroon)",
                        fontWeight: 600,
                        cursor: "pointer",
                        padding: 0,
                      }}
                    >
                      <FileText size={13} />
                      <span>
                        {expandedEvidenceId === msg.id
                          ? "Hide Supporting Judicial Authorities"
                          : `View Supporting Authorities (${msg.evidence.length} Precedent Chunks)`}
                      </span>
                      {expandedEvidenceId === msg.id ? (
                        <ChevronUp size={12} />
                      ) : (
                        <ChevronDown size={12} />
                      )}
                    </button>

                    {expandedEvidenceId === msg.id && (
                      <div
                        style={{
                          marginTop: "0.75rem",
                          display: "flex",
                          flexDirection: "column",
                          gap: "0.6rem",
                        }}
                      >
                        {msg.evidence.map((ev: any, i: number) => (
                          <div
                            key={i}
                            style={{
                              backgroundColor: "var(--bg-sheet)",
                              border: "1px solid var(--border-rule)",
                              borderRadius: "2px",
                              padding: "0.75rem 0.9rem",
                              fontSize: "0.78rem",
                            }}
                          >
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                fontWeight: 700,
                                color: "var(--text-ink)",
                                marginBottom: "0.25rem",
                              }}
                            >
                              <span>
                                [{ev.evidence_id || `E${i + 1}`}] {ev.case_title || ev.document_id}
                              </span>
                              <span
                                style={{
                                  fontSize: "0.7rem",
                                  color: "var(--text-faint)",
                                  fontFamily: "var(--font-mono)",
                                }}
                              >
                                {ev.court}
                              </span>
                            </div>
                            <div
                              style={{
                                color: "var(--text-muted)",
                                lineHeight: 1.45,
                                fontStyle: "italic",
                                marginBottom: "0.4rem",
                              }}
                            >
                              &ldquo;{ev.preview || ev.text?.slice(0, 240)}...&rdquo;
                            </div>

                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem", marginTop: "0.35rem" }}>
                              <span style={{ fontSize: "0.68rem", fontFamily: "var(--font-mono)", color: "var(--text-faint)" }}>
                                {ev.document_id} • {ev.page_number || "Page Record"}
                              </span>
                              <a
                                href={`/api/documents/stream?documentId=${encodeURIComponent(ev.document_id || "")}&matterId=${encodeURIComponent(matter.id)}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{
                                  display: "inline-flex",
                                  alignItems: "center",
                                  gap: "0.25rem",
                                  fontSize: "0.7rem",
                                  fontWeight: 600,
                                  color: "var(--navy)",
                                  textDecoration: "none",
                                }}
                              >
                                <span>Source PDF</span>
                                <ExternalLink size={10} />
                              </a>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Footer with clean badge ONLY: answered via rag or ai */}
                {msg.sender === "assistant" && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginTop: "0.85rem",
                      paddingTop: "0.6rem",
                      borderTop: "1px solid var(--border-subtle)",
                      fontSize: "0.72rem",
                    }}
                  >
                    <span style={{ color: "var(--text-faint)", fontFamily: "var(--font-mono)" }}>
                      {msg.timestamp}
                    </span>

                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.35rem",
                        fontFamily: "var(--font-mono)",
                        fontWeight: 700,
                        fontSize: "0.72rem",
                        letterSpacing: "0.04em",
                        color:
                          msg.routeType === "rag"
                            ? "var(--maroon)"
                            : "var(--status-supported-text)",
                        backgroundColor:
                          msg.routeType === "rag"
                            ? "var(--maroon-faint)"
                            : "var(--status-supported-bg)",
                        padding: "0.2rem 0.55rem",
                        borderRadius: "2px",
                        border:
                          msg.routeType === "rag"
                            ? "1px solid var(--maroon-border)"
                            : "1px solid var(--status-supported-border)",
                      }}
                    >
                      {msg.routeType === "rag" ? <Scale size={12} /> : <Sparkles size={12} />}
                      <span>{msg.sourceBadge || (msg.routeType === "rag" ? "Answered via Vidhik RAG" : "Answered via AI")}</span>
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ display: "flex", justifyContent: "flex-start" }}>
              <div
                style={{
                  backgroundColor: "var(--bg-parchment)",
                  border: "1px solid var(--border-rule)",
                  padding: "0.9rem 1.25rem",
                  borderRadius: "3px",
                  fontSize: "0.84rem",
                  color: "var(--text-muted)",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.6rem",
                  fontFamily: "var(--font-mono)",
                }}
              >
                <div
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: "var(--maroon)",
                    animation: "pulse 1.2s infinite",
                  }}
                />
                <span>Synthesizing legal intelligence across matter record & RAG corpus...</span>
              </div>
            </div>
          )}
        </div>

        {/* Query Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          style={{
            borderTop: "1.5px solid var(--border-dark)",
            padding: "1rem 1.25rem",
            backgroundColor: "var(--bg-sheet)",
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
          }}
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Ask a question about documents, case comparisons, sections, or predictions..."
            disabled={loading}
            style={{
              flex: 1,
              border: "1px solid var(--border-rule)",
              borderRadius: "2px",
              padding: "0.65rem 1rem",
              fontSize: "0.92rem",
              fontFamily: "var(--font-sans)",
              color: "var(--text-ink)",
              backgroundColor: "var(--bg-parchment)",
              outline: "none",
            }}
          />

          <button
            type="submit"
            disabled={loading || !inputText.trim()}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.45rem",
              padding: "0.65rem 1.35rem",
              backgroundColor:
                loading || !inputText.trim() ? "var(--border-dark)" : "var(--maroon)",
              color: "#FFFFFF",
              fontSize: "0.84rem",
              fontWeight: 600,
              border: "none",
              borderRadius: "2px",
              cursor: loading || !inputText.trim() ? "not-allowed" : "pointer",
              transition: "background-color 0.15s ease",
            }}
          >
            <Send size={14} />
            <span>Submit</span>
          </button>
        </form>
      </div>
    </div>
  );
}
