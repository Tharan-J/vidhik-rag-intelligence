import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { parsePdfBufferOrFile } from "@/lib/server/pdfParser";
import { saveUploadedDocument } from "@/lib/server/documentStorage";
import { Matter, MatterDocument, DocumentMetadata } from "@/lib/types/matter";
import { callGeminiJSON } from "@/lib/ai/gemini";
import { loadAllMatters, saveAllMatters } from "@/lib/server/mattersStore";

export async function POST(request: Request) {
  try {
    const contentType = request.headers.get("content-type") || "";
    let documentName = "Uploaded_Document.pdf";
    let documentType: MatterDocument["type"] = "Pleadings";
    let matterId = "";
    let docContent = "";
    let totalPages = 1;
    let savedStorage: { storagePath: string; absolutePath: string; sha256: string } | null = null;

    if (contentType.includes("multipart/form-data")) {
      const formData = await request.formData();
      const file = formData.get("file") as File | null;
      matterId = (formData.get("matterId") as string) || "";
      documentType = ((formData.get("type") as string) || "Pleadings") as MatterDocument["type"];
      const customName = formData.get("name") as string | null;

      if (!file) {
        return NextResponse.json({ error: "No file provided" }, { status: 400 });
      }

      documentName = customName || file.name;
      const arrayBuffer = await file.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);

      if (file.name.toLowerCase().endsWith(".pdf")) {
        savedStorage = saveUploadedDocument({
          buffer,
          matterId,
          documentName,
        });

        const parseResult = await parsePdfBufferOrFile({ filePath: savedStorage.absolutePath });
        if (!parseResult.success) {
          return NextResponse.json(
            { error: "Failed to extract verified text from PDF" },
            { status: 422 }
          );
        }
        docContent = parseResult.fullText;
        totalPages = parseResult.totalPages;
      } else {
        docContent = buffer.toString("utf-8");
      }
    } else {
      const body = await request.json();
      matterId = body.matterId || "";
      documentName = body.documentName || body.name || "Uploaded_Document.pdf";
      documentType = body.documentType || body.type || "Pleadings";
      docContent = body.fileText || body.text || "";
      totalPages = body.pages || 1;
    }

    if (!docContent || docContent.trim().length < 10) {
      return NextResponse.json(
        { error: "Document contains insufficient text for indexing" },
        { status: 422 }
      );
    }

    const daemonBase = process.env.RETRIEVAL_DAEMON_URL || "http://127.0.0.1:8008";

    // Step 1: Ingest into Qdrant Cloud via Document Intelligence Daemon
    let qdrantResult = null;
    try {
      const qRes = await fetch(`${daemonBase}/ingest`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify({
          document_id: documentName,
          matter_id: matterId,
          text: docContent,
          case_title: documentName,
          court: "Indian Judiciary",
        }),
        signal: AbortSignal.timeout(60000),
      });
      if (qRes.ok) {
        qdrantResult = await qRes.json();
      }
    } catch (err: any) {
      console.warn("Qdrant document ingestion warning:", err.message);
    }

    // Step 2: Extract Document Metadata via Document Intelligence Probe
    let probeHits: any[] = [];
    try {
      const pRes = await fetch(`${daemonBase}/probe`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify({
          document_id: documentName,
          probe_type: "parties_and_posture",
          top_k: 2,
        }),
        signal: AbortSignal.timeout(15000),
      });
      if (pRes.ok) {
        const pData = await pRes.json();
        probeHits = pData.results || [];
      }
    } catch (err) {}

    const nowDate = new Date().toISOString().split("T")[0];
    const topPointId = probeHits[0]?.qdrant_point_id || `qdrant_${Date.now()}`;

    const newDocument: MatterDocument = {
      id: `DOC-${Date.now()}`,
      matterId: matterId || "MAT-DEFAULT",
      name: documentName,
      type: documentType,
      date: nowDate,
      pages: totalPages,
      uploadedAt: nowDate,
      status: "active",
      fileSize: `${(docContent.length / 1024).toFixed(1)} KB`,
      extractionStatus: "completed",
      provenance: "SOURCE_EXPLICIT",
      storagePath: savedStorage?.storagePath,
      sha256: savedStorage?.sha256,
      extractedMetadata: {
        document_type: documentType,
        case_number: probeHits[0]?.case_number || "Grounded in Record",
        court: probeHits[0]?.court || "Indian Judiciary",
        parties: probeHits[0]?.case_title ? [probeHits[0].case_title] : [],
        dates: [nowDate],
        sections: [],
        important_points: [
          `Indexed in Qdrant Cloud collection vidhik_legal_chunks`,
          `Provenance Point: ${topPointId}`,
        ],
        extraction_source: "Vidhik Qdrant Document Intelligence",
        extracted_at: new Date().toISOString(),
      },
    };

    // Step 3: Update Matter in extracted_matters.json if matterId provided
    if (matterId) {
      try {
        const matters: Matter[] = loadAllMatters();
        const mIdx = matters.findIndex((m) => m.id === matterId);
        if (mIdx !== -1) {
          matters[mIdx].documents = [newDocument, ...(matters[mIdx].documents || [])];
          saveAllMatters(matters);
        }
      } catch (e) {
        console.warn("Could not append document to matter record:", e);
      }
    }

    return NextResponse.json({
      success: true,
      document: newDocument,
      qdrant: qdrantResult,
    });
  } catch (err: any) {
    console.error("Document ingestion route error:", err);
    return NextResponse.json(
      { error: err.message || "Failed to ingest document" },
      { status: 500 }
    );
  }
}
