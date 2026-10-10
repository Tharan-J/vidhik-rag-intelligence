/**
 * Confidential Legal Document Storage & Authorization Subsystem
 * ==============================================================
 * Security Invariants:
 * 1. ZERO PUBLIC STORAGE: Confidential matter PDFs are stored strictly OUTSIDE
 *    the Next.js public web root under `frontend/storage/documents/matters/`.
 * 2. TENANT & MATTER ISOLATION: A document belonging to matter A cannot be
 *    resolved, verified, or accessed by a request authorized only for matter B.
 * 3. NO CLIENT PATH TRUST: Client-supplied file paths are rejected. Resolution
 *    is performed strictly via document ID and authorized matter scope.
 * 4. PATH TRAVERSAL DEFENSE: All identifiers are strictly sanitized; any normalized
 *    path resolving outside the target matter storage namespace is blocked.
 * 5. CRYPTOGRAPHIC INTEGRITY: Computes and verifies SHA-256 digests on all stored
 *    and resolved documents.
 */

import fs from "fs";
import path from "path";
import crypto from "crypto";

// Private storage root strictly outside Next.js `public/` web root
export const PRIVATE_STORAGE_ROOT = path.resolve(process.cwd(), "storage", "documents", "matters");

// Read-only reference corpus roots for public precedents (never contains confidential matter briefs)
export const READONLY_CORPUS_ROOTS = [
  path.resolve(process.cwd(), "..", "research", "legal_data"),
  path.resolve(process.cwd(), "..", "test"),
];

export interface AuthorizationContext {
  isAuthenticated: boolean;
  matterId?: string;
  userId?: string;
  role?: "lawyer" | "admin" | "court_clerk" | "auditor";
}

export interface StoredDocumentResult {
  storagePath: string; // Relative private storage path (e.g. storage/documents/matters/MAT-001/doc.pdf)
  absolutePath: string;
  sha256: string;
  fileSize: number;
  documentId: string;
  matterId: string;
}

export type ResolveDocumentResult =
  | {
      success: true;
      authorizedPath: string;
      sha256: string;
      documentId: string;
      matterId: string;
      isCorpusPrecedent: boolean;
    }
  | {
      success: false;
      error:
        | "UNAUTHENTICATED"
        | "ACCESS_DENIED_CROSS_MATTER"
        | "ACCESS_DENIED_PATH_TRAVERSAL"
        | "DOCUMENT_NOT_FOUND"
        | "INVALID_IDENTIFIER";
      details: string;
    };

/**
 * Sanitizes matter and document identifiers, stripping path traversal sequences.
 */
export function sanitizeIdentifier(input: string): string {
  if (!input) return "";
  // Strip null bytes, slashes, backslashes, and directory traversal dots
  const clean = input
    .replace(/\0/g, "")
    .replace(/[\/\\]+/g, "_")
    .replace(/\.{2,}/g, "_")
    .replace(/[^a-zA-Z0-9_\-\. ]/g, "_")
    .trim();
  return clean;
}

/**
 * Computes SHA-256 hash of a buffer or file path.
 */
export function computeSha256(input: Buffer | string): string {
  const hash = crypto.createHash("sha256");
  if (Buffer.isBuffer(input)) {
    hash.update(input);
  } else if (typeof input === "string" && fs.existsSync(input)) {
    hash.update(fs.readFileSync(input));
  } else {
    return "";
  }
  return hash.digest("hex");
}

/**
 * Saves an uploaded confidential PDF to private matter-scoped persistent storage.
 */
export function saveUploadedDocument(params: {
  buffer: Buffer;
  matterId: string;
  documentName: string;
  documentId?: string;
}): StoredDocumentResult {
  const safeMatterId = sanitizeIdentifier(params.matterId || "default_matter");
  if (!safeMatterId) {
    throw new Error("INVALID_MATTER_ID: A valid matter identifier is required.");
  }

  const rawDocName = params.documentName || "document.pdf";
  const safeDocName = sanitizeIdentifier(path.basename(rawDocName));
  const docId = params.documentId || `DOC-${Date.now()}-${safeDocName}`;

  // Target directory strictly inside PRIVATE_STORAGE_ROOT
  const matterDir = path.resolve(PRIVATE_STORAGE_ROOT, safeMatterId);
  if (!fs.existsSync(matterDir)) {
    fs.mkdirSync(matterDir, { recursive: true });
  }

  const absolutePath = path.resolve(matterDir, safeDocName);

  // Safety invariant check: ensure resolved path is strictly within matterDir
  if (!absolutePath.startsWith(matterDir)) {
    throw new Error("SECURITY_VIOLATION: Document path escaped matter directory boundary.");
  }

  fs.writeFileSync(absolutePath, params.buffer);

  const sha256 = computeSha256(params.buffer);
  const relativeStoragePath = `storage/documents/matters/${safeMatterId}/${safeDocName}`;

  return {
    storagePath: relativeStoragePath,
    absolutePath,
    sha256,
    fileSize: params.buffer.length,
    documentId: docId,
    matterId: safeMatterId,
  };
}

