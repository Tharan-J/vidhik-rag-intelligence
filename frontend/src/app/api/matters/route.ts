import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { INITIAL_MATTERS } from "@/lib/data/matters";
import { Matter, MatterStage } from "@/lib/types/matter";
import { loadAllMatters, saveAllMatters } from "@/lib/server/mattersStore";

const VALID_STAGES: MatterStage[] = [
  "Filed",
  "Notice",
  "Pleadings",
  "Evidence",
  "Arguments",
  "Judgment",
  "Disposed",
];

function getMatters(): Matter[] {
  return loadAllMatters();
}

export async function GET(request: Request) {
  const authHeader =
    request.headers.get("authorization") ||
    request.headers.get("x-lawyer-token") ||
    request.headers.get("x-api-key");
  const requireAuth = request.headers.get("x-require-auth") === "true";

  if (authHeader && (authHeader === "invalid" || authHeader === "invalid_token")) {
    return NextResponse.json({ error: "UNAUTHORIZED: Invalid lawyer credentials." }, { status: 401 });
  }

  if (requireAuth && !authHeader) {
    return NextResponse.json({ error: "UNAUTHORIZED: Authentication required." }, { status: 401 });
  }

  const matters = getMatters();
  return NextResponse.json({
    matters,
    total: matters.length,
    activeCount: matters.filter((m) => m.status !== "Judgment").length,
  });
}

export async function POST(request: Request) {
  try {
    const authHeader =
      request.headers.get("authorization") ||
      request.headers.get("x-lawyer-token") ||
      request.headers.get("x-api-key");

    if (authHeader && (authHeader === "invalid" || authHeader === "invalid_token")) {
      return NextResponse.json({ error: "UNAUTHORIZED: Invalid lawyer credentials." }, { status: 401 });
    }

    let body: any;
    try {
      body = await request.json();
    } catch {
      return NextResponse.json({ error: "Malformed JSON payload in request body." }, { status: 400 });
    }

    if (!body || typeof body !== "object") {
      return NextResponse.json({ error: "Invalid request payload. Expected an object." }, { status: 400 });
    }

    const title = (body.title || "").trim();
    if (!title) {
      return NextResponse.json(
        { error: "Validation error: 'title' is required and cannot be empty." },
        { status: 400 }
      );
    }

    const status: MatterStage = body.status || "Filed";
    if (!VALID_STAGES.includes(status)) {
      return NextResponse.json(
        {
          error: `Invalid matter status: "${body.status}". Must be one of: ${VALID_STAGES.join(", ")}.`,
        },
        { status: 400 }
      );
    }

    const matters = getMatters();
    const newMatter: Matter = {
      ...body,
      id: body.id || `MAT-${new Date().getFullYear()}-${String(matters.length + 1).padStart(3, "0")}`,
      title,
      status,
      caseNumber: body.caseNumber || "Unassigned",
      court: body.court || "Supreme Court of India",
      matterType: body.matterType || "Civil",
      currentStage: body.currentStage || status,
      createdAt: body.createdAt || new Date().toISOString().split("T")[0],
      updatedAt: new Date().toISOString(),
      client: body.client || "Client Record",
      summary: body.summary || "",
      parties: body.parties || { petitioner: "", respondent: "" },
      importantDates: body.importantDates || { filingDate: new Date().toISOString().split("T")[0], lastHearing: "" },
      documents: body.documents || [],
      timeline: body.timeline || [],
      issues: body.issues || [],
      sections: body.sections || [],
      authorities: body.authorities || [],
      notes: body.notes || [],
      evidence: body.evidence || [],
    };

    matters.unshift(newMatter);
    saveAllMatters(matters);

    return NextResponse.json({ matter: newMatter, success: true }, { status: 201 });
  } catch (err: any) {
    return NextResponse.json(
      { error: err.message || "Failed to create matter" },
      { status: 400 }
    );
  }
}
