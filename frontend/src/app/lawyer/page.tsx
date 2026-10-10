"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LawyerShell } from "@/components/lawyer/LawyerShell";
import { INITIAL_MATTERS, INITIAL_RECENT_ACTIVITY, INITIAL_UPCOMING_ITEMS } from "@/lib/data/matters";
import { Matter, MatterStage } from "@/lib/types/matter";
import {
  Briefcase,
  Search,
  Plus,
  ArrowRight,
  Clock,
  Calendar,
  FileText,
  AlertCircle,
  CheckCircle2,
  Filter,
  ChevronRight,
  Scale,
  Upload,
  Database,
  RefreshCw,
  Sparkles,
  X,
  FileCheck,
  ShieldCheck,
} from "lucide-react";

interface CloudCase {
  id: string;
  filename: string;
  court: string;
  caseNumberHint: string;
  titleHint: string;
  fileSizeBytes: number;
  preview: string;
  sampleType: string;
}

const STAGES: MatterStage[] = [
  "Filed",
  "Notice",
  "Pleadings",
  "Evidence",
  "Arguments",
  "Judgment",
];

export default function LawyerDashboardPage() {
  const router = useRouter();
  const [matters, setMatters] = useState<Matter[]>(INITIAL_MATTERS);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCourtFilter, setSelectedCourtFilter] = useState("all");
  const [userName, setUserName] = useState("Adv. Rajesh Sharma");

  // Ingestion Modal States
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [intakeTab, setIntakeTab] = useState<"upload" | "cloud">("cloud");
  const [cloudCases, setCloudCases] = useState<CloudCase[]>([]);
  const [selectedCloudCase, setSelectedCloudCase] = useState<CloudCase | null>(null);
  const [selectedFileObj, setSelectedFileObj] = useState<File | null>(null);
  const [uploadedFile, setUploadedFile] = useState<{ name: string; size: string } | null>(null);
  const [clientNameInput, setClientNameInput] = useState("");
  const [customTitleInput, setCustomTitleInput] = useState("");

  // Ingestion progress & result
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestStep, setIngestStep] = useState<number>(0);
  const [createdMatter, setCreatedMatter] = useState<Matter | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load matters dynamically from API
  const refreshMatters = () => {
    fetch("/api/matters")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.matters && data.matters.length > 0) {
          setMatters(data.matters);
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    refreshMatters();

    // Load available repository cases
    fetch("/api/documents/cloud-cases")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.cases) {
          setCloudCases(data.cases);
          if (data.cases.length > 0) setSelectedCloudCase(data.cases[0]);
        }
      })
      .catch(() => {});

    try {
      const stored = localStorage.getItem("vidhik_user");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.name) setUserName(parsed.name);
      }
    } catch (e) {}
  }, []);

  // Handle local file selection with validation
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const lower = file.name.toLowerCase();
    if (!lower.endsWith(".pdf") && !lower.endsWith(".txt")) {
      setIngestError("Only supported court PDF documents (or plain text) can be uploaded.");
      setSelectedFileObj(null);
      setUploadedFile(null);
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setIngestError("File size exceeds 50MB limit. Please upload a smaller document.");
      setSelectedFileObj(null);
      setUploadedFile(null);
      return;
    }

    setIngestError(null);
    setSelectedFileObj(file);
    setUploadedFile({
      name: file.name,
      size: `${(file.size / 1024).toFixed(1)} KB`,
    });
    if (!customTitleInput) {
      setCustomTitleInput(file.name.replace(/\.[^/.]+$/, "").replace(/_/g, " "));
    }
  };

  // Execute End-to-End Ingestion Pipeline
  const handleStartIngestion = async () => {
    if (isIngesting) return; // Prevent duplicate submissions caused by repeated clicks
    setIsIngesting(true);
    setIngestError(null);
    setIngestStep(1);

    try {
      // Step 1: Parsing
      await new Promise((r) => setTimeout(r, 400));
      setIngestStep(2);

      let res: Response;

      if (intakeTab === "cloud" && selectedCloudCase) {
        setIngestStep(3);
        res = await fetch("/api/matters/ingest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            cloudFilename: selectedCloudCase.filename,
            customTitle: customTitleInput.trim() || selectedCloudCase.titleHint,
            clientName: clientNameInput.trim() || undefined,
          }),
        });
      } else if (intakeTab === "upload" && selectedFileObj) {
        setIngestStep(3);
        const formData = new FormData();
        formData.append("file", selectedFileObj);
        if (clientNameInput.trim()) formData.append("clientName", clientNameInput.trim());
        if (customTitleInput.trim()) formData.append("customTitle", customTitleInput.trim());

        res = await fetch("/api/matters/ingest", {
          method: "POST",
          body: formData,
        });
      } else {
        throw new Error("Please select a cloud case or upload a local document file.");
      }

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.error || "Ingestion and intelligence pipeline failed");
      }

      const data = await res.json();
      setIngestStep(4);
      await new Promise((r) => setTimeout(r, 400));

      setCreatedMatter(data.matter);
      refreshMatters();
    } catch (err: any) {
      console.error(err);
      setIngestError(err.message || "Failed to ingest matter");
      setIngestStep(0);
    } finally {
      setIsIngesting(false);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setCreatedMatter(null);
    setIngestError(null);
    setIngestStep(0);
    setSelectedFileObj(null);
    setUploadedFile(null);
    setCustomTitleInput("");
    setClientNameInput("");
  };


  const filteredMatters = matters.filter((m) => {
    const matchesQuery =
      m.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.caseNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.court.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCourt =
      selectedCourtFilter === "all" ||
      m.court.toLowerCase().includes(selectedCourtFilter.toLowerCase());
    return matchesQuery && matchesCourt;
  });

  return (
    <LawyerShell>
      <div style={{ maxWidth: "1240px", margin: "0 auto", paddingBottom: "4rem" }}>
        {/* ===================================================================
            HEADER: PROFESSIONAL GREETING & CONTEXT + ADD MATTER BUTTON
            =================================================================== */}
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            marginBottom: "2.5rem",
            flexWrap: "wrap",
            gap: "1.5rem",
          }}
        >
          <div>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.4rem",
                fontSize: "0.72rem",
                fontFamily: "var(--font-mono)",
                fontWeight: 700,
                color: "var(--maroon)",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                marginBottom: "0.5rem",
              }}
            >
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  backgroundColor: "var(--maroon)",
                  display: "inline-block",
                }}
              />
              <span>MATTER-CENTRIC INTELLIGENCE WORKSPACE</span>
            </div>

            <h1
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "2.35rem",
                fontWeight: 700,
                color: "var(--text-ink)",
                letterSpacing: "-0.015em",
                marginBottom: "0.4rem",
              }}
            >
              Good morning, {userName}
            </h1>

            <p
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "1.05rem",
                color: "var(--text-muted)",
                maxWidth: "600px",
                margin: 0,
              }}
            >
              Your matters, verified evidence provenance, and recent legal work in one place.
            </p>
          </div>

          {/* Action: "+ Add New Matter" */}
          <button
            onClick={() => setIsModalOpen(true)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.75rem 1.35rem",
              fontSize: "0.88rem",
              fontWeight: 700,
              backgroundColor: "var(--maroon)",
              color: "#FFFFFF",
              border: "none",
              borderRadius: "3px",
              cursor: "pointer",
              boxShadow: "0 2px 6px rgba(128, 0, 32, 0.2)",
              transition: "all 0.15s ease",
            }}
          >
            <Plus size={16} />
            <span>Add New Matter</span>
          </button>
        </div>

        {/* ===================================================================
            OVERVIEW METRICS
            =================================================================== */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "1.5rem",
            marginBottom: "3rem",
          }}
          className="metrics-grid"
        >
          <div
            className="paper-card"
            style={{
              padding: "1.35rem 1.5rem",
              backgroundColor: "var(--bg-sheet)",
              borderRadius: "3px",
            }}
          >
            <div
              style={{
                fontSize: "0.72rem",
                fontFamily: "var(--font-sans)",
                fontWeight: 600,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: "0.35rem",
              }}
            >
              Active Matters
            </div>
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "2.1rem",
                fontWeight: 700,
                color: "var(--navy)",
              }}
            >
              {matters.length}
            </div>
            <div style={{ fontSize: "0.74rem", color: "var(--text-faint)", marginTop: "0.2rem" }}>
              High Court, Supreme Court & Appellate
            </div>
          </div>

          <div
            className="paper-card"
            style={{
              padding: "1.35rem 1.5rem",
              backgroundColor: "var(--bg-sheet)",
              borderRadius: "3px",
            }}
          >
            <div
              style={{
                fontSize: "0.72rem",
                fontFamily: "var(--font-sans)",
                fontWeight: 600,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: "0.35rem",
              }}
            >
              Recently Updated
            </div>
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "2.1rem",
                fontWeight: 700,
                color: "var(--maroon)",
              }}
            >
              3
            </div>
            <div style={{ fontSize: "0.74rem", color: "var(--text-faint)", marginTop: "0.2rem" }}>
              Submissions filed in past 48h
            </div>
          </div>

          <div
            className="paper-card"
            style={{
              padding: "1.35rem 1.5rem",
              backgroundColor: "var(--bg-sheet)",
              borderRadius: "3px",
            }}
          >
            <div
              style={{
                fontSize: "0.72rem",
                fontFamily: "var(--font-sans)",
                fontWeight: 600,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: "0.35rem",
              }}
            >
              Indexed Documents
            </div>
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "2.1rem",
                fontWeight: 700,
                color: "var(--navy)",
              }}
            >
              29,156+
            </div>
            <div style={{ fontSize: "0.74rem", color: "var(--text-faint)", marginTop: "0.2rem" }}>
              Hierarchically parsed & RAG indexed
            </div>
          </div>

          <div
            className="paper-card"
            style={{
              padding: "1.35rem 1.5rem",
              backgroundColor: "var(--bg-sheet)",
              borderRadius: "3px",
            }}
          >
            <div
              style={{
                fontSize: "0.72rem",
                fontFamily: "var(--font-sans)",
                fontWeight: 600,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: "0.35rem",
              }}
            >
              Upcoming Items
            </div>
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: "2.1rem",
                fontWeight: 700,
                color: "var(--brass)",
              }}
            >
              4
            </div>
            <div style={{ fontSize: "0.74rem", color: "var(--text-faint)", marginTop: "0.2rem" }}>
              Hearings & statutory deadlines
            </div>
          </div>
        </div>

        {/* ===================================================================
            TWO-COLUMN MAIN SECTION
            =================================================================== */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.9fr 1.1fr",
            gap: "2.5rem",
          }}
          className="research-breakdown-grid"
        >
          {/* COLUMN 1: MY MATTERS */}
          <div>
            {/* Header + Search/Filters */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "1.5rem",
                flexWrap: "wrap",
                gap: "1rem",
              }}
            >
              <h2
                style={{
                  fontFamily: "var(--font-serif)",
                  fontSize: "1.55rem",
                  fontWeight: 700,
                  color: "var(--text-ink)",
                  margin: 0,
                }}
              >
                My Matters ({matters.length})
              </h2>

              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <div style={{ position: "relative" }}>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search matters, case no..."
                    style={{
                      padding: "0.45rem 0.75rem 0.45rem 2rem",
                      fontSize: "0.82rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      backgroundColor: "var(--bg-sheet)",
                      color: "var(--text-ink)",
                      width: "210px",
                    }}
                  />
                  <Search
                    size={14}
                    color="var(--text-faint)"
                    style={{
                      position: "absolute",
                      left: "0.65rem",
                      top: "50%",
                      transform: "translateY(-50%)",
                    }}
                  />
                </div>

                <select
                  value={selectedCourtFilter}
                  onChange={(e) => setSelectedCourtFilter(e.target.value)}
                  style={{
                    padding: "0.45rem 0.75rem",
                    fontSize: "0.82rem",
                    border: "1px solid var(--border-rule)",
                    borderRadius: "2px",
                    backgroundColor: "var(--bg-sheet)",
                    color: "var(--text-ink)",
                  }}
                >
                  <option value="all">All Courts</option>
                  <option value="delhi">Delhi High Court</option>
                  <option value="karnataka">Karnataka High Court</option>
                  <option value="bombay">Bombay High Court</option>
                  <option value="madras">Madras High Court</option>
                  <option value="supreme">Supreme Court</option>
                </select>
              </div>
            </div>

            {/* List of Matter Cards */}
            <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              {filteredMatters.map((matter) => (
                <div
                  key={matter.id}
                  className="paper-card"
                  style={{
                    padding: "1.75rem",
                    backgroundColor: "var(--bg-sheet)",
                    borderRadius: "3px",
                    cursor: "pointer",
                    position: "relative",
                  }}
                  onClick={() => router.push(`/lawyer/matters/${matter.id}`)}
                >
                  {/* Top Bar: Court & Status Tag */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: "0.75rem",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                      <span
                        style={{
                          fontSize: "0.72rem",
                          fontFamily: "var(--font-mono)",
                          fontWeight: 700,
                          color: "var(--maroon)",
                          backgroundColor: "var(--maroon-faint)",
                          padding: "0.15rem 0.5rem",
                          borderRadius: "2px",
                          border: "1px solid var(--maroon-border)",
                        }}
                      >
                        {matter.caseNumber}
                      </span>
                      <span
                        style={{
                          fontSize: "0.76rem",
                          color: "var(--navy)",
                          fontWeight: 600,
                        }}
                      >
                        {matter.court}
                      </span>
                    </div>

                    <span
                      style={{
                        fontSize: "0.72rem",
                        color: "var(--text-faint)",
                      }}
                    >
                      Updated {matter.updatedAt}
                    </span>
                  </div>

                  {/* Matter Title */}
                  <h3
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontSize: "1.28rem",
                      fontWeight: 700,
                      color: "var(--text-ink)",
                      marginBottom: "0.6rem",
                      lineHeight: 1.3,
                    }}
                  >
                    {matter.title}
                  </h3>

                  {/* Matter Summary preview */}
                  <p
                    style={{
                      fontFamily: "var(--font-sans)",
                      fontSize: "0.85rem",
                      lineHeight: 1.55,
                      color: "var(--text-muted)",
                      marginBottom: "1.25rem",
                      display: "-webkit-box",
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                    }}
                  >
                    {matter.summary}
                  </p>

                  {/* Status Progression Track */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.35rem",
                      padding: "0.6rem 0.85rem",
                      backgroundColor: "var(--bg-parchment)",
                      borderRadius: "2px",
                      border: "1px solid var(--border-subtle)",
                      marginBottom: "1.25rem",
                    }}
                  >
                    {STAGES.map((stg, i) => {
                      const isCurrent = stg === matter.status;
                      const isPassed =
                        STAGES.indexOf(matter.status) > STAGES.indexOf(stg);

                      return (
                        <React.Fragment key={stg}>
                          <div
                            style={{
                              fontSize: "0.7rem",
                              fontFamily: "var(--font-sans)",
                              fontWeight: isCurrent ? 700 : 500,
                              color: isCurrent
                                ? "var(--maroon)"
                                : isPassed
                                ? "var(--navy)"
                                : "var(--text-faint)",
                              display: "flex",
                              alignItems: "center",
                              gap: "0.25rem",
                            }}
                          >
                            <span
                              style={{
                                width: "6px",
                                height: "6px",
                                borderRadius: "50%",
                                backgroundColor: isCurrent
                                  ? "var(--maroon)"
                                  : isPassed
                                  ? "var(--navy)"
                                  : "var(--border-rule)",
                              }}
                            />
                            <span>{stg}</span>
                          </div>
                          {i < STAGES.length - 1 && (
                            <span
                              style={{
                                color: "var(--border-rule)",
                                fontSize: "0.65rem",
                              }}
                            >
                              →
                            </span>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </div>

                  {/* Bottom Footer: Next Event & Action */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      paddingTop: "0.85rem",
                      borderTop: "1px solid var(--border-subtle)",
                      fontSize: "0.78rem",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                      <span style={{ fontWeight: 600, color: "var(--text-ink)" }}>
                        Next:
                      </span>
                      <span style={{ color: "var(--navy)" }}>
                        {matter.nextImportantEvent}
                      </span>
                    </div>

                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.3rem",
                        color: "var(--maroon)",
                        fontWeight: 600,
                      }}
                    >
                      <span>Open Workspace</span>
                      <ArrowRight size={13} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* COLUMN 2: RECENT ACTIVITY & UPCOMING ITEMS */}
          <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
            {/* Upcoming Deadlines Widget */}
            <div
              className="paper-card"
              style={{
                padding: "1.75rem",
                backgroundColor: "var(--bg-sheet)",
                borderRadius: "3px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "1.25rem",
                }}
              >
                <h3
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.2rem",
                    fontWeight: 700,
                    color: "var(--text-ink)",
                    margin: 0,
                  }}
                >
                  Upcoming Deadlines
                </h3>
                <Calendar size={16} color="var(--maroon)" />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {INITIAL_UPCOMING_ITEMS.map((item) => (
                  <div
                    key={item.id}
                    style={{
                      padding: "0.85rem",
                      backgroundColor: "var(--bg-parchment)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "2px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "0.25rem",
                      cursor: "pointer",
                    }}
                    onClick={() => router.push(`/lawyer/matters/${item.matterId}`)}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                      }}
                    >
                      <span
                        style={{
                          fontSize: "0.78rem",
                          fontWeight: 700,
                          color: "var(--maroon)",
                          fontFamily: "var(--font-mono)",
                        }}
                      >
                        {item.date}
                      </span>
                      <span
                        style={{
                          fontSize: "0.68rem",
                          color: "var(--navy)",
                          textTransform: "uppercase",
                          fontWeight: 600,
                        }}
                      >
                        {item.type}
                      </span>
                    </div>

                    <div
                      style={{
                        fontSize: "0.85rem",
                        fontWeight: 600,
                        color: "var(--text-ink)",
                      }}
                    >
                      {item.title}
                    </div>

                    <div
                      style={{
                        fontSize: "0.72rem",
                        color: "var(--text-muted)",
                      }}
                    >
                      {item.matterTitle} • {item.court}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Activity Feed */}
            <div
              className="paper-card"
              style={{
                padding: "1.75rem",
                backgroundColor: "var(--bg-sheet)",
                borderRadius: "3px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "1.25rem",
                }}
              >
                <h3
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.2rem",
                    fontWeight: 700,
                    color: "var(--text-ink)",
                    margin: 0,
                  }}
                >
                  Recent Activity
                </h3>
                <Clock size={16} color="var(--navy)" />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {INITIAL_RECENT_ACTIVITY.map((act) => (
                  <div
                    key={act.id}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "0.65rem",
                      paddingBottom: "0.85rem",
                      borderBottom: "1px solid var(--border-subtle)",
                    }}
                  >
                    <div
                      style={{
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        backgroundColor: "var(--maroon)",
                        marginTop: "5px",
                        flexShrink: 0,
                      }}
                    />
                    <div style={{ flex: 1 }}>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          fontSize: "0.72rem",
                          color: "var(--text-faint)",
                          marginBottom: "0.15rem",
                        }}
                      >
                        <span style={{ fontWeight: 600, color: "var(--navy)" }}>
                          {act.title}
                        </span>
                        <span>{act.timestamp}</span>
                      </div>
                      <div
                        style={{
                          fontSize: "0.82rem",
                          color: "var(--text-ink)",
                          lineHeight: 1.4,
                        }}
                      >
                        {act.detail}
                      </div>
                      <div
                        style={{
                          fontSize: "0.72rem",
                          color: "var(--maroon)",
                          marginTop: "0.2rem",
                          cursor: "pointer",
                        }}
                        onClick={() => router.push(`/lawyer/matters/${act.matterId}`)}
                      >
                        {act.matterTitle} →
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ===================================================================
          MODAL: ADD NEW MATTER (UPLOAD OR CLOUD REPOSITORY INGESTION)
          =================================================================== */}
      {isModalOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.65)",
            backdropFilter: "blur(3px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "1rem",
          }}
          onClick={handleCloseModal}
        >
          <div
            className="paper-card"
            style={{
              width: "100%",
              maxWidth: "760px",
              maxHeight: "92vh",
              overflowY: "auto",
              backgroundColor: "var(--bg-sheet)",
              border: "2px solid var(--border-dark)",
              borderRadius: "4px",
              padding: "2rem",
              boxShadow: "0 20px 40px rgba(0,0,0,0.35)",
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
                marginBottom: "1.5rem",
              }}
            >
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.7rem",
                      fontWeight: 700,
                      backgroundColor: "var(--maroon)",
                      color: "#FFFFFF",
                      padding: "0.15rem 0.5rem",
                      borderRadius: "2px",
                    }}
                  >
                    NEURAL MATTER INTAKE
                  </span>
                  <span style={{ fontSize: "0.72rem", color: "var(--navy)", fontWeight: 600 }}>
                    Auto-ingested into RAG & Synthesized by Gemini
                  </span>
                </div>
                <h3
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.45rem",
                    fontWeight: 700,
                    color: "var(--text-ink)",
                    margin: 0,
                  }}
                >
                  Add Legal Matter / Case File
                </h3>
              </div>

              {!isIngesting && (
                <button
                  onClick={handleCloseModal}
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
              )}
            </div>

            {/* If Matter has been successfully created */}
            {createdMatter ? (
              <div style={{ textAlign: "center", padding: "1.5rem 0" }}>
                <div
                  style={{
                    width: "56px",
                    height: "56px",
                    borderRadius: "50%",
                    backgroundColor: "#EBF7F0",
                    border: "2px solid #10754A",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    margin: "0 auto 1.25rem auto",
                  }}
                >
                  <CheckCircle2 size={32} color="#10754A" />
                </div>

                <h3
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.35rem",
                    fontWeight: 700,
                    color: "var(--text-ink)",
                    marginBottom: "0.4rem",
                  }}
                >
                  Matter Ingested & Workspace Ready
                </h3>

                <p style={{ fontSize: "0.86rem", color: "var(--text-muted)", maxWidth: "520px", margin: "0 auto 1.5rem auto" }}>
                  The case record has been ingested into Vidhik RAG and fully analyzed by Gemini. Key issues, timeline, statutory sections, authorities, and evidence map are activated.
                </p>

                {/* Summary Card */}
                <div
                  style={{
                    backgroundColor: "var(--bg-parchment)",
                    border: "1.5px solid var(--border-rule)",
                    borderRadius: "3px",
                    padding: "1.25rem",
                    textAlign: "left",
                    marginBottom: "2rem",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--maroon)", fontWeight: 700 }}>
                      {createdMatter.caseNumber}
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "var(--navy)", fontWeight: 600 }}>
                      {createdMatter.court}
                    </span>
                  </div>
                  <h4 style={{ fontFamily: "var(--font-serif)", fontSize: "1.1rem", fontWeight: 700, color: "var(--text-ink)", margin: "0 0 0.5rem 0" }}>
                    {createdMatter.title}
                  </h4>
                  <div style={{ display: "flex", gap: "1rem", fontSize: "0.78rem", color: "var(--text-muted)" }}>
                    <span>Issues Identified: <strong>{createdMatter.issues.length}</strong></span>
                    <span>Evidence Items: <strong>{createdMatter.evidence?.length || 0}</strong></span>
                    <span>Authorities Cited: <strong>{createdMatter.authorities.length}</strong></span>
                  </div>
                </div>

                <div style={{ display: "flex", justifyContent: "center", gap: "1rem" }}>
                  <button
                    onClick={handleCloseModal}
                    style={{
                      padding: "0.6rem 1.25rem",
                      fontSize: "0.85rem",
                      backgroundColor: "transparent",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "3px",
                      cursor: "pointer",
                      fontWeight: 600,
                    }}
                  >
                    Back to Dashboard
                  </button>
                  <button
                    onClick={() => router.push(`/lawyer/matters/${createdMatter.id}`)}
                    style={{
                      padding: "0.6rem 1.5rem",
                      fontSize: "0.85rem",
                      fontWeight: 700,
                      backgroundColor: "var(--maroon)",
                      color: "#FFFFFF",
                      border: "none",
                      borderRadius: "3px",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                    }}
                  >
                    <span>Open Matter Workspace</span>
                    <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            ) : isIngesting ? (
              /* Ongoing Ingestion Progress View */
              <div style={{ padding: "2rem 1rem", textAlign: "center" }}>
                <RefreshCw size={36} color="var(--maroon)" className="animate-spin" style={{ margin: "0 auto 1.5rem auto" }} />
                <h4 style={{ fontFamily: "var(--font-serif)", fontSize: "1.25rem", color: "var(--text-ink)", marginBottom: "0.5rem" }}>
                  Ingesting Document into Vidhik Legal Workspace...
                </h4>
                <p style={{ fontSize: "0.84rem", color: "var(--text-muted)", maxWidth: "460px", margin: "0 auto 2rem auto" }}>
                  Processing certified court record, indexing chunks into RAG intelligence, and executing multi-factor Gemini legal analysis.
                </p>

                {/* Progress Steps */}
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxWidth: "480px", margin: "0 auto", textAlign: "left" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", fontSize: "0.82rem" }}>
                    {ingestStep >= 1 ? <CheckCircle2 size={16} color="#10754A" /> : <Clock size={16} color="var(--text-faint)" />}
                    <span style={{ fontWeight: ingestStep === 1 ? 700 : 500, color: ingestStep >= 1 ? "var(--text-ink)" : "var(--text-faint)" }}>
                      1. Parsing certified document text & metadata
                    </span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", fontSize: "0.82rem" }}>
                    {ingestStep >= 2 ? <CheckCircle2 size={16} color="#10754A" /> : <Clock size={16} color="var(--text-faint)" />}
                    <span style={{ fontWeight: ingestStep === 2 ? 700 : 500, color: ingestStep >= 2 ? "var(--text-ink)" : "var(--text-faint)" }}>
                      2. Chunking & registering in Vidhik RAG database
                    </span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", fontSize: "0.82rem" }}>
                    {ingestStep >= 3 ? <CheckCircle2 size={16} color="#10754A" /> : <Clock size={16} color="var(--text-faint)" />}
                    <span style={{ fontWeight: ingestStep === 3 ? 700 : 500, color: ingestStep >= 3 ? "var(--text-ink)" : "var(--text-faint)" }}>
                      3. Gemini Intelligence: Extracting issues, timeline, and sections
                    </span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", fontSize: "0.82rem" }}>
                    {ingestStep >= 4 ? <CheckCircle2 size={16} color="#10754A" /> : <Clock size={16} color="var(--text-faint)" />}
                    <span style={{ fontWeight: ingestStep === 4 ? 700 : 500, color: ingestStep >= 4 ? "var(--text-ink)" : "var(--text-faint)" }}>
                      4. Synthesizing Evidence Map & Authority citations
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              /* Modal Intake Selection Form */
              <div>
                {/* Intake Source Switcher */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "0.75rem",
                    marginBottom: "1.5rem",
                  }}
                >
                  <button
                    onClick={() => setIntakeTab("cloud")}
                    style={{
                      padding: "0.75rem",
                      borderRadius: "3px",
                      border: `1.5px solid ${intakeTab === "cloud" ? "var(--maroon)" : "var(--border-rule)"}`,
                      backgroundColor: intakeTab === "cloud" ? "var(--maroon-faint)" : "var(--bg-sheet)",
                      color: intakeTab === "cloud" ? "var(--maroon)" : "var(--text-ink)",
                      fontWeight: 700,
                      fontSize: "0.85rem",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "0.4rem",
                    }}
                  >
                    <Database size={15} />
                    <span>Import from Judicial Cloud DB</span>
                  </button>

                  <button
                    onClick={() => setIntakeTab("upload")}
                    style={{
                      padding: "0.75rem",
                      borderRadius: "3px",
                      border: `1.5px solid ${intakeTab === "upload" ? "var(--maroon)" : "var(--border-rule)"}`,
                      backgroundColor: intakeTab === "upload" ? "var(--maroon-faint)" : "var(--bg-sheet)",
                      color: intakeTab === "upload" ? "var(--maroon)" : "var(--text-ink)",
                      fontWeight: 700,
                      fontSize: "0.85rem",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "0.4rem",
                    }}
                  >
                    <Upload size={15} />
                    <span>Upload from Local Device</span>
                  </button>
                </div>

                {/* Option 1: Cloud Repository Selection */}
                {intakeTab === "cloud" && (
                  <div style={{ marginBottom: "1.5rem" }}>
                    <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.6rem" }}>
                      Select Real Court Case from Vidhik Judicial Database:
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem", maxHeight: "250px", overflowY: "auto", paddingRight: "0.25rem" }}>
                      {cloudCases.map((c) => {
                        const isSelected = selectedCloudCase?.id === c.id;
                        return (
                          <div
                            key={c.id}
                            onClick={() => setSelectedCloudCase(c)}
                            style={{
                              padding: "0.85rem 1rem",
                              backgroundColor: isSelected ? "var(--maroon-faint)" : "var(--bg-parchment)",
                              border: `1.5px solid ${isSelected ? "var(--maroon)" : "var(--border-rule)"}`,
                              borderRadius: "3px",
                              cursor: "pointer",
                              transition: "all 0.1s ease",
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
                              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: isSelected ? "var(--maroon)" : "var(--navy)", fontWeight: 700 }}>
                                {c.caseNumberHint}
                              </span>
                              <span style={{ fontSize: "0.7rem", color: "var(--text-faint)", fontFamily: "var(--font-mono)" }}>
                                {(c.fileSizeBytes / 1024).toFixed(0)} KB • {c.court}
                              </span>
                            </div>

                            <div style={{ fontSize: "0.88rem", fontWeight: 700, color: "var(--text-ink)", marginBottom: "0.3rem" }}>
                              {c.titleHint}
                            </div>

                            <div style={{ fontSize: "0.76rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                              {c.preview}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Option 2: Upload from Local Device */}
                {intakeTab === "upload" && (
                  <div style={{ marginBottom: "1.5rem" }}>
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileChange}
                      accept=".txt,.pdf,.docx,.odt"
                      style={{ display: "none" }}
                    />

                    <div
                      onClick={() => fileInputRef.current?.click()}
                      style={{
                        padding: "2.5rem 1.5rem",
                        border: "2px dashed var(--border-dark)",
                        borderRadius: "3px",
                        backgroundColor: "var(--bg-parchment)",
                        textAlign: "center",
                        cursor: "pointer",
                      }}
                    >
                      <Upload size={32} color="var(--maroon)" style={{ margin: "0 auto 0.75rem auto" }} />
                      <div style={{ fontSize: "0.92rem", fontWeight: 700, color: "var(--text-ink)", marginBottom: "0.25rem" }}>
                        Click to select case file from your computer
                      </div>
                      <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                        Supports .txt, .pdf, .docx, .odt (Court Orders, Petitions, Pleadings)
                      </div>

                      {uploadedFile && (
                        <div
                          style={{
                            marginTop: "1rem",
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "0.5rem",
                            padding: "0.4rem 0.85rem",
                            backgroundColor: "var(--bg-sheet)",
                            border: "1px solid var(--border-rule)",
                            borderRadius: "2px",
                            fontSize: "0.8rem",
                            fontWeight: 600,
                            color: "var(--navy)",
                          }}
                        >
                          <FileText size={14} />
                          <span>{uploadedFile.name} ({uploadedFile.size})</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Optional Client / Title Fields */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
                  <div>
                    <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-ink)", display: "block", marginBottom: "0.3rem" }}>
                      Client Name (Optional):
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Chintels India Ltd."
                      value={clientNameInput}
                      onChange={(e) => setClientNameInput(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "0.5rem 0.75rem",
                        fontSize: "0.82rem",
                        border: "1px solid var(--border-rule)",
                        borderRadius: "2px",
                        backgroundColor: "var(--bg-sheet)",
                        outline: "none",
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-ink)", display: "block", marginBottom: "0.3rem" }}>
                      Matter Title Override (Optional):
                    </label>
                    <input
                      type="text"
                      placeholder="Leave blank for auto-extraction"
                      value={customTitleInput}
                      onChange={(e) => setCustomTitleInput(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "0.5rem 0.75rem",
                        fontSize: "0.82rem",
                        border: "1px solid var(--border-rule)",
                        borderRadius: "2px",
                        backgroundColor: "var(--bg-sheet)",
                        outline: "none",
                      }}
                    />
                  </div>
                </div>

                {/* Error Banner */}
                {ingestError && (
                  <div
                    style={{
                      padding: "0.6rem 0.85rem",
                      backgroundColor: "#FEF2F2",
                      border: "1px solid #FECACA",
                      borderRadius: "3px",
                      color: "#B91C1C",
                      fontSize: "0.8rem",
                      marginBottom: "1rem",
                    }}
                  >
                    {ingestError}
                  </div>
                )}

                {/* Modal Footer Actions */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-end",
                    gap: "0.75rem",
                    borderTop: "1px solid var(--border-subtle)",
                    paddingTop: "1.25rem",
                  }}
                >
                  <button
                    onClick={handleCloseModal}
                    style={{
                      padding: "0.55rem 1.15rem",
                      fontSize: "0.82rem",
                      backgroundColor: "transparent",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "3px",
                      cursor: "pointer",
                      fontWeight: 600,
                    }}
                  >
                    Cancel
                  </button>

                  <button
                    onClick={handleStartIngestion}
                    disabled={isIngesting || (intakeTab === "upload" && !uploadedFile)}
                    style={{
                      padding: "0.55rem 1.35rem",
                      fontSize: "0.82rem",
                      fontWeight: 700,
                      backgroundColor:
                        isIngesting || (intakeTab === "upload" && !uploadedFile)
                          ? "var(--bg-surface)"
                          : "var(--maroon)",
                      color:
                        isIngesting || (intakeTab === "upload" && !uploadedFile)
                          ? "var(--text-faint)"
                          : "#FFFFFF",
                      border: "none",
                      borderRadius: "3px",
                      cursor:
                        isIngesting || (intakeTab === "upload" && !uploadedFile)
                          ? "not-allowed"
                          : "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.4rem",
                    }}
                  >
                    <Sparkles size={14} />
                    <span>Start Ingestion & Analysis</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </LawyerShell>
  );
}
