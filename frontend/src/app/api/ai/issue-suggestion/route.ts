import { NextResponse } from "next/server";
import { suggestCandidateIssues } from "@/lib/ai/gemini";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { matterTitle, documentSnippets } = body;

    if (!matterTitle || !documentSnippets || !documentSnippets.length) {
      return NextResponse.json(
        { error: "matterTitle and documentSnippets are required." },
        { status: 400 }
      );
    }

    const issues = await suggestCandidateIssues({
      matterTitle,
      documentSnippets,
    });

    return NextResponse.json({
      issues,
      model: "gemini-3.5-flash-lite",
      generated_at: new Date().toISOString(),
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: err.message || "Failed to suggest candidate issues" },
      { status: 500 }
    );
  }
}
