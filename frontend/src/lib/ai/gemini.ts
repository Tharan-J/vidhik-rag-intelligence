/**
 * Server-Side Gemini Intelligence Utility
 * ========================================
 * Uses model: gemini-3.5-flash-lite
 *
 * RESTRICTED RESPONSIBILITIES:
 * 1. Matter document metadata extraction
 * 2. Preliminary case/matter summarization
 * 3. Timeline/date extraction from uploaded matter documents
 * 4. Identifying candidate issues from matter documents
 * 5. Structuring unstructured lawyer notes
 *
 * CRITICAL ARCHITECTURAL RULE:
 * Gemini MUST NOT perform authoritative legal retrieval, legal research,
 * statutory determination, citation fabrication, or replace Vidhik's BGE-M3 + BM25 + Qdrant + Qwen RAG pipeline.
 */

const GEMINI_API_KEY =
  process.env.GEMINI_API_KEY ||
  process.env.NEXT_SERVER_GEMINI_API_KEY ||
  "";

const GEMINI_MODEL = "gemini-3.5-flash-lite";
const GEMINI_API_ENDPOINT = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent`;

interface GeminiGenerateOptions {
  systemInstruction?: string;
  temperature?: number;
  timeoutMs?: number;
  maxOutputTokens?: number;
}

/**
 * Low-level server-side invocation to gemini-3.5-flash-lite with JSON response constraint.
 */
export async function callGeminiJSON<T = any>(
  prompt: string,
  options: GeminiGenerateOptions = {}
): Promise<T> {
  if (!GEMINI_API_KEY) {
    throw new Error(
      "GEMINI_API_KEY is not configured in the server environment. Please set GEMINI_API_KEY."
    );
  }

  const timeoutMs = options.timeoutMs || 25000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const payload: any = {
    contents: [
      {
        parts: [{ text: prompt }],
      },
    ],
    generationConfig: {
      responseMimeType: "application/json",
      temperature: options.temperature !== undefined ? options.temperature : 0.1,
      maxOutputTokens: options.maxOutputTokens || 8192,
    },
  };

  if (options.systemInstruction) {
    payload.systemInstruction = {
      parts: [{ text: options.systemInstruction }],
    };
  }

  try {
    const url = `${GEMINI_API_ENDPOINT}?key=${GEMINI_API_KEY}`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errText = await response.text().catch(() => "");
      throw new Error(
        `Gemini API returned status ${response.status}: ${errText.slice(0, 300)}`
      );
    }

    const data = await response.json();
    const rawContent = data.candidates?.[0]?.content?.parts?.[0]?.text;

    if (!rawContent) {
      throw new Error("Gemini returned empty candidate response.");
    }

    return cleanAndParseJSON<T>(rawContent);
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new Error(`Gemini request timed out after ${timeoutMs}ms.`);
    }
    throw err;
  }
}

function cleanAndParseJSON<T = any>(raw: string): T {
  let cleaned = raw.trim();

  // 1. Strip markdown code fences if present
  if (cleaned.startsWith("```json")) {
    cleaned = cleaned.replace(/^```json\s*/i, "").replace(/\s*```$/, "");
  } else if (cleaned.startsWith("```")) {
    cleaned = cleaned.replace(/^```\s*/, "").replace(/\s*```$/, "");
  }
  cleaned = cleaned.trim();

  // 2. Try standard parse first
  try {
    return JSON.parse(cleaned) as T;
  } catch (initialErr) {
    // 3. Automated repair of common LLM JSON syntax issues
    try {
      let repaired = cleaned;
      // Remove trailing commas in objects and arrays
      repaired = repaired.replace(/,\s*([}\]])/g, "$1");
      // Fix unquoted property names: { propertyName: ... } -> { "propertyName": ... }
      repaired = repaired.replace(/([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)/g, '$1"$2"$3');
      // Fix single-quoted property names: { 'propertyName': ... } -> { "propertyName": ... }
      repaired = repaired.replace(/([{,]\s*)'([^']+)'(\s*:)/g, '$1"$2"$3');

      return JSON.parse(repaired) as T;
    } catch {
      // 4. Handle truncated structures (unclosed strings, dangling keys, unclosed braces/brackets)
      try {
        let s = cleaned;
        s = s.replace(/,\s*([}\]])/g, "$1");
        s = s.replace(/([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)/g, '$1"$2"$3');
        s = s.replace(/([{,]\s*)'([^']+)'(\s*:)/g, '$1"$2"$3');

        let inString = false;
        let escaped = false;
        const stack: string[] = [];
        for (let i = 0; i < s.length; i++) {
          const ch = s[i];
          if (inString) {
            if (escaped) escaped = false;
            else if (ch === "\\") escaped = true;
            else if (ch === '"') inString = false;
          } else {
            if (ch === '"') inString = true;
            else if (ch === "{" || ch === "[") stack.push(ch);
            else if (ch === "}" && stack[stack.length - 1] === "{") stack.pop();
            else if (ch === "]" && stack[stack.length - 1] === "[") stack.pop();
          }
        }

        let repaired = s;
        if (inString) repaired += '"';
        repaired = repaired.replace(/,\s*"[^"]*"\s*:\s*$/, "");
        repaired = repaired.replace(/,\s*"[^"]*"\s*$/, "");
        repaired = repaired.replace(/,\s*$/, "");

        while (stack.length > 0) {
          const top = stack.pop();
          if (top === "{") repaired += "}";
          else if (top === "[") repaired += "]";
        }

        return JSON.parse(repaired) as T;
      } catch {
        // 5. Try extracting the outermost valid JSON object
        const startBrace = cleaned.indexOf("{");
        const endBrace = cleaned.lastIndexOf("}");
        if (startBrace !== -1 && endBrace !== -1 && endBrace > startBrace) {
          try {
            let block = cleaned.slice(startBrace, endBrace + 1);
            block = block.replace(/,\s*([}\]])/g, "$1");
            return JSON.parse(block) as T;
          } catch {}
        }
        throw initialErr;
      }
    }
  }
}

