import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import {
  resolveAuthorizedDocument,
  AuthorizationContext,
} from "@/lib/server/documentStorage";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const documentId = searchParams.get("docId") || searchParams.get("documentId") || "";
    const matterId = searchParams.get("matterId") || "";

    if (!documentId) {
      return NextResponse.json(
        { error: "docId parameter is required." },
        { status: 400 }
      );
    }

    // 1. Establish and verify authorization context
    const authHeader =
      request.headers.get("authorization") ||
      request.headers.get("x-lawyer-token") ||
      request.headers.get("x-api-key");
    const callerMatter = request.headers.get("x-matter-id") || matterId;

    const authContext: AuthorizationContext = {
      isAuthenticated: Boolean(authHeader || callerMatter),
      matterId: callerMatter,
      userId: request.headers.get("x-user-id") || "lawyer_session",
      role: "lawyer",
    };

    if (!authContext.isAuthenticated) {
      return NextResponse.json(
        { error: "UNAUTHORIZED: Authentication required to access confidential document." },
        { status: 401 }
      );
    }

    // 2. Resolve document via authorized private storage
    const resolved = resolveAuthorizedDocument({
      documentId,
      authContext,
      requestedMatterId: matterId,
      allowCorpusFallback: true,
    });

    if (!resolved.success) {
      if (resolved.error === "ACCESS_DENIED_CROSS_MATTER") {
        return NextResponse.json(
          { error: "FORBIDDEN: Cross-matter document access is prohibited." },
          { status: 403 }
        );
      }
      if (resolved.error === "ACCESS_DENIED_PATH_TRAVERSAL") {
        return NextResponse.json(
          { error: "FORBIDDEN: Invalid path identifier." },
          { status: 403 }
        );
      }
      return NextResponse.json(
        { error: "NOT_FOUND: Document not found in authorized storage." },
        { status: 404 }
      );
    }

    // 3. Stream PDF binary with security headers
    const fileBuffer = fs.readFileSync(resolved.authorizedPath);
    return new NextResponse(fileBuffer, {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `inline; filename="${encodeURIComponent(path.basename(resolved.authorizedPath))}"`,
        "X-Document-Sha256": resolved.sha256,
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, no-cache, no-store, must-revalidate",
      },
    });
  } catch (err: any) {
    console.error("Document streaming error:", err);
    return NextResponse.json(
      { error: err.message || "Failed to stream document" },
      { status: 500 }
    );
  }
}
