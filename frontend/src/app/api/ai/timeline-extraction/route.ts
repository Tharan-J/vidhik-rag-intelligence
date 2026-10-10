import { NextResponse } from "next/server";
import { extractTimelineEvents } from "@/lib/ai/gemini";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { documentName, documentText } = body;

    if (!documentName || !documentText) {
      return NextResponse.json(
        { error: "documentName and documentText are required." },
        { status: 400 }
      );
    }

    const events = await extractTimelineEvents({
      documentName,
      documentText,
    });

    return NextResponse.json({
      events,
      model: "gemini-3.5-flash-lite",
      extracted_at: new Date().toISOString(),
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: err.message || "Failed to extract timeline events" },
      { status: 500 }
    );
  }
}