/**
 * Free-text invocation to gemini-3.5-flash-lite.
 */
export async function callGeminiText(
  prompt: string,
  options: GeminiGenerateOptions = {}
): Promise<string> {
  if (!GEMINI_API_KEY) {
    throw new Error(
      "GEMINI_API_KEY is not configured in the server environment. Please set GEMINI_API_KEY."
    );
  }

  const timeoutMs = options.timeoutMs || 25000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const payload: any = {
    contents: [
      {
        parts: [{ text: prompt }],
      },
    ],
    generationConfig: {
      temperature: options.temperature !== undefined ? options.temperature : 0.2,
    },
  };

  if (options.systemInstruction) {
    payload.systemInstruction = {
      parts: [{ text: options.systemInstruction }],
    };
  }

  try {
    const url = `${GEMINI_API_ENDPOINT}?key=${GEMINI_API_KEY}`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errText = await response.text().catch(() => "");
      throw new Error(
        `Gemini API returned status ${response.status}: ${errText.slice(0, 300)}`
      );
    }

    const data = await response.json();
    const rawContent = data.candidates?.[0]?.content?.parts?.[0]?.text;

    if (!rawContent) {
      throw new Error("Gemini returned empty candidate response.");
    }

    return rawContent;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new Error(`Gemini request timed out after ${timeoutMs}ms.`);
    }
    throw err;
  }
}

/**
 * 1. Generate Structured Matter Summary for Overview tab
 */
export async function generateMatterSummary(params: {
  title: string;
  caseNumber?: string;
  court?: string;
  parties: { petitioner?: string; respondent?: string };
  documentSummaries: string[];
}): Promise<{
  summary: string;
  current_status: string;
  important_dates: { label: string; date: string; source: string }[];
  key_issues: string[];
  documents_requiring_attention: string[];
}> {
  const prompt = `
Analyze the following Indian judicial matter documents and metadata:
Matter Title: ${params.title}
Case Number: ${params.caseNumber || "N/A"}
Court: ${params.court || "N/A"}
Petitioner: ${params.parties.petitioner || "N/A"}
Respondent: ${params.parties.respondent || "N/A"}

Uploaded Documents Summary:
${params.documentSummaries.join("\n")}

STRICT INSTRUCTIONS:
- Extract and summarize only what is explicitly in the provided matter record.
- Do not invent legal authorities, facts, or citations.
- Return a JSON object with this exact shape:
{
  "summary": "2-3 concise sentences summarizing what the matter is about",
  "current_status": "Concise statement of current stage and pending actions",
  "important_dates": [
    { "label": "event name", "date": "YYYY-MM-DD", "source": "originating document name" }
  ],
  "key_issues": ["Issue 1", "Issue 2"],
  "documents_requiring_attention": ["Document name"]
}
`;

  return callGeminiJSON(prompt, {
    systemInstruction:
      "You are Vidhik's auxiliary matter organizer. Provide strictly factual, restrained legal workspace organization in JSON format without inventing missing details.",
    temperature: 0.1,
  });
}

