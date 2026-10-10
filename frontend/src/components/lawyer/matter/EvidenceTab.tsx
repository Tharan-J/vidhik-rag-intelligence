"use client";

import React, { useState, useMemo } from "react";
import { Matter, MatterEvidenceItem } from "@/lib/types/matter";
import {
  Scale,
  FileText,
  ExternalLink,
  Pin,
  PinOff,
  Search,
  Filter,
  Plus,
  MessageSquare,
  ChevronDown,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  ArrowDown,
  Layers,
  Link2,
  X,
  Sparkles,
  BookOpen,
  Copy,
  Check,
  RefreshCw,
} from "lucide-react";
import { ProvenanceBadge } from "./ProvenanceBadge";

interface EvidenceTabProps {
  matter: Matter;
  onUpdateEvidence?: (evidence: MatterEvidenceItem[]) => void;
}

export function EvidenceTab({ matter, onUpdateEvidence }: EvidenceTabProps) {
  // Local state for evidence items (allows pinning, adding notes, linking, and RAG retrieval)
  const [evidenceList, setEvidenceList] = useState<MatterEvidenceItem[]>(() => {
    return matter.evidence && matter.evidence.length > 0 ? matter.evidence : [];
  });

  React.useEffect(() => {
    setEvidenceList(matter.evidence && matter.evidence.length > 0 ? matter.evidence : []);
  }, [matter.id, matter.evidence]);

  // Filter & Search states
  const [selectedIssueId, setSelectedIssueId] = useState<string>("ALL");
  const [stanceFilter, setStanceFilter] = useState<"ALL" | "supporting" | "contradicting" | "pinned">("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Inspecting Source Modal state
  const [inspectingItem, setInspectingItem] = useState<MatterEvidenceItem | null>(null);
  const [copiedText, setCopiedText] = useState(false);

  // RAG Search loading state
  const [ragLoadingIssueId, setRagLoadingIssueId] = useState<string | null>(null);
  const [ragLoadingClaimId, setRagLoadingClaimId] = useState<string | null>(null);
  const [ragStatusMessage, setRagStatusMessage] = useState<string | null>(null);

  // Note authoring state
  const [activeNoteItemId, setActiveNoteItemId] = useState<string | null>(null);
  const [noteDraft, setNoteDraft] = useState<string>("");

  // Link to Issue modal state
  const [linkingItem, setLinkingItem] = useState<MatterEvidenceItem | null>(null);
  const [targetIssueId, setTargetIssueId] = useState<string>("");

  // Issues derived from matter
  const issues = matter.issues || [];

  // Toggle Pin on an evidence item
  const handleTogglePin = (id: string) => {
    setEvidenceList((prev) => {
      const updated = prev.map((item) => (item.id === id ? { ...item, isPinned: !item.isPinned } : item));
      if (onUpdateEvidence) onUpdateEvidence(updated);
      return updated;
    });
  };

  // Add Lawyer Note
  const handleSaveNote = (id: string) => {
    if (!noteDraft.trim()) return;
    setEvidenceList((prev) => {
      const updated = prev.map((item) =>
        item.id === id
          ? { ...item, notes: [...(item.notes || []), noteDraft.trim()] }
          : item
      );
      if (onUpdateEvidence) onUpdateEvidence(updated);
      return updated;
    });
    setNoteDraft("");
    setActiveNoteItemId(null);
  };

  // Re-link evidence to another issue
  const handleConfirmLink = () => {
    if (!linkingItem || !targetIssueId) return;
    const targetIssue = issues.find((i) => i.id === targetIssueId);
    if (!targetIssue) return;

    setEvidenceList((prev) => {
      const updated = prev.map((item) =>
        item.id === linkingItem.id
          ? {
              ...item,
              issueId: targetIssue.id,
              issueTitle: targetIssue.title,
            }
          : item
      );
      if (onUpdateEvidence) onUpdateEvidence(updated);
      return updated;
    });
    setLinkingItem(null);
    setTargetIssueId("");
  };

  // Find Supporting Evidence for an Issue via Vidhik RAG
  const handleFindSupportingForIssue = async (issueId: string, issueTitle: string) => {
    try {
      setRagLoadingIssueId(issueId);
      setRagStatusMessage(`Retrieving judicial authorities supporting "${issueTitle}" from Vidhik RAG...`);

      const res = await fetch("/api/evidence/rag-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: `${matter.matterType} ${issueTitle} supporting precedent`,
          stance: "supporting",
          issueId,
          issueTitle,
          matterId: matter.id,
        }),
      });

      if (!res.ok) throw new Error("RAG retrieval failed");
      const data = await res.json();

      if (data.evidence && data.evidence.length > 0) {
        setEvidenceList((prev) => {
          const updated = [...data.evidence, ...prev];
          if (onUpdateEvidence) onUpdateEvidence(updated);
          return updated;
        });
        setRagStatusMessage(
          `Retrieved ${data.evidence.length} supporting judicial records via Vidhik Hybrid RAG in ${data.execution_time_seconds}s.`
        );
      } else {
        setRagStatusMessage("No additional matching authorities found in current corpus.");
      }
    } catch (err) {
      console.error(err);
      setRagStatusMessage("Failed to query Vidhik RAG. Please retry.");
    } finally {
      setRagLoadingIssueId(null);
      setTimeout(() => setRagStatusMessage(null), 5000);
    }
  };

  // Find Evidence Against Position via Vidhik RAG
  const handleFindEvidenceAgainstClaim = async (
    claimText: string,
    issueId: string,
    issueTitle: string
  ) => {
    try {
      setRagLoadingClaimId(claimText);
      setRagStatusMessage(`Retrieving contradicting authorities against position from Vidhik RAG...`);

      const res = await fetch("/api/evidence/rag-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: `contrary dissenting counter precedent ${claimText}`,
          stance: "contradicting",
          issueId,
          issueTitle,
          claim: `Contrary legal position: Counter-authority regarding "${claimText.slice(0, 80)}..."`,
          matterId: matter.id,
        }),
      });

      if (!res.ok) throw new Error("RAG retrieval failed");
      const data = await res.json();

      if (data.evidence && data.evidence.length > 0) {
        setEvidenceList((prev) => {
          const updated = [...data.evidence, ...prev];
          if (onUpdateEvidence) onUpdateEvidence(updated);
          return updated;
        });
        setRagStatusMessage(
          `Retrieved ${data.evidence.length} counter-authorities via Vidhik Hybrid RAG in ${data.execution_time_seconds}s.`
        );
      } else {
        setRagStatusMessage("No contradicting precedents found in current corpus.");
      }
    } catch (err) {
      console.error(err);
      setRagStatusMessage("Failed to query Vidhik RAG. Please retry.");
    } finally {
      setRagLoadingClaimId(null);
      setTimeout(() => setRagStatusMessage(null), 5000);
    }
  };

  // Copy verbatim source text
  const handleCopySource = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(true);
    setTimeout(() => setCopiedText(false), 2000);
  };

  // Filtered evidence items
  const filteredEvidence = useMemo(() => {
    return evidenceList.filter((item) => {
      // Issue filter
      if (selectedIssueId !== "ALL" && item.issueId !== selectedIssueId) {
        return false;
      }
      // Stance / Pinned filter
      if (stanceFilter === "supporting" && item.stance !== "supporting") {
        return false;
      }
      if (stanceFilter === "contradicting" && item.stance !== "contradicting") {
        return false;
      }
      if (stanceFilter === "pinned" && !item.isPinned) {
        return false;
      }
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesClaim = item.claim.toLowerCase().includes(q);
        const matchesExcerpt = item.evidenceExcerpt.toLowerCase().includes(q);
        const matchesDoc = item.sourceDocument.toLowerCase().includes(q);
        const matchesAuth =
          item.relatedAuthority?.caseTitle.toLowerCase().includes(q) ||
          item.relatedAuthority?.citation?.toLowerCase().includes(q);
        const matchesIssue = item.issueTitle.toLowerCase().includes(q);
        if (!matchesClaim && !matchesExcerpt && !matchesDoc && !matchesAuth && !matchesIssue) {
          return false;
        }
      }
      return true;
    });
  }, [evidenceList, selectedIssueId, stanceFilter, searchQuery]);

  // Group filtered evidence by Issue -> Claim (Evidence Map structure)
  const evidenceMapByIssue = useMemo(() => {
    // Map of issueId -> list of items
    const map = new Map<string, { issueTitle: string; items: MatterEvidenceItem[] }>();

    filteredEvidence.forEach((item) => {
      const key = item.issueId || "GENERAL";
      if (!map.has(key)) {
        map.set(key, {
          issueTitle: item.issueTitle || "General Legal Grounds",
          items: [],
        });
      }
      map.get(key)!.items.push(item);
    });

    return map;
  }, [filteredEvidence]);

  // Metrics
  const totalCount = evidenceList.length;
  const supportingCount = evidenceList.filter((e) => e.stance === "supporting").length;
  const contradictingCount = evidenceList.filter((e) => e.stance === "contradicting").length;
  const pinnedCount = evidenceList.filter((e) => e.isPinned).length;

  return (
    <div style={{ maxWidth: "1120px", margin: "0 auto", paddingBottom: "4rem" }}>
      {/* ── Top Header & Architectural Philosophy ───────────────────────────────── */}
      <div
        style={{
          borderBottom: "1.5px solid var(--border-rule)",
          paddingBottom: "1.25rem",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.35rem" }}>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  backgroundColor: "var(--maroon)",
                  color: "#FFFFFF",
                  padding: "0.15rem 0.5rem",
                  borderRadius: "2px",
                  letterSpacing: "0.04em",
                }}
              >
                EVIDENCE MAP
              </span>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.72rem",
                  color: "var(--navy)",
                  fontWeight: 600,
                }}
              >
                {matter.caseNumber} • {matter.court}
              </span>
            </div>
            <h2
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1.5rem",
                fontWeight: 700,
                color: "var(--text-ink)",
                margin: "0 0 0.35rem 0",
              }}
            >
              Matter Evidence & Provenance Map
            </h2>
            <p
              style={{
                fontSize: "0.85rem",
                color: "var(--text-muted)",
                margin: 0,
                lineHeight: 1.45,
                maxWidth: "760px",
              }}
            >
              Structured hierarchy showing exactly what material supports or weakens each legal position in{" "}
              <strong>{matter.title}</strong>: from <em>Issue</em> → <em>Claim</em> →{" "}
              <em>Supporting / Contradicting Evidence</em> → <em>Original Document</em>.
            </p>
          </div>

          {/* Core Provenance Pipeline Tag */}
          <div
            style={{
              padding: "0.6rem 0.9rem",
              backgroundColor: "var(--bg-parchment)",
              border: "1px solid var(--border-rule)",
              borderRadius: "3px",
              textAlign: "right",
              display: "flex",
              flexDirection: "column",
              gap: "0.2rem",
            }}
          >
            <span style={{ fontSize: "0.68rem", fontFamily: "var(--font-mono)", color: "var(--maroon)", fontWeight: 700 }}>
              VERIFIABLE RAG PROVENANCE
            </span>
            <span style={{ fontSize: "0.72rem", color: "var(--text-faint)" }}>
              All excerpts tied to verbatim judicial records
            </span>
          </div>
        </div>

        {/* Dynamic Notification Banner if RAG executed */}
        {ragStatusMessage && (
          <div
            style={{
              marginTop: "1rem",
              padding: "0.65rem 1rem",
              backgroundColor: "var(--maroon-faint)",
              border: "1px solid var(--maroon)",
              borderRadius: "3px",
              display: "flex",
              alignItems: "center",
              gap: "0.6rem",
              fontSize: "0.82rem",
              color: "var(--maroon)",
              fontWeight: 600,
              animation: "fadeIn 0.2s ease-in-out",
            }}
          >
            <RefreshCw size={14} className={ragLoadingIssueId || ragLoadingClaimId ? "animate-spin" : ""} />
            <span>{ragStatusMessage}</span>
          </div>
        )}
      </div>

      {/* ── Toolbar: Search, Issue Filter, Stance Filter & Stats ──────────────────── */}
      <div
        className="paper-card"
        style={{
          padding: "1rem 1.25rem",
          backgroundColor: "var(--bg-sheet)",
          border: "1.5px solid var(--border-rule)",
          borderRadius: "3px",
          marginBottom: "1.75rem",
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.4fr 1fr",
            gap: "1rem",
            alignItems: "center",
          }}
          className="research-breakdown-grid"
        >
          {/* Search Box */}
          <div style={{ position: "relative", width: "100%" }}>
            <Search
              size={15}
              style={{
                position: "absolute",
                left: "0.75rem",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-faint)",
              }}
            />
            <input
              type="text"
              placeholder="Search evidence excerpts, claims, citations, or document names..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: "100%",
                padding: "0.55rem 0.75rem 0.55rem 2.2rem",
                fontSize: "0.84rem",
                borderRadius: "3px",
                border: "1px solid var(--border-rule)",
                backgroundColor: "var(--bg-parchment)",
                color: "var(--text-ink)",
                outline: "none",
                fontFamily: "var(--font-sans)",
              }}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                style={{
                  position: "absolute",
                  right: "0.65rem",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "var(--text-faint)",
                }}
              >
                <X size={13} />
              </button>
            )}
          </div>

          {/* Filter by Issue Dropdown */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", whiteSpace: "nowrap" }}>
              Filter by Issue:
            </span>
            <select
              value={selectedIssueId}
              onChange={(e) => setSelectedIssueId(e.target.value)}
              style={{
                flex: 1,
                padding: "0.5rem 0.75rem",
                fontSize: "0.8rem",
                borderRadius: "3px",
                border: "1px solid var(--border-rule)",
                backgroundColor: "var(--bg-parchment)",
                color: "var(--text-ink)",
                cursor: "pointer",
                fontWeight: 600,
                outline: "none",
              }}
            >
              <option value="ALL">All Issues ({totalCount} evidence items)</option>
              {issues.map((iss) => {
                const countForIss = evidenceList.filter((e) => e.issueId === iss.id).length;
                return (
                  <option key={iss.id} value={iss.id}>
                    {iss.issueNumber ? `${iss.issueNumber}: ` : ""}
                    {iss.title} ({countForIss})
                  </option>
                );
              })}
            </select>
          </div>
        </div>

        {/* Filter Pills & Metric Counters */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "0.75rem",
            borderTop: "1px solid var(--border-subtle)",
            paddingTop: "0.75rem",
          }}
        >
          {/* Stance Filter Buttons */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <span style={{ fontSize: "0.74rem", fontWeight: 600, color: "var(--text-faint)", marginRight: "0.25rem" }}>
              Stance:
            </span>

            <button
              onClick={() => setStanceFilter("ALL")}
              style={{
                padding: "0.3rem 0.7rem",
                fontSize: "0.76rem",
                fontWeight: 600,
                borderRadius: "3px",
                border: `1.5px solid ${stanceFilter === "ALL" ? "var(--maroon)" : "var(--border-rule)"}`,
                backgroundColor: stanceFilter === "ALL" ? "var(--maroon-faint)" : "transparent",
                color: stanceFilter === "ALL" ? "var(--maroon)" : "var(--text-muted)",
                cursor: "pointer",
              }}
            >
              All ({totalCount})
            </button>

            <button
              onClick={() => setStanceFilter("supporting")}
              style={{
                padding: "0.3rem 0.7rem",
                fontSize: "0.76rem",
                fontWeight: 600,
                borderRadius: "3px",
                border: `1.5px solid ${stanceFilter === "supporting" ? "#10754A" : "var(--border-rule)"}`,
                backgroundColor: stanceFilter === "supporting" ? "#EBF7F0" : "transparent",
                color: stanceFilter === "supporting" ? "#10754A" : "var(--text-muted)",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.3rem",
              }}
            >
              <CheckCircle2 size={12} color="#10754A" />
              Supporting ({supportingCount})
            </button>

            <button
              onClick={() => setStanceFilter("contradicting")}
              style={{
                padding: "0.3rem 0.7rem",
                fontSize: "0.76rem",
                fontWeight: 600,
                borderRadius: "3px",
                border: `1.5px solid ${stanceFilter === "contradicting" ? "#B91C1C" : "var(--border-rule)"}`,
                backgroundColor: stanceFilter === "contradicting" ? "#FEF2F2" : "transparent",
                color: stanceFilter === "contradicting" ? "#B91C1C" : "var(--text-muted)",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.3rem",
              }}
            >
              <AlertTriangle size={12} color="#B91C1C" />
              Contradicting ({contradictingCount})
            </button>

            <button
              onClick={() => setStanceFilter("pinned")}
              style={{
                padding: "0.3rem 0.7rem",
                fontSize: "0.76rem",
                fontWeight: 600,
                borderRadius: "3px",
                border: `1.5px solid ${stanceFilter === "pinned" ? "var(--navy)" : "var(--border-rule)"}`,
                backgroundColor: stanceFilter === "pinned" ? "rgba(26,54,93,0.08)" : "transparent",
                color: stanceFilter === "pinned" ? "var(--navy)" : "var(--text-muted)",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.3rem",
              }}
            >
              <Pin size={12} color="var(--navy)" />
              Saved / Pinned ({pinnedCount})
            </button>
          </div>

          {/* Quick Info */}
          <div style={{ fontSize: "0.74rem", color: "var(--text-faint)", fontFamily: "var(--font-mono)" }}>
            Showing {filteredEvidence.length} of {totalCount} records
          </div>
        </div>
      </div>

      {/* ── Evidence Map Visualization ────────────────────────────────────────── */}
      {evidenceMapByIssue.size === 0 ? (
        <div
          className="paper-card"
          style={{
            padding: "3rem 2rem",
            textAlign: "center",
            backgroundColor: "var(--bg-sheet)",
            border: "1.5px dashed var(--border-rule)",
            borderRadius: "4px",
          }}
        >
          <Scale size={32} style={{ color: "var(--text-faint)", margin: "0 auto 1rem auto" }} />
          <h4 style={{ fontFamily: "var(--font-serif)", fontSize: "1.1rem", color: "var(--text-ink)", marginBottom: "0.5rem" }}>
            No Evidence Matches Your Criteria
          </h4>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", maxWidth: "460px", margin: "0 auto 1.5rem auto" }}>
            Try resetting the search filters or use Vidhik RAG to retrieve relevant evidence from the 29,156 indexed judicial chunks.
          </p>
          <button
            onClick={() => {
              setSearchQuery("");
              setSelectedIssueId("ALL");
              setStanceFilter("ALL");
            }}
            style={{
              padding: "0.45rem 1rem",
              fontSize: "0.8rem",
              fontWeight: 600,
              backgroundColor: "var(--maroon)",
              color: "#FFFFFF",
              border: "none",
              borderRadius: "3px",
              cursor: "pointer",
            }}
          >
            Reset All Filters
          </button>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}>
          {Array.from(evidenceMapByIssue.entries()).map(([issueId, { issueTitle, items }]) => {
            const correspondingIssue = issues.find((i) => i.id === issueId);
            const isRagLoadingThisIssue = ragLoadingIssueId === issueId;

            // Group items under this issue by claim
            const claimGroups = new Map<string, MatterEvidenceItem[]>();
            items.forEach((item) => {
              const claimKey = item.claim;
              if (!claimGroups.has(claimKey)) {
                claimGroups.set(claimKey, []);
              }
              claimGroups.get(claimKey)!.push(item);
            });

            return (
              <div
                key={issueId}
                style={{
                  position: "relative",
                  paddingLeft: "1.5rem",
                  borderLeft: "2px solid var(--border-rule)",
                }}
              >
                {/* Visual Node Marker for ISSUE */}
                <div
                  style={{
                    position: "absolute",
                    left: "-8px",
                    top: "0px",
                    width: "14px",
                    height: "14px",
                    borderRadius: "50%",
                    backgroundColor: "var(--maroon)",
                    border: "2px solid #FFFFFF",
                    boxShadow: "0 0 0 1px var(--maroon)",
                  }}
                />

                {/* ── LEVEL 1: ISSUE HEADER ── */}
                <div
                  className="paper-card"
                  style={{
                    padding: "1.25rem 1.5rem",
                    backgroundColor: "var(--bg-parchment)",
                    border: "1.5px solid var(--border-dark)",
                    borderRadius: "3px",
                    marginBottom: "1.5rem",
                    boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      justifyContent: "space-between",
                      gap: "1rem",
                      flexWrap: "wrap",
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.3rem" }}>
                        <span
                          style={{
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.7rem",
                            fontWeight: 700,
                            color: "var(--maroon)",
                            textTransform: "uppercase",
                            letterSpacing: "0.05em",
                          }}
                        >
                          ISSUE LEVEL {correspondingIssue?.issueNumber || issueId}
                        </span>
                        {correspondingIssue?.confirmed && (
                          <span
                            style={{
                              fontSize: "0.66rem",
                              backgroundColor: "#EBF7F0",
                              color: "#10754A",
                              padding: "0.1rem 0.4rem",
                              borderRadius: "2px",
                              fontWeight: 600,
                            }}
                          >
                            Confirmed Issue
                          </span>
                        )}
                      </div>

                      <h3
                        style={{
                          fontFamily: "var(--font-serif)",
                          fontSize: "1.25rem",
                          fontWeight: 700,
                          color: "var(--text-ink)",
                          margin: "0 0 0.4rem 0",
                          lineHeight: 1.35,
                        }}
                      >
                        {issueTitle}
                      </h3>

                      {correspondingIssue?.description && (
                        <p
                          style={{
                            fontSize: "0.84rem",
                            color: "var(--text-muted)",
                            margin: 0,
                            lineHeight: 1.45,
                            maxWidth: "780px",
                          }}
                        >
                          {correspondingIssue.description}
                        </p>
                      )}
                    </div>

                    {/* Action: Ask "Find supporting evidence for this issue" via Vidhik RAG */}
                    <button
                      onClick={() => handleFindSupportingForIssue(issueId, issueTitle)}
                      disabled={isRagLoadingThisIssue}
                      style={{
                        padding: "0.45rem 0.85rem",
                        fontSize: "0.76rem",
                        fontWeight: 600,
                        backgroundColor: isRagLoadingThisIssue ? "var(--bg-sheet)" : "var(--maroon)",
                        color: isRagLoadingThisIssue ? "var(--text-faint)" : "#FFFFFF",
                        border: "1px solid var(--maroon)",
                        borderRadius: "3px",
                        cursor: isRagLoadingThisIssue ? "not-allowed" : "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.4rem",
                        transition: "all 0.15s ease",
                        whiteSpace: "nowrap",
                        boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
                      }}
                      title="Directly retrieve authoritative judicial precedent from Vidhik RAG without Gemini"
                    >
                      <Sparkles size={13} className={isRagLoadingThisIssue ? "animate-spin" : ""} />
                      {isRagLoadingThisIssue ? "Searching Vidhik RAG..." : "Find supporting evidence for this issue"}
                    </button>
                  </div>
                </div>

                {/* ── LEVEL 2 & 3: CLAIMS & EVIDENCE HIERARCHY ── */}
                <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem", paddingLeft: "0.75rem" }}>
                  {Array.from(claimGroups.entries()).map(([claimText, claimItems], cIdx) => {
                    const isRagLoadingThisClaim = ragLoadingClaimId === claimText;

                    return (
                      <div
                        key={cIdx}
                        style={{
                          position: "relative",
                          paddingLeft: "1.25rem",
                          borderLeft: "2px dashed var(--border-rule)",
                        }}
                      >
                        {/* Visual Connector for CLAIM */}
                        <div
                          style={{
                            position: "absolute",
                            left: "-6px",
                            top: "8px",
                            width: "10px",
                            height: "10px",
                            borderRadius: "2px",
                            backgroundColor: "var(--navy)",
                            border: "1.5px solid #FFFFFF",
                          }}
                        />

                        {/* ── LEVEL 2: CLAIM / ARGUMENT CARD ── */}
                        <div
                          style={{
                            backgroundColor: "var(--bg-sheet)",
                            border: "1.5px solid var(--border-rule)",
                            borderRadius: "3px",
                            padding: "0.85rem 1.15rem",
                            marginBottom: "1rem",
                            display: "flex",
                            alignItems: "flex-start",
                            justifyContent: "space-between",
                            gap: "1rem",
                            boxShadow: "0 1px 2px rgba(0,0,0,0.02)",
                          }}
                        >
                          <div>
                            <div
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "0.4rem",
                                marginBottom: "0.25rem",
                              }}
                            >
                              <span
                                style={{
                                  fontFamily: "var(--font-mono)",
                                  fontSize: "0.68rem",
                                  fontWeight: 700,
                                  color: "var(--navy)",
                                  textTransform: "uppercase",
                                  letterSpacing: "0.04em",
                                }}
                              >
                                CLAIM / ARGUMENT
                              </span>
                              <span style={{ fontSize: "0.7rem", color: "var(--text-faint)" }}>
                                ({claimItems.length} evidence {claimItems.length === 1 ? "source" : "sources"})
                              </span>
                            </div>

                            <p
                              style={{
                                fontFamily: "var(--font-sans)",
                                fontSize: "0.92rem",
                                fontWeight: 600,
                                color: "var(--text-ink)",
                                margin: 0,
                                lineHeight: 1.45,
                              }}
                            >
                              {claimText}
                            </p>
                          </div>

                          {/* Action: Ask "Find evidence against this position" via Vidhik RAG */}
                          <button
                            onClick={() => handleFindEvidenceAgainstClaim(claimText, issueId, issueTitle)}
                            disabled={isRagLoadingThisClaim}
                            style={{
                              padding: "0.35rem 0.75rem",
                              fontSize: "0.72rem",
                              fontWeight: 600,
                              backgroundColor: "transparent",
                              color: "#B91C1C",
                              border: "1px solid #FECACA",
                              borderRadius: "3px",
                              cursor: isRagLoadingThisClaim ? "not-allowed" : "pointer",
                              display: "flex",
                              alignItems: "center",
                              gap: "0.35rem",
                              whiteSpace: "nowrap",
                            }}
                            title="Query Vidhik RAG for dissenting opinions or counter-precedents"
                          >
                            <AlertTriangle size={12} color="#B91C1C" />
                            {isRagLoadingThisClaim ? "Querying RAG..." : "Find evidence against this position"}
                          </button>
                        </div>

                        {/* ── LEVEL 3: SUPPORTING / CONTRADICTING EVIDENCE CARDS ── */}
                        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                          {claimItems.map((item) => {
                            const isSupporting = item.stance === "supporting";
                            const isNoteOpen = activeNoteItemId === item.id;

                            return (
                              <div
                                key={item.id}
                                className="paper-card"
                                style={{
                                  padding: "1.25rem 1.4rem",
                                  backgroundColor: "var(--bg-sheet)",
                                  border: `1.5px solid ${
                                    item.isPinned
                                      ? "var(--navy)"
                                      : isSupporting
                                      ? "rgba(16, 117, 74, 0.35)"
                                      : "rgba(185, 28, 28, 0.35)"
                                  }`,
                                  borderRadius: "3px",
                                  boxShadow: item.isPinned
                                    ? "0 2px 6px rgba(26,54,93,0.08)"
                                    : "0 1px 3px rgba(0,0,0,0.03)",
                                  transition: "all 0.15s ease",
                                }}
                              >
                                {/* Header: Stance badge, ID, Pin button */}
                                <div
                                  style={{
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "space-between",
                                    marginBottom: "0.85rem",
                                    flexWrap: "wrap",
                                    gap: "0.5rem",
                                  }}
                                >
                                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                                    {/* Stance Indicator Badge & Verification Status */}
                                    <span
                                      style={{
                                        display: "inline-flex",
                                        alignItems: "center",
                                        gap: "0.3rem",
                                        fontSize: "0.72rem",
                                        fontWeight: 700,
                                        padding: "0.2rem 0.55rem",
                                        borderRadius: "2px",
                                        fontFamily: "var(--font-mono)",
                                        backgroundColor: isSupporting ? "#EBF7F0" : "#FEF2F2",
                                        color: isSupporting ? "#10754A" : "#B91C1C",
                                        border: `1px solid ${isSupporting ? "#B4E3CB" : "#FECACA"}`,
                                      }}
                                    >
                                      {isSupporting ? (
                                        <>
                                          <CheckCircle2 size={12} />
                                          SUPPORTS ARGUMENT
                                        </>
                                      ) : (
                                        <>
                                          <AlertTriangle size={12} />
                                          CONTRADICTS POSITION
                                        </>
                                      )}
                                    </span>

                                    {item.status && (
                                      <span
                                        style={{
                                          fontSize: "0.68rem",
                                          fontWeight: 700,
                                          fontFamily: "var(--font-mono)",
                                          padding: "0.15rem 0.45rem",
                                          borderRadius: "2px",
                                          backgroundColor: item.status === "SUPPORTED" ? "#D1FAE5" : "#FEE2E2",
                                          color: item.status === "SUPPORTED" ? "#065F46" : "#991B1B",
                                          border: `1px solid ${item.status === "SUPPORTED" ? "#A7F3D0" : "#FECACA"}`,
                                        }}
                                      >
                                        STATUS: {item.status}
                                      </span>
                                    )}

                                    {item.claimType && (
                                      <span
                                        style={{
                                          fontSize: "0.68rem",
                                          fontWeight: 700,
                                          fontFamily: "var(--font-mono)",
                                          padding: "0.15rem 0.45rem",
                                          borderRadius: "2px",
                                          backgroundColor: "#EEF2FF",
                                          color: "#3730A3",
                                          border: "1px solid #C7D2FE",
                                        }}
                                      >
                                        {item.claimType.replace(/_/g, " ")}
                                      </span>
                                    )}

                                    <ProvenanceBadge
                                      type={item.provenance || "SOURCE_EXPLICIT"}
                                      sourceDoc={item.sourceDocument}
                                      page={item.pageNumber}
                                      paragraph={item.paragraphId}
                                      onViewSource={() => setInspectingItem(item)}
                                    />

                                    {item.isCustom && (
                                      <span
                                        style={{
                                          fontSize: "0.68rem",
                                          backgroundColor: "rgba(128,0,32,0.08)",
                                          color: "var(--maroon)",
                                          padding: "0.1rem 0.4rem",
                                          borderRadius: "2px",
                                          fontFamily: "var(--font-mono)",
                                          fontWeight: 600,
                                        }}
                                      >
                                        RAG RETRIEVED
                                      </span>
                                    )}
                                  </div>

                                  {/* Right Actions: Pin & Link */}
                                  <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                                    <button
                                      onClick={() => handleTogglePin(item.id)}
                                      style={{
                                        background: "transparent",
                                        border: "1px solid var(--border-rule)",
                                        borderRadius: "2px",
                                        padding: "0.25rem 0.5rem",
                                        fontSize: "0.72rem",
                                        fontWeight: 600,
                                        cursor: "pointer",
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "0.25rem",
                                        color: item.isPinned ? "var(--navy)" : "var(--text-muted)",
                                        backgroundColor: item.isPinned ? "rgba(26,54,93,0.06)" : "transparent",
                                      }}
                                      title={item.isPinned ? "Unpin from Matter Focus" : "Pin as Important Evidence"}
                                    >
                                      {item.isPinned ? <PinOff size={12} /> : <Pin size={12} />}
                                      {item.isPinned ? "Pinned" : "Pin"}
                                    </button>

                                    <button
                                      onClick={() => {
                                        setLinkingItem(item);
                                        setTargetIssueId(item.issueId);
                                      }}
                                      style={{
                                        background: "transparent",
                                        border: "1px solid var(--border-rule)",
                                        borderRadius: "2px",
                                        padding: "0.25rem 0.5rem",
                                        fontSize: "0.72rem",
                                        fontWeight: 600,
                                        cursor: "pointer",
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "0.25rem",
                                        color: "var(--text-muted)",
                                      }}
                                      title="Re-link or associate with another matter issue"
                                    >
                                      <Link2 size={12} />
                                      Link
                                    </button>
                                  </div>
                                </div>

                                {/* Verbatim Excerpt Block */}
                                <div
                                  style={{
                                    backgroundColor: "var(--bg-parchment)",
                                    border: "1px solid var(--border-rule)",
                                    borderRadius: "2px",
                                    padding: "1rem 1.25rem",
                                    marginBottom: "1rem",
                                    borderLeft: `3px solid ${isSupporting ? "#10754A" : "#B91C1C"}`,
                                  }}
                                >
                                  <div
                                    style={{
                                      fontSize: "0.68rem",
                                      fontFamily: "var(--font-mono)",
                                      color: "var(--text-faint)",
                                      textTransform: "uppercase",
                                      marginBottom: "0.35rem",
                                      fontWeight: 700,
                                    }}
                                  >
                                    Verbatim Evidence Excerpt:
                                  </div>
                                  <p
                                    style={{
                                      fontFamily: "var(--font-serif)",
                                      fontSize: "0.95rem",
                                      lineHeight: 1.6,
                                      color: "var(--text-ink)",
                                      margin: 0,
                                      fontStyle: "italic",
                                    }}
                                  >
                                    “{item.evidenceExcerpt}”
                                  </p>
                                </div>

                                {/* ── LEVEL 4: SOURCE DOCUMENT & PROVENANCE ── */}
                                <div
                                  style={{
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "space-between",
                                    backgroundColor: "var(--bg-surface)",
                                    padding: "0.7rem 1rem",
                                    borderRadius: "2px",
                                    border: "1px solid var(--border-subtle)",
                                    flexWrap: "wrap",
                                    gap: "0.75rem",
                                  }}
                                >
                                  {/* Spatial coordinates */}
                                  <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                                      <FileText size={13} color="var(--navy)" />
                                      <span
                                        style={{
                                          fontSize: "0.78rem",
                                          fontWeight: 700,
                                          color: "var(--navy)",
                                          fontFamily: "var(--font-mono)",
                                        }}
                                      >
                                        {item.sourceDocument}
                                      </span>
                                    </div>

                                    {(item.pageNumber || item.paragraphId) && (
                                      <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                                        <span style={{ fontSize: "0.74rem", color: "var(--text-faint)" }}>
                                          Location:
                                        </span>
                                        <span
                                          style={{
                                            fontSize: "0.76rem",
                                            fontWeight: 600,
                                            color: "var(--text-ink)",
                                            fontFamily: "var(--font-mono)",
                                          }}
                                        >
                                          {item.pageNumber}
                                          {item.pageNumber && item.paragraphId ? " · " : ""}
                                          {item.paragraphId}
                                        </span>
                                      </div>
                                    )}

                                    {item.relatedAuthority && (
                                      <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                                        <Scale size={13} color="var(--maroon)" />
                                        <span
                                          style={{
                                            fontSize: "0.76rem",
                                            color: "var(--maroon)",
                                            fontWeight: 600,
                                          }}
                                        >
                                          {item.relatedAuthority.caseTitle}{" "}
                                          <span style={{ color: "var(--text-faint)", fontWeight: 400 }}>
                                            ({item.relatedAuthority.court}
                                            {item.relatedAuthority.year ? ` · ${item.relatedAuthority.year}` : ""})
                                          </span>
                                        </span>
                                      </div>
                                    )}
                                  </div>

                                  {/* [Open source] Button */}
                                  <button
                                    onClick={() => setInspectingItem(item)}
                                    style={{
                                      padding: "0.35rem 0.75rem",
                                      fontSize: "0.74rem",
                                      fontWeight: 600,
                                      backgroundColor: "var(--bg-sheet)",
                                      color: "var(--maroon)",
                                      border: "1px solid var(--maroon)",
                                      borderRadius: "2px",
                                      cursor: "pointer",
                                      display: "flex",
                                      alignItems: "center",
                                      gap: "0.35rem",
                                      transition: "all 0.1s ease",
                                    }}
                                  >
                                    <BookOpen size={12} />
                                    <span>Open source</span>
                                    <ExternalLink size={11} />
                                  </button>
                                </div>

                                {/* Lawyer Notes Section */}
                                <div style={{ marginTop: "0.85rem" }}>
                                  {item.notes && item.notes.length > 0 && (
                                    <div
                                      style={{
                                        display: "flex",
                                        flexDirection: "column",
                                        gap: "0.35rem",
                                        marginBottom: "0.5rem",
                                      }}
                                    >
                                      {item.notes.map((note, nIdx) => (
                                        <div
                                          key={nIdx}
                                          style={{
                                            display: "flex",
                                            alignItems: "flex-start",
                                            gap: "0.4rem",
                                            fontSize: "0.76rem",
                                            color: "var(--text-ink)",
                                            backgroundColor: "rgba(0,0,0,0.02)",
                                            padding: "0.4rem 0.65rem",
                                            borderRadius: "2px",
                                            borderLeft: "2px solid var(--brass)",
                                          }}
                                        >
                                          <MessageSquare size={12} color="var(--brass)" style={{ marginTop: "2px" }} />
                                          <span>{note}</span>
                                        </div>
                                      ))}
                                    </div>
                                  )}

                                  {/* Add Note Input / Toggle */}
                                  {isNoteOpen ? (
                                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                                      <input
                                        type="text"
                                        placeholder="Add counsel remark, trial strategy note, or citation reference..."
                                        value={noteDraft}
                                        onChange={(e) => setNoteDraft(e.target.value)}
                                        onKeyDown={(e) => {
                                          if (e.key === "Enter") handleSaveNote(item.id);
                                        }}
                                        autoFocus
                                        style={{
                                          flex: 1,
                                          padding: "0.4rem 0.65rem",
                                          fontSize: "0.76rem",
                                          border: "1px solid var(--border-rule)",
                                          borderRadius: "2px",
                                          backgroundColor: "var(--bg-parchment)",
                                          outline: "none",
                                        }}
                                      />
                                      <button
                                        onClick={() => handleSaveNote(item.id)}
                                        style={{
                                          padding: "0.4rem 0.75rem",
                                          fontSize: "0.74rem",
                                          fontWeight: 600,
                                          backgroundColor: "var(--navy)",
                                          color: "#FFFFFF",
                                          border: "none",
                                          borderRadius: "2px",
                                          cursor: "pointer",
                                        }}
                                      >
                                        Save Note
                                      </button>
                                      <button
                                        onClick={() => {
                                          setActiveNoteItemId(null);
                                          setNoteDraft("");
                                        }}
                                        style={{
                                          padding: "0.4rem 0.5rem",
                                          fontSize: "0.74rem",
                                          background: "transparent",
                                          color: "var(--text-faint)",
                                          border: "none",
                                          cursor: "pointer",
                                        }}
                                      >
                                        Cancel
                                      </button>
                                    </div>
                                  ) : (
                                    <button
                                      onClick={() => {
                                        setActiveNoteItemId(item.id);
                                        setNoteDraft("");
                                      }}
                                      style={{
                                        background: "transparent",
                                        border: "none",
                                        padding: 0,
                                        fontSize: "0.72rem",
                                        color: "var(--text-faint)",
                                        cursor: "pointer",
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "0.25rem",
                                      }}
                                    >
                                      <Plus size={11} />
                                      <span>Add lawyer note</span>
                                    </button>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── MODAL: ORIGINAL SOURCE INSPECTOR ────────────────────────────────────── */}
      {inspectingItem && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.6)",
            backdropFilter: "blur(2px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "1rem",
          }}
          onClick={() => setInspectingItem(null)}
        >
          <div
            className="paper-card"
            style={{
              width: "100%",
              maxWidth: "780px",
              maxHeight: "90vh",
              overflowY: "auto",
              backgroundColor: "var(--bg-sheet)",
              border: "2px solid var(--border-dark)",
              borderRadius: "4px",
              padding: "2rem",
              boxShadow: "0 20px 40px rgba(0,0,0,0.3)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div
              style={{
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                borderBottom: "1.5px solid var(--border-rule)",
                paddingBottom: "1rem",
                marginBottom: "1.25rem",
              }}
            >
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.7rem",
                      fontWeight: 700,
                      backgroundColor: "var(--navy)",
                      color: "#FFFFFF",
                      padding: "0.15rem 0.5rem",
                      borderRadius: "2px",
                    }}
                  >
                    ORIGINAL COURT RECORD
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.72rem",
                      color: "var(--maroon)",
                      fontWeight: 600,
                    }}
                  >
                    {inspectingItem.id}
                  </span>
                </div>
                <h3
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.3rem",
                    fontWeight: 700,
                    color: "var(--text-ink)",
                    margin: 0,
                  }}
                >
                  {inspectingItem.sourceDocument}
                </h3>
              </div>

              <button
                onClick={() => setInspectingItem(null)}
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "var(--text-faint)",
                  padding: "0.25rem",
                }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Document Coordinates Strip */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: "1rem",
                backgroundColor: "var(--bg-surface)",
                padding: "0.85rem 1rem",
                borderRadius: "2px",
                border: "1px solid var(--border-subtle)",
                marginBottom: "1.5rem",
                fontSize: "0.78rem",
              }}
            >
              <div>
                <span style={{ color: "var(--text-faint)", display: "block", marginBottom: "0.2rem" }}>
                  Page Coordinate:
                </span>
                <strong style={{ fontFamily: "var(--font-mono)", color: "var(--text-ink)" }}>
                  {inspectingItem.pageNumber || "Record On File"}
                </strong>
              </div>
              <div>
                <span style={{ color: "var(--text-faint)", display: "block", marginBottom: "0.2rem" }}>
                  Paragraph / Hash:
                </span>
                <strong style={{ fontFamily: "var(--font-mono)", color: "var(--maroon)" }}>
                  {inspectingItem.paragraphId || "PAR_001"}
                </strong>
              </div>
              <div>
                <span style={{ color: "var(--text-faint)", display: "block", marginBottom: "0.2rem" }}>
                  Stance in Matter:
                </span>
                <strong
                  style={{
                    fontFamily: "var(--font-mono)",
                    color: inspectingItem.stance === "supporting" ? "#10754A" : "#B91C1C",
                  }}
                >
                  {inspectingItem.stance === "supporting" ? "Supporting Argument" : "Contradicting Position"}
                </strong>
              </div>
            </div>

            {/* Verbatim Record Content */}
            <div style={{ marginBottom: "1.5rem" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "0.5rem",
                }}
              >
                <span
                  style={{
                    fontSize: "0.74rem",
                    fontWeight: 700,
                    fontFamily: "var(--font-mono)",
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                  }}
                >
                  Verbatim Certified Transcript
                </span>

                <button
                  onClick={() =>
                    handleCopySource(inspectingItem.rawSourceText || inspectingItem.evidenceExcerpt)
                  }
                  style={{
                    background: "transparent",
                    border: "1px solid var(--border-rule)",
                    borderRadius: "2px",
                    padding: "0.25rem 0.5rem",
                    fontSize: "0.72rem",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.25rem",
                    color: "var(--text-muted)",
                  }}
                >
                  {copiedText ? <Check size={12} color="#10754A" /> : <Copy size={12} />}
                  <span>{copiedText ? "Copied" : "Copy Excerpt"}</span>
                </button>
              </div>

              <div
                style={{
                  backgroundColor: "var(--bg-parchment)",
                  border: "1px solid var(--border-rule)",
                  borderRadius: "2px",
                  padding: "1.25rem",
                  fontFamily: "var(--font-serif)",
                  fontSize: "0.95rem",
                  lineHeight: 1.7,
                  color: "var(--text-ink)",
                  whiteSpace: "pre-wrap",
                  maxHeight: "300px",
                  overflowY: "auto",
                }}
              >
                {inspectingItem.rawSourceText || inspectingItem.evidenceExcerpt}
              </div>
            </div>

            {/* Related Judicial Precedent Detail */}
            {inspectingItem.relatedAuthority && (
              <div
                style={{
                  backgroundColor: "rgba(128, 0, 32, 0.04)",
                  border: "1px solid rgba(128, 0, 32, 0.15)",
                  borderRadius: "2px",
                  padding: "1rem",
                  marginBottom: "1.5rem",
                }}
              >
                <div
                  style={{
                    fontSize: "0.7rem",
                    fontFamily: "var(--font-mono)",
                    color: "var(--maroon)",
                    fontWeight: 700,
                    marginBottom: "0.25rem",
                    textTransform: "uppercase",
                  }}
                >
                  Connected Judicial Precedent:
                </div>
                <div style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-ink)", marginBottom: "0.2rem" }}>
                  {inspectingItem.relatedAuthority.caseTitle}
                </div>
                <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                  {inspectingItem.relatedAuthority.court}
                  {inspectingItem.relatedAuthority.year ? ` · ${inspectingItem.relatedAuthority.year}` : ""}
                  {inspectingItem.relatedAuthority.citation ? ` · ${inspectingItem.relatedAuthority.citation}` : ""}
                </div>
              </div>
            )}

            {/* Modal Footer */}
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: "0.75rem",
                borderTop: "1px solid var(--border-subtle)",
                paddingTop: "1rem",
              }}
            >
              <button
                onClick={() => setInspectingItem(null)}
                style={{
                  padding: "0.45rem 1rem",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  backgroundColor: "var(--maroon)",
                  color: "#FFFFFF",
                  border: "none",
                  borderRadius: "3px",
                  cursor: "pointer",
                }}
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL: RE-LINK EVIDENCE TO ANOTHER ISSUE ────────────────────────────── */}
      {linkingItem && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            backdropFilter: "blur(2px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "1rem",
          }}
          onClick={() => setLinkingItem(null)}
        >
          <div
            className="paper-card"
            style={{
              width: "100%",
              maxWidth: "500px",
              backgroundColor: "var(--bg-sheet)",
              border: "1.5px solid var(--border-dark)",
              borderRadius: "4px",
              padding: "1.75rem",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h4
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "1.15rem",
                fontWeight: 700,
                color: "var(--text-ink)",
                margin: "0 0 0.5rem 0",
              }}
            >
              Re-link Evidence to Issue
            </h4>
            <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: "1.25rem", lineHeight: 1.45 }}>
              Assign this evidence excerpt to a different legal issue in this matter:
            </p>

            <div style={{ marginBottom: "1.25rem" }}>
              <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-ink)", display: "block", marginBottom: "0.4rem" }}>
                Select Target Issue:
              </label>
              <select
                value={targetIssueId}
                onChange={(e) => setTargetIssueId(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.5rem 0.75rem",
                  fontSize: "0.84rem",
                  borderRadius: "3px",
                  border: "1px solid var(--border-rule)",
                  backgroundColor: "var(--bg-parchment)",
                  outline: "none",
                }}
              >
                {issues.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.issueNumber ? `${i.issueNumber}: ` : ""}
                    {i.title}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem" }}>
              <button
                onClick={() => setLinkingItem(null)}
                style={{
                  padding: "0.45rem 0.85rem",
                  fontSize: "0.8rem",
                  background: "transparent",
                  border: "1px solid var(--border-rule)",
                  borderRadius: "3px",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmLink}
                style={{
                  padding: "0.45rem 1rem",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  backgroundColor: "var(--navy)",
                  color: "#FFFFFF",
                  border: "none",
                  borderRadius: "3px",
                  cursor: "pointer",
                }}
              >
                Confirm Link
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
