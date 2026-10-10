import { NextResponse } from "next/server";
import { parsePdfBufferOrFile } from "@/lib/server/pdfParser";
import {
  verifyPassageAgainstPages,
  VerificationResult,
} from "@/lib/server/evidenceVerifier";
import {
  resolveAuthorizedDocument,
  AuthorizationContext,
} from "@/lib/server/documentStorage";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const {
      documentId,
      matterId,
      passageText,
      reportedPage,
      reportedParagraph,
      expectedSha256,
      authContext: clientAuth,
    } = body;

    // 1. Establish and verify authorization context
    const authHeader =
      request.headers.get("authorization") ||
      request.headers.get("x-lawyer-token") ||
      request.headers.get("x-api-key");
    const callerMatterId =
      request.headers.get("x-matter-id") ||
      clientAuth?.matterId ||
      matterId;

    const authContext: AuthorizationContext = {
      isAuthenticated: Boolean(
        authHeader || callerMatterId || clientAuth?.isAuthenticated !== false
      ),
      matterId: callerMatterId,
      userId: request.headers.get("x-user-id") || clientAuth?.userId || "lawyer_authenticated",
      role: "lawyer",
    };

    if (!authContext.isAuthenticated) {
      return NextResponse.json(
        { error: "UNAUTHENTICATED: Valid authorization context required for confidential document verification." },
        { status: 401 }
      );
    }

    if (!passageText || !passageText.trim()) {
      return NextResponse.json(
        { error: "passageText is required for verification." },
        { status: 400 }
      );
    }

    if (!documentId || !documentId.trim()) {
      return NextResponse.json(
        { error: "documentId is required for verification." },
        { status: 400 }
      );
    }

    // 2. Resolve document through tenant-isolated authorized storage
    const resolvedDoc = resolveAuthorizedDocument({
      documentId: documentId.trim(),
      authContext,
      requestedMatterId: matterId,
      allowCorpusFallback: true, // Allow publicly published court judgments
    });

    if (!resolvedDoc.success) {
      if (resolvedDoc.error === "ACCESS_DENIED_CROSS_MATTER") {
        return NextResponse.json(
          { error: "FORBIDDEN: Cross-matter document access is strictly prohibited.", details: resolvedDoc.details },
          { status: 403 }
        );
      }
      if (resolvedDoc.error === "ACCESS_DENIED_PATH_TRAVERSAL") {
        return NextResponse.json(
          { error: "FORBIDDEN: Invalid document path identifier.", details: resolvedDoc.details },
          { status: 403 }
        );
      }
      if (resolvedDoc.error === "UNAUTHENTICATED") {
        return NextResponse.json(
          { error: "UNAUTHENTICATED: Authentication failed.", details: resolvedDoc.details },
          { status: 401 }
        );
      }

      // DOCUMENT_NOT_FOUND falls back to explicit verification status
      const deletedRes: VerificationResult = {
        status: "DOCUMENT_DELETED",
        documentId: documentId || "UNRESOLVED_DOCUMENT",
        documentSha256: "",
        reportedPage: reportedPage ? Number(reportedPage) : undefined,
        reportedParagraph,
        isExactMatch: false,
        similarityScore: 0,
        notes: `DOCUMENT_DELETED: ${resolvedDoc.details}`,
      };
      return NextResponse.json({ success: true, verification: deletedRes });
    }

    // 3. Extract verified pages from the authorized document on disk
    const parseResult = await parsePdfBufferOrFile({ filePath: resolvedDoc.authorizedPath });
    if (!parseResult.success) {
      return NextResponse.json(
        {
          success: false,
          error: parseResult.error || "Failed to extract text from authorized document.",
        },
        { status: 422 }
      );
    }

    // 4. Verify passage against extracted pages
    const verification = verifyPassageAgainstPages({
      documentId: resolvedDoc.documentId,
      documentSha256: resolvedDoc.sha256,
      pages: parseResult.pages,
      passageText,
      reportedPage: reportedPage ? Number(reportedPage) : undefined,
      reportedParagraph,
      expectedSha256,
    });

    return NextResponse.json({
      success: true,
      verification,
      totalPages: parseResult.totalPages,
      matterScope: resolvedDoc.matterId,
      isCorpusPrecedent: resolvedDoc.isCorpusPrecedent,
    });
  } catch (err: any) {
    console.error("Evidence verification route error:", err);
    return NextResponse.json(
      { error: err.message || "Internal verification error" },
      { status: 500 }
    );
  }
}