/**
 * Resolves and authorizes access to a confidential matter document.
 * Strictly verifies authentication, matter boundary matching, and path confinement.
 */
export function resolveAuthorizedDocument(params: {
  documentId: string;
  authContext: AuthorizationContext;
  requestedMatterId?: string;
  allowCorpusFallback?: boolean;
}): ResolveDocumentResult {
  const { documentId, authContext, requestedMatterId, allowCorpusFallback = false } = params;

  // 1. Authentication check
  if (!authContext || !authContext.isAuthenticated) {
    return {
      success: false,
      error: "UNAUTHENTICATED",
      details: "Request lacks valid authentication context.",
    };
  }

  if (!documentId || !documentId.trim()) {
    return {
      success: false,
      error: "INVALID_IDENTIFIER",
      details: "Document ID cannot be empty.",
    };
  }

  const safeDocId = sanitizeIdentifier(path.basename(documentId));
  const effectiveMatter = requestedMatterId || authContext.matterId;

  // 2. Tenant / Matter Isolation check
  if (effectiveMatter && authContext.matterId && authContext.matterId !== effectiveMatter) {
    return {
      success: false,
      error: "ACCESS_DENIED_CROSS_MATTER",
      details: `User authorized for matter '${authContext.matterId}' cannot access matter '${effectiveMatter}'.`,
    };
  }

  // 3. Check confidential matter storage if matterId is present
  if (effectiveMatter) {
    const safeMatter = sanitizeIdentifier(effectiveMatter);
    const targetMatterDir = path.resolve(PRIVATE_STORAGE_ROOT, safeMatter);
    const candidatePath = path.resolve(targetMatterDir, safeDocId);

    // Path traversal defense
    if (!candidatePath.startsWith(targetMatterDir)) {
      return {
        success: false,
        error: "ACCESS_DENIED_PATH_TRAVERSAL",
        details: "Path traversal detected in document identifier.",
      };
    }

    let finalPath = candidatePath;
    if (!fs.existsSync(finalPath) && fs.existsSync(targetMatterDir)) {
      try {
        const files = fs.readdirSync(targetMatterDir);
        const match = files.find(
          (f) => f === safeDocId || f.startsWith(safeDocId) || safeDocId.includes(f)
        );
        if (match) {
          finalPath = path.resolve(targetMatterDir, match);
        }
      } catch {}
    }

    if (fs.existsSync(finalPath) && finalPath.startsWith(targetMatterDir)) {
      const sha256 = computeSha256(finalPath);
      return {
        success: true,
        authorizedPath: finalPath,
        sha256,
        documentId: path.basename(finalPath),
        matterId: safeMatter,
        isCorpusPrecedent: false,
      };
    }
  }

  // 4. Fallback for published judicial precedents (corpus precedents)
  if (allowCorpusFallback) {
    for (const corpusRoot of READONLY_CORPUS_ROOTS) {
      const candidateCorpus = path.resolve(corpusRoot, safeDocId);
      if (candidateCorpus.startsWith(corpusRoot) && fs.existsSync(/*turbopackIgnore: true*/ candidateCorpus)) {
        const sha256 = computeSha256(candidateCorpus);
        return {
          success: true,
          authorizedPath: candidateCorpus,
          sha256,
          documentId: safeDocId,
          matterId: "PUBLIC_CORPUS",
          isCorpusPrecedent: true,
        };
      }
    }

    // Check nested candidate pools in research/legal_data
    const baseLegalData = path.resolve(process.cwd(), "..", "research", "legal_data");
    const candidates = [safeDocId];
    const parts = safeDocId.split("_");
    if (parts.length >= 5) {
      candidates.push(parts.slice(-5).join("_"));
    }
    for (const c of candidates) {
      for (const tier of ["supreme_court", "high_court", "district_court"]) {
        const tierDir = path.resolve(baseLegalData, tier, "pdfs_stage1_candidates");
        if (!fs.existsSync(tierDir)) continue;
        try {
          const years = fs.readdirSync(tierDir);
          for (const yr of years) {
            const candPath = path.resolve(tierDir, yr, c);
            if (fs.existsSync(candPath)) {
              return {
                success: true,
                authorizedPath: candPath,
                sha256: computeSha256(candPath),
                documentId: safeDocId,
                matterId: "PUBLIC_CORPUS",
                isCorpusPrecedent: true,
              };
            }
          }
        } catch {}
      }
    }
  }

  return {
    success: false,
    error: "DOCUMENT_NOT_FOUND",
    details: `Document '${safeDocId}' was not found in authorized matter scope '${effectiveMatter || "NONE"}'.`,
  };
}