/**
 * 2. Structured Document Intelligence Metadata Extraction
 */
export async function extractDocumentMetadata(params: {
  documentName: string;
  documentTypeHint?: string;
  documentTextSnippet: string;
}): Promise<{
  document_type: string;
  case_number: string | null;
  court: string | null;
  parties: string[];
  dates: string[];
  sections: string[];
  important_points: string[];
}> {
  const prompt = `
Extract structured legal metadata from this Indian court document:
Document Name: ${params.documentName}
Document Type Hint: ${params.documentTypeHint || "Unknown"}

Document Excerpt:
"""
${params.documentTextSnippet.slice(0, 4000)}
"""

STRICT INSTRUCTIONS:
- Extract ONLY facts explicitly stated in the excerpt.
- If court, case number, or parties are absent, set them to null or empty list.
- Do not fabricate case law or statutory numbers.
- Return JSON matching this exact structure:
{
  "document_type": "string describing type (e.g. Pleadings, Interlocutory Application, Order, Judgment)",
  "case_number": "case number if present, else null",
  "court": "court name if present, else null",
  "parties": ["names of parties mentioned"],
  "dates": ["dates mentioned in YYYY-MM-DD or readable format"],
  "sections": ["statutory sections explicitly cited in text"],
  "important_points": ["2-4 factual bullet points stated in document"]
}
`;

  return callGeminiJSON(prompt, {
    systemInstruction:
      "You are a strict legal document parser. Extract only verified verbatim elements present in the text snippet.",
    temperature: 0.05,
  });
}

/**
 * 3. Timeline / Date Extraction from Matter Document
 */
export async function extractTimelineEvents(params: {
  documentName: string;
  documentText: string;
}): Promise<
  Array<{
    date: string;
    title: string;
    description: string;
    sourceDocument: string;
  }>
> {
  const prompt = `
Extract chronological dates and events from this matter document:
Document Name: ${params.documentName}

Content:
"""
${params.documentText.slice(0, 3500)}
"""

STRICT INSTRUCTIONS:
- Identify explicit dates mentioned and their associated judicial/procedural events.
- Output JSON array of objects:
[
  {
    "date": "YYYY-MM-DD or DD Month YYYY",
    "title": "Short event title (e.g. Trial Court Decree, Notice Issued, Order Passed)",
    "description": "Factual 1-sentence description based on text",
    "sourceDocument": "${params.documentName}"
  }
]
`;

  const res = await callGeminiJSON<{ events: any[] } | any[]>(prompt, {
    temperature: 0.1,
  });

  if (Array.isArray(res)) return res;
  if (res && Array.isArray(res.events)) return res.events;
  return [];
}

/**
 * 4. Suggest Candidate Issues from Matter Documents
 */
export async function suggestCandidateIssues(params: {
  matterTitle: string;
  documentSnippets: string[];
}): Promise<
  Array<{
    title: string;
    description: string;
    relatedSections: string[];
  }>
> {
  const prompt = `
Identify candidate legal issues that arise from these Indian court matter documents:
Matter Title: ${params.matterTitle}

Document Excerpts:
${params.documentSnippets.join("\n---\n").slice(0, 4000)}

STRICT INSTRUCTIONS:
- Frame issues as objective legal questions (e.g. "Whether the delay of 48 days is condonable under Section 5 of the Limitation Act?").
- These will be presented to the lawyer as "AI-suggested issues" requiring lawyer confirmation.
- Output JSON array:
[
  {
    "title": "Question starting with Whether...",
    "description": "Brief context from document records",
    "relatedSections": ["Sections referenced"]
  }
]
`;

  const res = await callGeminiJSON<{ issues: any[] } | any[]>(prompt, {
    temperature: 0.15,
  });

  if (Array.isArray(res)) return res;
  if (res && Array.isArray(res.issues)) return res.issues;
  return [];
}

/**
 * 5. Structure Unstructured Lawyer Notes
 */
export async function structureLawyerNotes(notesText: string): Promise<{
  title: string;
  structuredPoints: string[];
  suggestedTags: string[];
  actionItems: string[];
}> {
  const prompt = `
Structure the following raw lawyer matter notes into clean workspace headings:
Raw Notes:
"""
${notesText}
"""

Output JSON:
{
  "title": "Clean concise title",
  "structuredPoints": ["Point 1", "Point 2"],
  "suggestedTags": ["Tag1", "Tag2"],
  "actionItems": ["Action item if any"]
}
`;

  return callGeminiJSON(prompt, {
    temperature: 0.1,
  });
}
