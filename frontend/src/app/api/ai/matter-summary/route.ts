import { NextResponse } from "next/server";
import { generateMatterSummary } from "@/lib/ai/gemini";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { title, caseNumber, court, parties, documentSummaries } = body;

    if (!title) {
      return NextResponse.json(
        { error: "Matter title is required for summary generation." },
        { status: 400 }
      );
    }

    const summaryResult = await generateMatterSummary({
      title,
      caseNumber,
      court,
      parties: parties || {},
      documentSummaries: documentSummaries || [],
    });

    return NextResponse.json({
      summary: summaryResult,
      model: "gemini-3.5-flash-lite",
      generated_at: new Date().toISOString(),
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: err.message || "Failed to generate matter summary" },
      { status: 500 }
    );
  }
}
