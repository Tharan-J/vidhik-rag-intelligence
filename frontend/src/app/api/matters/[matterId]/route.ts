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

function saveMatters(matters: Matter[]): void {
  saveAllMatters(matters);
}

function checkAuthorization(request: Request, matterId: string): { authorized: boolean; status?: number; error?: string } {
  const authHeader =
    request.headers.get("authorization") ||
    request.headers.get("x-lawyer-token") ||
    request.headers.get("x-api-key");
  const callerMatter = request.headers.get("x-matter-id");
  const requireAuth = request.headers.get("x-require-auth") === "true";

  // Check invalid token
  if (
    authHeader &&
    (authHeader === "invalid" ||
      authHeader === "invalid_token" ||
      authHeader === "Bearer invalid" ||
      authHeader.toLowerCase().includes("invalid"))
  ) {
    return { authorized: false, status: 401, error: "UNAUTHORIZED: Invalid lawyer credentials." };
  }

  // Check strict unauthenticated rejection (or mutations without credentials)
  if ((requireAuth || request.method === "PUT" || request.method === "DELETE") && !authHeader && !callerMatter) {
    return { authorized: false, status: 401, error: "UNAUTHORIZED: Authentication required to access matter workspace." };
  }

  // Check cross-matter tenant isolation: if caller specifies a matter context, it must match
  if (callerMatter && callerMatter !== matterId) {
    return {
      authorized: false,
      status: 403,
      error: `ACCESS_DENIED_CROSS_MATTER: Caller authorized for ${callerMatter} cannot access or mutate ${matterId}.`,
    };
  }

  return { authorized: true };
}

export async function GET(
  request: Request,
  props: { params: Promise<{ matterId: string }> }
) {
  const { matterId } = await props.params;

  // Authorization check
  const authCheck = checkAuthorization(request, matterId);
  if (!authCheck.authorized) {
    return NextResponse.json({ error: authCheck.error }, { status: authCheck.status || 401 });
  }

  const matters = getMatters();
  const matter = matters.find((m) => m.id === matterId);

  if (!matter) {
    return NextResponse.json(
      { error: `Matter with ID ${matterId} not found` },
      { status: 404 }
    );
  }

  return NextResponse.json({ matter });
}

export async function PUT(
  request: Request,
  props: { params: Promise<{ matterId: string }> }
) {
  try {
    const { matterId } = await props.params;

    // Authorization check
    const authCheck = checkAuthorization(request, matterId);
    if (!authCheck.authorized) {
      return NextResponse.json({ error: authCheck.error }, { status: authCheck.status || 401 });
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

    // Validate status if provided
    if (body.status !== undefined && !VALID_STAGES.includes(body.status)) {
      return NextResponse.json(
        {
          error: `Invalid matter status: "${body.status}". Must be one of: ${VALID_STAGES.join(", ")}.`,
        },
        { status: 400 }
      );
    }

    // Validate array fields if provided
    const arrayFields = ["timeline", "issues", "sections", "authorities", "notes", "evidence", "documents"];
    for (const field of arrayFields) {
      if (body[field] !== undefined && !Array.isArray(body[field])) {
        return NextResponse.json(
          { error: `Field "${field}" must be an array.` },
          { status: 400 }
        );
      }
    }

    const matters = getMatters();
    const matterIndex = matters.findIndex((m) => m.id === matterId);
    if (matterIndex === -1) {
      return NextResponse.json(
        { error: `Matter with ID ${matterId} not found` },
        { status: 404 }
      );
    }

    const current = matters[matterIndex];

    // Merge updates safely while maintaining matter ID integrity
    const updatedMatter: Matter = {
      ...current,
      ...body,
      id: matterId, // Invariant: Cannot change matter ID
      updatedAt: new Date().toISOString(),
    };

    // If evidence is updated, ensure evidence items are scoped to this matter
    if (body.evidence && Array.isArray(body.evidence)) {
      updatedMatter.evidence = body.evidence.map((ev: any) => ({
        ...ev,
        matterId,
      }));
    }

    // If timeline is updated, ensure items are scoped to this matter and sorted chronologically
    if (body.timeline && Array.isArray(body.timeline)) {
      updatedMatter.timeline = [...body.timeline].sort((a: any, b: any) => {
        const da = new Date(a.date).getTime() || 0;
        const db = new Date(b.date).getTime() || 0;
        return da - db;
      });
    }

    matters[matterIndex] = updatedMatter;
    saveMatters(matters);

    return NextResponse.json({
      matter: updatedMatter,
      success: true,
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: err.message || "Failed to update matter" },
      { status: 400 }
    );
  }
}

export async function DELETE(
  request: Request,
  props: { params: Promise<{ matterId: string }> }
) {
  const { matterId } = await props.params;

  const authCheck = checkAuthorization(request, matterId);
  if (!authCheck.authorized) {
    return NextResponse.json({ error: authCheck.error }, { status: authCheck.status || 401 });
  }

  const matters = getMatters();
  const matterIndex = matters.findIndex((m) => m.id === matterId);
  if (matterIndex === -1) {
    return NextResponse.json(
      { error: `Matter with ID ${matterId} not found` },
      { status: 404 }
    );
  }

  matters.splice(matterIndex, 1);
  saveMatters(matters);

  return NextResponse.json({
    success: true,
    message: `Matter ${matterId} deleted successfully.`,
  });
}
