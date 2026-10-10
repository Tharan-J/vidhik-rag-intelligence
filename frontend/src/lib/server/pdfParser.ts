import { exec } from "child_process";
import { promisify } from "util";
import fs from "fs";
import path from "path";

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
 * Extracts verified page-by-page text from a PDF file using PyMuPDF / pdftotext.
 * Returns exact page text and total pages.
 * Fails closed if the document is encrypted, corrupt, or contains no extractable text.
 */
export async function parsePdfBufferOrFile(
  input: { buffer?: Buffer; filePath?: string }
): Promise<ParseResult> {
  let tempFilePath: string | null = null;

  try {
    let targetPath = input.filePath;

    if (!targetPath && input.buffer) {
      const tempDir = path.resolve(process.cwd(), "..", "prototype", "scratch");
      if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true });
      tempFilePath = path.join(tempDir, `upload_${Date.now()}.pdf`);
      fs.writeFileSync(tempFilePath, input.buffer);
      targetPath = tempFilePath;
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

    // Run python script using PyMuPDF (pymupdf) to extract verified page-by-page text
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
    if (!jsonMatch) {
      throw new Error(`Failed to extract JSON from Python output: ${trimmed.slice(0, 200)}`);
    }
    const result = JSON.parse(jsonMatch[0]);

    if (!result.success || !result.fullText || result.fullText.trim().length === 0) {
      return {
        success: false,
        pages: [],
        fullText: "",
        totalPages: result.totalPages || 0,
        error:
          result.error ||
          "INSUFFICIENT_SOURCE_EVIDENCE: Document contains zero extractable text (scanned image or empty record).",
      };
    }

    return {
      success: true,
      pages: result.pages,
      fullText: result.fullText,
      totalPages: result.totalPages,
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
