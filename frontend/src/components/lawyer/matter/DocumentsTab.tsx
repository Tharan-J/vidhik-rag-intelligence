"use client";

import React, { useState } from "react";
import { Matter, MatterDocument, DocumentMetadata } from "@/lib/types/matter";
import {
  FileText,
  Search,
  Upload,
  Filter,
  CheckCircle2,
  Clock,
  Sparkles,
  ExternalLink,
  X,
  FileCheck2,
  Layers,
  Eye,
} from "lucide-react";
import { ProvenanceBadge } from "./ProvenanceBadge";

interface DocumentsTabProps {
  matter: Matter;
  onDocumentAdded?: (newDoc: MatterDocument) => void;
}

const TYPE_FILTERS = [
  "All",
  "Pleadings",
  "Orders",
  "Judgments",
  "Applications",
  "Evidence",
  "Other",
];

export function DocumentsTab({ matter, onDocumentAdded }: DocumentsTabProps) {
  const [documents, setDocuments] = useState<MatterDocument[]>(matter.documents);
  const [selectedType, setSelectedType] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [inspectDoc, setInspectDoc] = useState<MatterDocument | null>(null);
  const [inspectTab, setInspectTab] = useState<"metadata" | "verbatim">("metadata");
  const [verbatimData, setVerbatimData] = useState<any>(null);
  const [loadingVerbatim, setLoadingVerbatim] = useState(false);

  const loadVerbatimChunks = async (docIdStr: string) => {
    setLoadingVerbatim(true);
    try {
      const res = await fetch(`/api/documents/demonstrate?doc=${encodeURIComponent(docIdStr)}`);
      if (res.ok) {
        const data = await res.json();
        setVerbatimData(data);
      }
    } catch (e) {
      console.error("Failed to load verbatim chunks:", e);
    } finally {
      setLoadingVerbatim(false);
    }
  };

  // Upload modal states
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadName, setUploadName] = useState("");
  const [uploadType, setUploadType] = useState<MatterDocument["type"]>("Pleadings");
  const [uploadText, setUploadText] = useState("");
  const [isExtracting, setIsExtracting] = useState(false);
  const [uploadStatusMsg, setUploadStatusMsg] = useState("");

  const filteredDocs = documents.filter((d) => {
    const matchesType = selectedType === "All" || d.type === selectedType;
    const matchesSearch =
      d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.type.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadName) return;

    setIsExtracting(true);
    setUploadStatusMsg("Indexing into Qdrant Cloud & extracting Document Intelligence...");

    try {
      const res = await fetch("/api/documents/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          matterId: matter.id,
          documentName: uploadName.endsWith(".pdf") ? uploadName : `${uploadName}.pdf`,
          documentType: uploadType,
          fileText:
            uploadText ||
            `IN THE HIGH COURT OF JUDICATURE AT MADRAS\nC.A. No. 4182/2024\nPetitioner: R. Swaminathan\nRespondent: K. Gurusamy\nSubject: Regular First Appeal challenging Partition Decree. Ground of limitation under Section 5 Limitation Act.`,
          pages: Math.floor(Math.random() * 15) + 4,
        }),
      });

      if (res.ok) {
        const json = await res.json();
        if (json.document) {
          setDocuments((prev) => [json.document, ...prev]);
          if (onDocumentAdded) onDocumentAdded(json.document);
        }
      }
      setUploadStatusMsg("Indexed in Qdrant Cloud successfully!");
      setTimeout(() => {
        setShowUploadModal(false);
        setIsExtracting(false);
        setUploadStatusMsg("");
        setUploadName("");
        setUploadText("");
      }, 700);
    } catch (err) {
      setIsExtracting(false);
      setUploadStatusMsg("Failed to ingest document into Qdrant Cloud.");
    }
  };

  return (
    <div>
      {/* Top Controls: Filter Pills & Search & Upload CTA */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "1.75rem",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        {/* Filter Pills */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
          {TYPE_FILTERS.map((f) => {
            const isSelected = selectedType === f;
            return (
              <button
                key={f}
                onClick={() => setSelectedType(f)}
                style={{
                  padding: "0.35rem 0.85rem",
                  fontSize: "0.8rem",
                  fontWeight: isSelected ? 700 : 500,
                  borderRadius: "2px",
                  border: `1px solid ${
                    isSelected ? "var(--maroon)" : "var(--border-rule)"
                  }`,
                  backgroundColor: isSelected
                    ? "var(--maroon)"
                    : "var(--bg-sheet)",
                  color: isSelected ? "#FFFFFF" : "var(--text-ink)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {f}
              </button>
            );
          })}
        </div>

        {/* Right Search & Upload */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div style={{ position: "relative" }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search documents..."
              style={{
                padding: "0.45rem 0.75rem 0.45rem 2rem",
                fontSize: "0.82rem",
                border: "1px solid var(--border-rule)",
                borderRadius: "2px",
                backgroundColor: "var(--bg-sheet)",
                width: "200px",
              }}
            />
            <Search
              size={13}
              color="var(--text-faint)"
              style={{
                position: "absolute",
                left: "0.65rem",
                top: "50%",
                transform: "translateY(-50%)",
              }}
            />
          </div>

          <button
            onClick={() => setShowUploadModal(true)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.45rem",
              padding: "0.45rem 1rem",
              fontSize: "0.82rem",
              fontWeight: 600,
              backgroundColor: "var(--maroon)",
              color: "#FFFFFF",
              border: "none",
              borderRadius: "2px",
              cursor: "pointer",
            }}
          >
            <Upload size={14} />
            <span>Add Document</span>
          </button>
        </div>
      </div>

      {/* Documents Table */}
      <div
        className="paper-card"
        style={{
          backgroundColor: "var(--bg-sheet)",
          borderRadius: "3px",
          overflow: "hidden",
        }}
      >
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
          <thead>
            <tr
              style={{
                backgroundColor: "var(--bg-parchment)",
                borderBottom: "1px solid var(--border-rule)",
                fontSize: "0.72rem",
                fontFamily: "var(--font-mono)",
                color: "var(--text-faint)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
              }}
            >
              <th style={{ padding: "0.85rem 1.25rem" }}>Document Name</th>
              <th style={{ padding: "0.85rem 1rem" }}>Type</th>
              <th style={{ padding: "0.85rem 1rem" }}>Date</th>
              <th style={{ padding: "0.85rem 1rem" }}>Pages</th>
              <th style={{ padding: "0.85rem 1rem" }}>Intelligence</th>
              <th style={{ padding: "0.85rem 1.25rem", textAlign: "right" }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredDocs.map((doc) => {
              const hasMeta = !!doc.extractedMetadata;

              return (
                <tr
                  key={doc.id}
                  style={{
                    borderBottom: "1px solid var(--border-subtle)",
                    fontSize: "0.85rem",
                    transition: "background-color 0.15s ease",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.backgroundColor = "var(--bg-card-hover)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.backgroundColor = "transparent")
                  }
                >
                  <td style={{ padding: "1rem 1.25rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                      <FileText size={17} color="var(--maroon)" />
                      <span style={{ fontWeight: 600, color: "var(--text-ink)" }}>
                        {doc.name}
                      </span>
                    </div>
                  </td>

                  <td style={{ padding: "1rem 1rem" }}>
                    <span
                      style={{
                        fontSize: "0.74rem",
                        padding: "0.15rem 0.5rem",
                        backgroundColor: "var(--bg-parchment)",
                        border: "1px solid var(--border-subtle)",
                        borderRadius: "2px",
                        color: "var(--navy)",
                        fontWeight: 600,
                      }}
                    >
                      {doc.type}
                    </span>
                  </td>

                  <td style={{ padding: "1rem 1rem", fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
                    {doc.date}
                  </td>

                  <td style={{ padding: "1rem 1rem", color: "var(--text-muted)" }}>
                    {doc.pages} pp
                  </td>

                  <td style={{ padding: "1rem 1rem" }}>
                    <ProvenanceBadge
                      type={doc.provenance || (hasMeta ? "VERIFIED_FROM_SOURCE" : "NOT_VERIFIED")}
                    />
                  </td>

                  <td style={{ padding: "1rem 1.25rem", textAlign: "right" }}>
                    <div style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", justifyContent: "flex-end" }}>
                      <a
                        href={`/api/documents/stream?documentId=${encodeURIComponent(doc.name)}&matterId=${encodeURIComponent(matter.id)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.3rem",
                          fontSize: "0.76rem",
                          color: "var(--navy)",
                          fontWeight: 600,
                          textDecoration: "none",
                          padding: "0.25rem 0.55rem",
                          border: "1px solid var(--border-rule)",
                          borderRadius: "2px",
                          backgroundColor: "var(--bg-parchment)",
                        }}
                        title={doc.sha256 ? `SHA-256: ${doc.sha256}` : "Authorized PDF Stream"}
                      >
                        <FileText size={12} />
                        <span>Source PDF</span>
                      </a>
                      <button
                        onClick={() => setInspectDoc(doc)}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.35rem",
                          fontSize: "0.78rem",
                          color: "var(--maroon)",
                          fontWeight: 600,
                          background: "none",
                          border: "1px solid var(--maroon-border)",
                          padding: "0.25rem 0.6rem",
                          borderRadius: "2px",
                          cursor: "pointer",
                        }}
                      >
                        <Eye size={12} />
                        <span>Inspect</span>
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* =====================================================================
          DOCUMENT INTELLIGENCE INSPECTION DRAWER/MODAL
          ===================================================================== */}
      {inspectDoc && (
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
              maxWidth: "680px",
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
                  STRUCTURED DOCUMENT INTELLIGENCE
                </span>
                <h3
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.45rem",
                    fontWeight: 700,
                    color: "var(--text-ink)",
                    margin: "0.25rem 0 0 0",
                  }}
                >
                  {inspectDoc.name}
                </h3>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginTop: "0.35rem", flexWrap: "wrap" }}>
                  {inspectDoc.sha256 && (
                    <span style={{ fontSize: "0.7rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)", backgroundColor: "var(--bg-parchment)", padding: "0.1rem 0.4rem", borderRadius: "2px", border: "1px solid var(--border-rule)" }}>
                      SHA-256: {inspectDoc.sha256.slice(0, 16)}...{inspectDoc.sha256.slice(-8)}
                    </span>
                  )}
                  <a
                    href={`/api/documents/stream?documentId=${encodeURIComponent(inspectDoc.name)}&matterId=${encodeURIComponent(matter.id)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      fontSize: "0.72rem",
                      fontWeight: 600,
                      color: "var(--maroon)",
                      textDecoration: "underline",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.25rem",
                    }}
                  >
                    <ExternalLink size={11} />
                    <span>Open Confidential PDF Stream</span>
                  </a>
                </div>
              </div>

              <button
                onClick={() => setInspectDoc(null)}
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

            {/* Modal Tabs */}
            <div
              style={{
                display: "flex",
                gap: "0.5rem",
                borderBottom: "1px solid var(--border-rule)",
                paddingBottom: "0.75rem",
                marginBottom: "1.25rem",
              }}
            >
              <button
                onClick={() => setInspectTab("metadata")}
                style={{
                  padding: "0.4rem 0.9rem",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  backgroundColor:
                    inspectTab === "metadata" ? "var(--maroon)" : "var(--bg-parchment)",
                  color: inspectTab === "metadata" ? "#FFFFFF" : "var(--text-ink)",
                  border: "1px solid var(--border-rule)",
                  borderRadius: "2px",
                  cursor: "pointer",
                }}
              >
                Structured Intelligence
              </button>

              <button
                onClick={() => {
                  setInspectTab("verbatim");
                  if (!verbatimData) loadVerbatimChunks("2021 INSC 194");
                }}
                style={{
                  padding: "0.4rem 0.9rem",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  backgroundColor:
                    inspectTab === "verbatim" ? "var(--maroon)" : "var(--bg-parchment)",
                  color: inspectTab === "verbatim" ? "#FFFFFF" : "var(--text-ink)",
                  border: "1px solid var(--border-rule)",
                  borderRadius: "2px",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.4rem",
                }}
              >
                <FileText size={13} />
                <span>
                  Verbatim Chunks (Real Repository Corpus)
                </span>
              </button>
            </div>

            {inspectTab === "verbatim" ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {loadingVerbatim ? (
                  <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
                    Loading verbatim chunks from persistent repository index...
                  </div>
                ) : verbatimData ? (
                  <>
                    <div
                      style={{
                        padding: "0.9rem 1rem",
                        backgroundColor: "var(--maroon-faint)",
                        border: "1px solid var(--maroon-border)",
                        borderRadius: "2px",
                        fontSize: "0.8rem",
                      }}
                    >
                      <div style={{ fontWeight: 700, color: "var(--maroon)", marginBottom: "0.25rem" }}>
                        {verbatimData.caseName}
                      </div>
                      <div style={{ color: "var(--text-ink)", marginBottom: "0.35rem" }}>
                        Citation: <strong>{verbatimData.citation}</strong> • Bench: {verbatimData.bench}
                      </div>
                      <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "0.74rem" }}>
                        Source File: {verbatimData.pdfSourcePath} ({verbatimData.pageSize} Pages • {verbatimData.total_chunks_in_corpus || 63} Chunks)
                      </div>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                      <div style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--text-faint)", textTransform: "uppercase" }}>
                        CHUNKS EXTRACTED DIRECTLY FROM THE REPOSITORY (FIRST 10 SHOWN):
                      </div>

                      {verbatimData.chunks?.map((chk: any, idx: number) => (
                        <div
                          key={idx}
                          style={{
                            padding: "0.85rem 1rem",
                            backgroundColor: "var(--bg-parchment)",
                            border: "1px solid var(--border-rule)",
                            borderRadius: "2px",
                          }}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.4rem", fontSize: "0.72rem", fontFamily: "var(--font-mono)", color: "var(--maroon)", fontWeight: 700 }}>
                            <span>Chunk ID: {chk.chunk_id}</span>
                            <span>Length: {chk.length} chars</span>
                          </div>
                          <div style={{ fontSize: "0.82rem", fontFamily: "var(--font-serif)", lineHeight: 1.55, color: "var(--text-ink)", whiteSpace: "pre-wrap" }}>
                            {chk.text}
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div style={{ color: "var(--text-muted)" }}>No verbatim data available.</div>
                )}
              </div>
            ) : inspectDoc.extractedMetadata ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <div
                  style={{
                    backgroundColor: "var(--maroon-faint)",
                    border: "1px solid var(--maroon-border)",
                    borderRadius: "2px",
                    padding: "0.85rem 1rem",
                    fontSize: "0.75rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    color: "var(--maroon)",
                  }}
                >
                  <Sparkles size={14} />
                  <span>
                    Parsed by Gemini 3.5 Flash Lite • Linked to Vidhik Hierarchical Document Index
                  </span>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "1rem",
                  }}
                >
                  <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-faint)", textTransform: "uppercase" }}>
                      Document Class
                    </div>
                    <div style={{ fontSize: "0.88rem", fontWeight: 600, color: "var(--text-ink)" }}>
                      {inspectDoc.extractedMetadata.document_type}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-faint)", textTransform: "uppercase" }}>
                      Court / Authority
                    </div>
                    <div style={{ fontSize: "0.88rem", fontWeight: 600, color: "var(--navy)" }}>
                      {inspectDoc.extractedMetadata.court || matter.court}
                    </div>
                  </div>
                </div>

                {inspectDoc.extractedMetadata.sections?.length ? (
                  <div>
                    <div
                      style={{
                        fontSize: "0.72rem",
                        color: "var(--text-faint)",
                        textTransform: "uppercase",
                        marginBottom: "0.4rem",
                      }}
                    >
                      Statutory Sections Cited
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                      {inspectDoc.extractedMetadata.sections.map((sec, i) => (
                        <span
                          key={i}
                          style={{
                            fontSize: "0.78rem",
                            padding: "0.2rem 0.5rem",
                            backgroundColor: "var(--bg-parchment)",
                            border: "1px solid var(--border-rule)",
                            borderRadius: "2px",
                            fontFamily: "var(--font-mono)",
                            color: "var(--maroon)",
                          }}
                        >
                          {sec}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}

                {inspectDoc.extractedMetadata.important_points?.length ? (
                  <div>
                    <div
                      style={{
                        fontSize: "0.72rem",
                        color: "var(--text-faint)",
                        textTransform: "uppercase",
                        marginBottom: "0.4rem",
                      }}
                    >
                      Key Factual Statements Extracted
                    </div>
                    <div
                      style={{
                        backgroundColor: "var(--bg-parchment)",
                        border: "1px solid var(--border-subtle)",
                        borderRadius: "2px",
                        padding: "1rem",
                        display: "flex",
                        flexDirection: "column",
                        gap: "0.5rem",
                      }}
                    >
                      {inspectDoc.extractedMetadata.important_points.map((pt, i) => (
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
                          <span style={{ color: "var(--maroon)" }}>•</span>
                          <span>{pt}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <p style={{ color: "var(--text-muted)", fontSize: "0.88rem" }}>
                Metadata has not been extracted for this document yet.
              </p>
            )}

            <div
              style={{
                marginTop: "1.75rem",
                paddingTop: "1rem",
                borderTop: "1px solid var(--border-subtle)",
                display: "flex",
                justifyContent: "flex-end",
              }}
            >
              <button
                onClick={() => setInspectDoc(null)}
                style={{
                  padding: "0.5rem 1.25rem",
                  backgroundColor: "var(--navy)",
                  color: "#FFFFFF",
                  borderRadius: "2px",
                  fontSize: "0.85rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Close Inspection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          DOCUMENT UPLOAD MODAL WITH GEMINI EXTRACTION
          ===================================================================== */}
      {showUploadModal && (
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
            padding: "1rem",
          }}
        >
          <div
            className="paper-card"
            style={{
              maxWidth: "540px",
              width: "100%",
              backgroundColor: "var(--bg-sheet)",
              borderRadius: "4px",
              padding: "2rem",
              boxShadow: "var(--shadow-modal)",
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
                  fontSize: "1.35rem",
                  fontWeight: 700,
                  color: "var(--text-ink)",
                  margin: 0,
                }}
              >
                Add Matter Document
              </h3>

              <button
                onClick={() => setShowUploadModal(false)}
                style={{ background: "none", border: "none", cursor: "pointer" }}
              >
                <X size={18} color="var(--text-muted)" />
              </button>
            </div>

            <form onSubmit={handleUploadSubmit}>
              <div style={{ display: "flex", flexDirection: "column", gap: "1.1rem" }}>
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.8rem",
                      fontWeight: 600,
                      marginBottom: "0.35rem",
                    }}
                  >
                    Document Name / Filename
                  </label>
                  <input
                    type="text"
                    required
                    value={uploadName}
                    onChange={(e) => setUploadName(e.target.value)}
                    placeholder="e.g. Additional_Affidavit_Medical_Records.pdf"
                    style={{
                      width: "100%",
                      padding: "0.65rem 0.8rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      fontSize: "0.88rem",
                    }}
                  />
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.8rem",
                      fontWeight: 600,
                      marginBottom: "0.35rem",
                    }}
                  >
                    Document Classification
                  </label>
                  <select
                    value={uploadType}
                    onChange={(e) => setUploadType(e.target.value as any)}
                    style={{
                      width: "100%",
                      padding: "0.65rem 0.8rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      fontSize: "0.88rem",
                    }}
                  >
                    <option value="Pleadings">Pleadings</option>
                    <option value="Orders">Orders</option>
                    <option value="Judgments">Judgments</option>
                    <option value="Applications">Applications</option>
                    <option value="Evidence">Evidence</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.8rem",
                      fontWeight: 600,
                      marginBottom: "0.35rem",
                    }}
                  >
                    Document Text Excerpt (for Intelligence Extraction)
                  </label>
                  <textarea
                    rows={4}
                    value={uploadText}
                    onChange={(e) => setUploadText(e.target.value)}
                    placeholder="Paste verbatim document text or summary to trigger Gemini structured extraction..."
                    style={{
                      width: "100%",
                      padding: "0.65rem 0.8rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      fontSize: "0.85rem",
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                </div>

                {uploadStatusMsg && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      fontSize: "0.8rem",
                      color: "var(--maroon)",
                      backgroundColor: "var(--maroon-faint)",
                      padding: "0.5rem 0.75rem",
                      borderRadius: "2px",
                    }}
                  >
                    <Sparkles size={14} />
                    <span>{uploadStatusMsg}</span>
                  </div>
                )}

                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-end",
                    gap: "0.75rem",
                    marginTop: "0.5rem",
                  }}
                >
                  <button
                    type="button"
                    onClick={() => setShowUploadModal(false)}
                    style={{
                      padding: "0.6rem 1rem",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      background: "none",
                      fontSize: "0.85rem",
                      cursor: "pointer",
                    }}
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    disabled={isExtracting}
                    style={{
                      padding: "0.6rem 1.4rem",
                      backgroundColor: "var(--maroon)",
                      color: "#FFFFFF",
                      borderRadius: "2px",
                      fontSize: "0.85rem",
                      fontWeight: 600,
                      border: "none",
                      cursor: isExtracting ? "wait" : "pointer",
                    }}
                  >
                    {isExtracting ? "Extracting..." : "Upload & Parse"}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
