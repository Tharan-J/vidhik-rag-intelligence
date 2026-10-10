import { NextResponse } from "next/server";
import { extractDocumentMetadata } from "@/lib/ai/gemini";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { documentName, documentTypeHint, documentTextSnippet } = body;

    if (!documentName || !documentTextSnippet) {
      return NextResponse.json(
        { error: "documentName and documentTextSnippet are required." },
        { status: 400 }
      );
    }

    const metadata = await extractDocumentMetadata({
      documentName,
      documentTypeHint,
      documentTextSnippet,
    });

    return NextResponse.json({
      metadata,
      model: "gemini-3.5-flash-lite",
      extracted_at: new Date().toISOString(),
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: err.message || "Failed to extract document metadata" },
      { status: 500 }
    );
  }
}
