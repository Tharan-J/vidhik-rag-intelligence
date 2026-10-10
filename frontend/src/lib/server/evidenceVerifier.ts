/**
 * Deterministic Evidence Verification and Provenance Subsystem
 * ============================================================
 * Implements strict source verification for retrieved evidence against
 * authentic court documents and extraction manifests.
 *
 * Guarantees:
 * - Verification status is NEVER equated to semantic support.
 * - Detects coordinate mismatches (wrong page), missing passages, and stale documents.
 * - Preserves exact character landmarks without fabricating bounding boxes.
 */

import crypto from "crypto";
import fs from "fs";
import path from "path";

export type VerificationStatus =
  | "VERIFIED_EXACT"
  | "VERIFIED_NORMALIZED"
  | "OCR_UNCERTAINTY"
  | "COORDINATE_MISMATCH"
  | "PASSAGE_NOT_FOUND"
  | "DOCUMENT_STALE"
  | "DOCUMENT_DELETED"
  | "HISTORICAL_UNVERIFIED";

export interface ReconstructedContext {
  targetParagraphId: string;
  targetPage: number;
  targetText: string;
  precedingParagraphs: Array<{ paragraphId: string; pageNumber: number; text: string }>;
  succeedingParagraphs: Array<{ paragraphId: string; pageNumber: number; text: string }>;
  fullContextText: string;
  paragraphRange: [string, string];
  pageSpan: [number, number];
}

export interface VerificationResult {
  status: VerificationStatus;
  documentId: string;
  documentSha256: string;
  reportedPage?: number;
  verifiedPage?: number;
  reportedParagraph?: string;
  verifiedParagraph?: string;
  isExactMatch: boolean;
  similarityScore: number;
  charOffsetInPage?: [number, number];
  reconstructedContext?: ReconstructedContext;
  notes: string;
}

/**
 * Standardize whitespace, linebreaks, and Unicode normalization (NFKC).
 */
export function normalizeLegalText(text: string): string {
  if (!text) return "";
  return text
    .normalize("NFKC")
    .replace(/\xad/g, "")
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/[\u2014\u2013]/g, "-")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Computes SHA-256 hash of a file buffer or disk path.
 */
export function computeSha256(filePathOrBuffer: string | Buffer): string {
  const hash = crypto.createHash("sha256");
  if (Buffer.isBuffer(filePathOrBuffer)) {
    hash.update(filePathOrBuffer);
  } else if (fs.existsSync(filePathOrBuffer)) {
    const fileBuffer = fs.readFileSync(filePathOrBuffer);
    hash.update(fileBuffer);
  } else {
    return "";
  }
  return hash.digest("hex");
}

/**
 * Verifies a retrieved passage against an in-memory page array or manifest.
 */
