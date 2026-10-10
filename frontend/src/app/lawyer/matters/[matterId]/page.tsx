"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { LawyerShell } from "@/components/lawyer/LawyerShell";
import { INITIAL_MATTERS } from "@/lib/data/matters";
import { Matter } from "@/lib/types/matter";
import { MatterHeader } from "@/components/lawyer/matter/MatterHeader";
import { OverviewTab } from "@/components/lawyer/matter/OverviewTab";
import { StatusTab } from "@/components/lawyer/matter/StatusTab";
import { TimelineTab } from "@/components/lawyer/matter/TimelineTab";
import { DocumentsTab } from "@/components/lawyer/matter/DocumentsTab";
import { IssuesTab } from "@/components/lawyer/matter/IssuesTab";
import { SectionsTab } from "@/components/lawyer/matter/SectionsTab";
import { AuthoritiesTab } from "@/components/lawyer/matter/AuthoritiesTab";
import { ResearchTab } from "@/components/lawyer/matter/ResearchTab";
import { EvidenceTab } from "@/components/lawyer/matter/EvidenceTab";
import { AIAssistantTab } from "@/components/lawyer/matter/AIAssistantTab";
import { NotesTab } from "@/components/lawyer/matter/NotesTab";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

function MatterWorkspaceContent() {
  const params = useParams();
  const matterId = params?.matterId as string;

  const [matter, setMatter] = useState<Matter | null>(null);
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch(`/api/matters/${matterId}`, {
      headers: {
        "x-lawyer-token": "dev_lawyer_token",
        "x-matter-id": matterId,
      },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.matter) {
          setMatter(data.matter);
        } else {
          const local = INITIAL_MATTERS.find((m) => m.id === matterId);
          if (local) setMatter(local);
        }
      })
      .catch(() => {
        const local = INITIAL_MATTERS.find((m) => m.id === matterId);
        if (local) setMatter(local);
      });
  }, [matterId]);

  const handleUpdateMatter = async (updates: Partial<Matter>) => {
    if (!matter) return;

    // Optimistically update local state
    const updatedMatter = { ...matter, ...updates, updatedAt: new Date().toISOString() };
    setMatter(updatedMatter);

    try {
      setSaving(true);
      const res = await fetch(`/api/matters/${matter.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "x-lawyer-token": "dev_lawyer_token",
          "x-matter-id": matter.id,
        },
        body: JSON.stringify(updates),
      });

      if (res.ok) {
        const data = await res.json();
        if (data?.matter) {
          setMatter(data.matter);
        }
      } else {
        console.error("Failed to persist matter updates to server:", await res.text());
      }
    } catch (err) {
      console.error("Network error persisting matter updates:", err);
    } finally {
      setSaving(false);
    }
  };

  if (!matter) {
    return (
      <LawyerShell>
        <div style={{ padding: "3rem", textAlign: "center", fontFamily: "var(--font-sans)", color: "var(--text-muted)" }}>
          Loading matter workspace...
        </div>
      </LawyerShell>
    );
  }

  return (
    <LawyerShell
      matterTitle={matter.title}
      matterCaseNumber={matter.caseNumber}
    >
      <div style={{ maxWidth: "1140px", margin: "0 auto" }}>
        {/* Dedicated Matter Header with Tab Bar */}
        <MatterHeader
          matter={matter}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        {/* Tab Content Display */}
        {activeTab === "overview" && (
          <OverviewTab matter={matter} onNavigateTab={setActiveTab} />
        )}
        {activeTab === "status" && (
          <StatusTab
            matter={matter}
            onUpdateStatus={(newStatus) =>
              handleUpdateMatter({ status: newStatus, currentStage: newStatus })
            }
          />
        )}
        {activeTab === "timeline" && (
          <TimelineTab
            matter={matter}
            onAddTimelineEvent={(newEvent) =>
              handleUpdateMatter({ timeline: [...(matter.timeline || []), newEvent] })
            }
          />
        )}
        {activeTab === "documents" && (
          <DocumentsTab
            matter={matter}
            onDocumentAdded={(newDoc) =>
              handleUpdateMatter({ documents: [newDoc, ...(matter.documents || [])] })
            }
          />
        )}
        {activeTab === "issues" && (
          <IssuesTab
            matter={matter}
            onUpdateIssues={(newIssues) =>
              handleUpdateMatter({ issues: newIssues })
            }
          />
        )}
        {activeTab === "sections" && (
          <SectionsTab
            matter={matter}
            onUpdateSections={(newSections) =>
              handleUpdateMatter({ sections: newSections })
            }
          />
        )}
        {activeTab === "authorities" && (
          <AuthoritiesTab
            matter={matter}
            onNavigateToResearch={() => setActiveTab("research")}
            onUpdateAuthorities={(newAuthorities) =>
              handleUpdateMatter({ authorities: newAuthorities })
            }
          />
        )}
        {activeTab === "research" && (
          <ResearchTab
            matter={matter}
            onSaveEvidenceToMatter={(newEvid) => {
              const currentEvidence = matter.evidence || [];
              const exists = currentEvidence.some((e) => e.id === newEvid.id);
              if (!exists) {
                handleUpdateMatter({ evidence: [...currentEvidence, newEvid] });
              }
            }}
          />
        )}
        {activeTab === "evidence" && (
          <EvidenceTab
            matter={matter}
            onUpdateEvidence={(newEvidence) =>
              handleUpdateMatter({ evidence: newEvidence })
            }
          />
        )}
        {activeTab === "assistant" && <AIAssistantTab matter={matter} />}
        {activeTab === "notes" && (
          <NotesTab
            matter={matter}
            onUpdateNotes={(newNotes) =>
              handleUpdateMatter({ notes: newNotes })
            }
          />
        )}
      </div>
    </LawyerShell>
  );
}

export default function MatterWorkspacePage() {
  return (
    <React.Suspense
      fallback={
        <div
          style={{
            minHeight: "100vh",
            backgroundColor: "var(--bg-parchment)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: "var(--font-sans)",
            color: "var(--text-muted)",
          }}
        >
          Loading matter workspace...
        </div>
      }
    >
      <MatterWorkspaceContent />
    </React.Suspense>
  );
}
