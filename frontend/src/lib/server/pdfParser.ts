import { exec } from "child_process";
import { promisify } from "util";
import fs from "fs";
import path from "path";
import os from "os";
import zlib from "zlib";

const execAsync = promisify(exec);

export interface ExtractedPage {
  pageNumber: number;
  text: string;
}

export interface ParseResult {
  success: boolean;
  pages: ExtractedPage[];
  fullText: string;
  totalPages: number;
  error?: string;
}

/**
 * Pure Node.js fallback PDF text extractor.
 * Extracts text streams from PDF without requiring external python3 or C-bindings.
 */
function extractTextFromPdfBufferPureNode(buffer: Buffer): {
  pages: ExtractedPage[];
  fullText: string;
  totalPages: number;
} {
  const textPages: ExtractedPage[] = [];
  const fullTextParts: string[] = [];
  const bufferStr = buffer.toString("binary");

  // Regex to match PDF content streams
  const streamRegex = /stream\r?\n([\s\S]*?)\r?\nendstream/g;
  let match: RegExpExecArray | null;
  let pageIndex = 1;

  while ((match = streamRegex.exec(bufferStr)) !== null) {
    const rawStream = Buffer.from(match[1], "binary");
    let streamText = "";

    try {
      const decompressed = zlib.inflateSync(rawStream);
      streamText = decompressed.toString("latin1");
    } catch {
      try {
        const decompressed = zlib.unzipSync(rawStream);
        streamText = decompressed.toString("latin1");
      } catch {
        streamText = rawStream.toString("latin1");
      }
    }

    // Look for text in BT ... ET blocks
    const btRegex = /BT[\s\S]*?ET/g;
    let btMatch: RegExpExecArray | null;
    let pageChunk = "";

    while ((btMatch = btRegex.exec(streamText)) !== null) {
      const block = btMatch[0];

      // Extract (text) Tj
      const tjRegex = /\(([^)]*)\)\s*Tj/g;
      let tjMatch: RegExpExecArray | null;
      while ((tjMatch = tjRegex.exec(block)) !== null) {
        pageChunk += tjMatch[1] + " ";
      }

      // Extract [(text)] TJ
      const tjArrayRegex = /\[(.*?)\]\s*TJ/g;
      let arrayMatch: RegExpExecArray | null;
      while ((arrayMatch = tjArrayRegex.exec(block)) !== null) {
        const inner = arrayMatch[1];
        const innerTjRegex = /\(([^)]*)\)/g;
        let innerMatch: RegExpExecArray | null;
        while ((innerMatch = innerTjRegex.exec(inner)) !== null) {
          pageChunk += innerMatch[1] + " ";
        }
      }
      pageChunk += "\n";
    }

    if (pageChunk.trim().length > 10) {
      const cleaned = pageChunk
        .replace(/\\([0-9]{3})/g, (_, oct) => String.fromCharCode(parseInt(oct, 8)))
        .replace(/\\([\\()])/g, "$1")
        .replace(/\r/g, "")
        .replace(/\n\s*\n+/g, "\n")
        .trim();

      if (cleaned.length > 15) {
        textPages.push({ pageNumber: pageIndex, text: cleaned });
        fullTextParts.push(`--- PAGE ${pageIndex} ---\n${cleaned}`);
        pageIndex++;
      }
    }
  }

  // Fallback: search for readable strings in parentheses
  if (textPages.length === 0) {
    const parenMatches = bufferStr.match(/\([A-Za-z0-9 ,.\-:;'/"]{4,}\)/g);
    if (parenMatches && parenMatches.length > 5) {
      const fallbackText = parenMatches
        .map((p) => p.slice(1, -1))
        .join(" ")
        .replace(/\s+/g, " ")
        .trim();
      if (fallbackText.length > 20) {
        textPages.push({ pageNumber: 1, text: fallbackText });
        fullTextParts.push(`--- PAGE 1 ---\n${fallbackText}`);
      }
    }
  }

  return {
    pages: textPages,
    fullText: fullTextParts.join("\n\n"),
    totalPages: textPages.length || 1,
  };
}

/**
 * Extracts verified page-by-page text from a PDF file using PyMuPDF / pdftotext
 * with an automatic pure Node.js fallback when Python is unavailable (e.g. Vercel).
 */
export async function parsePdfBufferOrFile(
  input: { buffer?: Buffer; filePath?: string }
): Promise<ParseResult> {
  let tempFilePath: string | null = null;
  let fileBuffer: Buffer | null = input.buffer || null;

  try {
    let targetPath = input.filePath;

    if (!targetPath && fileBuffer) {
      const tempDir = path.resolve(os.tmpdir(), "vidhik_scratch");
      if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true });
      tempFilePath = path.join(tempDir, `upload_${Date.now()}.pdf`);
      fs.writeFileSync(tempFilePath, fileBuffer);
      targetPath = tempFilePath;
    }

    if (targetPath && !fileBuffer && fs.existsSync(/*turbopackIgnore: true*/ targetPath)) {
      try {
        fileBuffer = fs.readFileSync(/*turbopackIgnore: true*/ targetPath);
      } catch {}
    }

    if (!targetPath || !fs.existsSync(/*turbopackIgnore: true*/ targetPath)) {
      return {
        success: false,
        pages: [],
        fullText: "",
        totalPages: 0,
        error: "DOCUMENT_NOT_FOUND: Document file does not exist on disk.",
      };
    }

    // Attempt 1: Run python script using PyMuPDF (pymupdf)
    try {
      const script = `
import json, sys, warnings
warnings.filterwarnings("ignore")
try:
    import pymupdf as fitz
except ImportError:
    import fitz

pdf_path = sys.argv[1]
try:
    doc = fitz.open(pdf_path)
    pages = []
    full_text_list = []
    for i, p in enumerate(doc):
        txt = p.get_text() or ""
        pages.append({"pageNumber": i + 1, "text": txt.strip()})
        if txt.strip():
            full_text_list.append(f"--- PAGE {i + 1} ---\\n" + txt.strip())
    
    total_chars = sum(len(p["text"]) for p in pages)
    print(json.dumps({
        "success": total_chars > 20,
        "totalPages": len(doc),
        "pages": pages,
        "fullText": "\\n\\n".join(full_text_list),
        "totalChars": total_chars
    }))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e), "totalPages": 0, "pages": [], "fullText": ""}))
`;

      const cmd = `python3 -c '${script.replace(/'/g, "'\\''")}' "${targetPath}"`;
      const { stdout } = await execAsync(cmd, { timeout: 15000, maxBuffer: 10 * 1024 * 1024 });

      const trimmed = stdout.trim();
      const jsonMatch = trimmed.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const result = JSON.parse(jsonMatch[0]);
        if (result.success && result.fullText && result.fullText.trim().length > 0) {
          return {
            success: true,
            pages: result.pages,
            fullText: result.fullText,
            totalPages: result.totalPages,
          };
        }
      }
    } catch {
      // Python unavailable or pymupdf failed (e.g. running on Vercel serverless)
    }

    // Attempt 2: High-fidelity extraction via Laptop AI Gateway (local PyMuPDF on inference host)
    if (fileBuffer && fileBuffer.length > 0 && process.env.AI_GATEWAY_URL) {
      try {
        const gatewayBase = process.env.AI_GATEWAY_URL.replace(/\/+$/, "");
        const extractUrl = gatewayBase.endsWith("/api/extract-pdf")
          ? gatewayBase
          : `${gatewayBase}/api/extract-pdf`;
        const rawToken = process.env.AI_GATEWAY_TOKEN || process.env.GATEWAY_TOKEN || "";
        const token = rawToken.trim().replace(/^["']|["']$/g, "");

        const headers: Record<string, string> = {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        };
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
          headers["x-gateway-token"] = token;
        }

        const res = await fetch(extractUrl, {
          method: "POST",
          headers,
          body: JSON.stringify({
            pdf_base64: fileBuffer.toString("base64"),
          }),
          signal: AbortSignal.timeout(30000),
        });

        if (res.ok) {
          const data = await res.json();
          if (data.success && data.fullText && data.fullText.trim().length > 0) {
            return {
              success: true,
              pages: data.pages || [],
              fullText: data.fullText,
              totalPages: data.totalPages || 1,
            };
          }
        }
      } catch (gwErr: any) {
        console.warn("Laptop AI Gateway PDF extraction fallback:", gwErr.message);
      }
    }

    // Attempt 3: Pure Node.js stream extractor fallback
    if (fileBuffer && fileBuffer.length > 0) {
      const pureResult = extractTextFromPdfBufferPureNode(fileBuffer);
      if (pureResult.fullText.trim().length > 20) {
        return {
          success: true,
          pages: pureResult.pages,
          fullText: pureResult.fullText,
          totalPages: pureResult.totalPages,
        };
      }
    }

    return {
      success: false,
      pages: [],
      fullText: "",
      totalPages: 0,
      error:
        "INSUFFICIENT_SOURCE_EVIDENCE: Document contains zero extractable text (scanned image or empty record).",
    };
  } catch (err: any) {
    return {
      success: false,
      pages: [],
      fullText: "",
      totalPages: 0,
      error: `EXTRACTION_FAILED: ${err.message}`,
    };
  } finally {
    if (tempFilePath && fs.existsSync(tempFilePath)) {
      try {
        fs.unlinkSync(tempFilePath);
      } catch {}
    }
  }
}