export function verifyPassageAgainstPages(params: {
  documentId: string;
  documentSha256: string;
  pages: Array<{ pageNumber: number; text: string }>;
  passageText: string;
  reportedPage?: number;
  reportedParagraph?: string;
  expectedSha256?: string;
}): VerificationResult {
  const {
    documentId,
    documentSha256,
    pages,
    passageText,
    reportedPage,
    reportedParagraph,
    expectedSha256,
  } = params;

  // 1. Version drift check
  if (expectedSha256 && documentSha256 && expectedSha256 !== documentSha256) {
    return {
      status: "DOCUMENT_STALE",
      documentId,
      documentSha256,
      reportedPage,
      reportedParagraph,
      isExactMatch: false,
      similarityScore: 0,
      notes: `DOCUMENT_STALE: Stored document SHA-256 diverges from expected hash (${expectedSha256.slice(0, 10)}...).`,
    };
  }

  const cleanPassage = passageText.trim();
  const normPassage = normalizeLegalText(cleanPassage);

  if (!normPassage) {
    return {
      status: "PASSAGE_NOT_FOUND",
      documentId,
      documentSha256,
      reportedPage,
      reportedParagraph,
      isExactMatch: false,
      similarityScore: 0,
      notes: "Passage query text is empty.",
    };
  }

  // 2. Check reported page first
  if (reportedPage && reportedPage >= 1 && reportedPage <= pages.length) {
    const pageObj = pages[reportedPage - 1];
    const rawPage = pageObj.text || "";
    const normPage = normalizeLegalText(rawPage);

    // Exact verbatim check
    const exactIdx = rawPage.indexOf(cleanPassage);
    if (exactIdx !== -1) {
      return {
        status: "VERIFIED_EXACT",
        documentId,
        documentSha256,
        reportedPage,
        verifiedPage: reportedPage,
        reportedParagraph,
        verifiedParagraph: reportedParagraph || `Page ${reportedPage} Section`,
        isExactMatch: true,
        similarityScore: 1.0,
        charOffsetInPage: [exactIdx, exactIdx + cleanPassage.length],
        notes: `Passage verified verbatim on Page ${reportedPage}.`,
      };
    }

    // Normalized check
    const normIdx = normPage.indexOf(normPassage);
    if (normIdx !== -1) {
      return {
        status: "VERIFIED_NORMALIZED",
        documentId,
        documentSha256,
        reportedPage,
        verifiedPage: reportedPage,
        reportedParagraph,
        verifiedParagraph: reportedParagraph || `Page ${reportedPage} Section`,
        isExactMatch: false,
        similarityScore: 0.99,
        notes: `Passage verified after whitespace/line-wrap normalization on Page ${reportedPage}.`,
      };
    }

    // Fuzzy OCR check (token overlap ratio)
    const pTokens = new Set(normPassage.split(" ").filter((t) => t.length > 2));
    const pageTokens = new Set(normPage.split(" ").filter((t) => t.length > 2));
    let matchCount = 0;
    pTokens.forEach((t) => {
      if (pageTokens.has(t)) matchCount++;
    });
    const tokenOverlap = pTokens.size > 0 ? matchCount / pTokens.size : 0;

    if (tokenOverlap >= 0.85) {
      return {
        status: "OCR_UNCERTAINTY",
        documentId,
        documentSha256,
        reportedPage,
        verifiedPage: reportedPage,
        reportedParagraph,
        verifiedParagraph: reportedParagraph || `Page ${reportedPage} Section`,
        isExactMatch: false,
        similarityScore: Number(tokenOverlap.toFixed(2)),
        notes: `OCR_UNCERTAINTY: High token overlap (${(tokenOverlap * 100).toFixed(0)}%) on Page ${reportedPage}, possible scan or OCR artifacts.`,
      };
    }
  }

  // 3. Coordinate mismatch check across other pages
  for (const pageObj of pages) {
    if (reportedPage && pageObj.pageNumber === reportedPage) continue;

    const rawOther = pageObj.text || "";
    const exactOtherIdx = rawOther.indexOf(cleanPassage);
    if (exactOtherIdx !== -1) {
      return {
        status: "COORDINATE_MISMATCH",
        documentId,
        documentSha256,
        reportedPage,
        verifiedPage: pageObj.pageNumber,
        reportedParagraph,
        verifiedParagraph: `Page ${pageObj.pageNumber} Section`,
        isExactMatch: true,
        similarityScore: 1.0,
        charOffsetInPage: [exactOtherIdx, exactOtherIdx + cleanPassage.length],
        notes: `COORDINATE_MISMATCH: Reported as Page ${reportedPage}, but physically verified on Page ${pageObj.pageNumber}.`,
      };
    }

    const normOther = normalizeLegalText(rawOther);
    if (normOther.includes(normPassage)) {
      return {
        status: "COORDINATE_MISMATCH",
        documentId,
        documentSha256,
        reportedPage,
        verifiedPage: pageObj.pageNumber,
        reportedParagraph,
        verifiedParagraph: `Page ${pageObj.pageNumber} Section`,
        isExactMatch: false,
        similarityScore: 0.98,
        notes: `COORDINATE_MISMATCH: Reported as Page ${reportedPage}, but normalized text found on Page ${pageObj.pageNumber}.`,
      };
    }
  }

  // 4. Passage not found
  return {
    status: "PASSAGE_NOT_FOUND",
    documentId,
    documentSha256,
    reportedPage,
    reportedParagraph,
    isExactMatch: false,
    similarityScore: 0,
    notes: `PASSAGE_NOT_FOUND: The passage does not exist anywhere within document ${documentId} (${pages.length} pages searched).`,
  };
}
