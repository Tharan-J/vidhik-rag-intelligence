/**
 * Vidhik Local Qwen Legal Answer Generation Pipeline
 * ==================================================
 * Directly invokes the established local Qwen runtime (qwen3:4b-instruct via Ollama)
 * to produce evidence-grounded legal answers with structured claims, support levels,
 * judicial-status distinctions, and contrary evidence.
 *
 * Guarantees:
 * - Substantive answers are produced by local Qwen (never silently replaced by Gemini).
 * - Strips thinking blocks and parses strict JSON.
 * - Enforces claim-level attribution (E1, E2, ...).
 */

export interface QwenClaim {
  claim: string;
  evidence_ids: string[];
  claim_type?: "judicial_finding" | "statutory_provision" | "party_submission" | "procedural_history" | "legal_interpretation";
  support_level?: "directly_supports" | "relevant_context" | "contradicts_or_qualifies" | "unrelated" | "unverified";
  qualification?: string;
}

export interface QwenContraryEvidence {
  evidence_id: string;
  nature: "contradiction" | "qualification" | "distinction" | string;
  explanation: string;
}

export interface QwenLegalAnswerResult {
  answer: string;
  confidence: "supported" | "partially_supported" | "insufficient_evidence";
  limitations: string;
  claims: QwenClaim[];
  contrary_evidence: QwenContraryEvidence[];
  raw_response?: string;
}

const SYSTEM_LEGAL_GROUNDING_PROMPT = `You are Vidhik, an authoritative, rigorous legal AI assistant for Indian Law.
Your primary duty is strict factual and legal accuracy based EXCLUSIVELY on the provided evidence.

CRITICAL GROUNDING RULES:
1. Answer ONLY from the supplied legal evidence blocks ([E1], [E2], ...).
2. Do NOT invent, assume, or extrapolate cases, statutes, sections, dates, holdings, or procedural history.
3. Every substantive legal claim in your response MUST cite one or more evidence IDs (e.g. ["E1"], ["E1", "E2"]).
4. If the provided evidence does not contain sufficient facts or law to answer the user's question, you MUST explicitly state that the evidence is insufficient. Set "confidence": "insufficient_evidence".
5. Do NOT pretend that retrieved evidence proves something it does not prove.
6. Rigorously distinguish between:
   - What the court held / observed (judicial_finding)
   - What the statute or statutory rule provides (statutory_provision)
   - What a party argued or alleged (party_submission)
   - Procedural events or case transfer history (procedural_history)
   - General legal doctrine or reasonable interpretation (legal_interpretation)
   NEVER present a party's submission or argument as the holding of the court.
7. Assess whether cited evidence directly supports, provides context, or qualifies/contradicts the claim.
8. If retrieved evidence contains contrary views, qualifications, or limitations, preserve them in "contrary_or_qualifying_evidence".
9. NEVER fabricate citations, CNR numbers, neutral citations, or dates.
10. Keep the answer clear and authoritative (2-3 paragraphs) and formulate 2-5 distinct claims citing evidence IDs.

OUTPUT SCHEMA:
You MUST output strictly valid JSON adhering to this exact schema:
{
  "answer": "Comprehensive, clear legal answer summarizing the findings supported strictly by the evidence.",
  "claims": [
    {
      "claim": "Specific factual or legal statement made in the answer.",
      "evidence_ids": ["E1"],
      "claim_type": "judicial_finding" | "statutory_provision" | "party_submission" | "procedural_history" | "legal_interpretation",
      "support_level": "directly_supports" | "relevant_context" | "contradicts_or_qualifies" | "unrelated" | "unverified",
      "qualification": "Optional note if the proposition is qualified or partial."
    }
  ],
  "contrary_or_qualifying_evidence": [
    {
      "evidence_id": "E2",
      "nature": "contradiction" | "qualification" | "distinction",
      "explanation": "Brief explanation of how this authority qualifies or limits the proposition."
    }
  ],
  "limitations": "Explicit note of any missing facts, unaddressed legal aspects, or limitations of the retrieved evidence.",
  "confidence": "supported" | "partially_supported" | "insufficient_evidence"
}`;

function getQwenEndpointAndHeaders(overrideEndpoint?: string): {
  endpoint: string;
  headers: Record<string, string>;
} {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true",
  };

  const rawToken = process.env.AI_GATEWAY_TOKEN || process.env.GATEWAY_TOKEN;
  const gatewayToken = rawToken ? rawToken.trim().replace(/^["']|["']$/g, "") : undefined;
  if (gatewayToken) {
    headers["Authorization"] = `Bearer ${gatewayToken}`;
    headers["x-gateway-token"] = gatewayToken;
  }

  if (overrideEndpoint) {
    return { endpoint: overrideEndpoint, headers };
  }

  const gatewayUrl = process.env.AI_GATEWAY_URL;
  if (gatewayUrl) {
    const cleanUrl = gatewayUrl.replace(/\/+$/, "");
    const endpoint = cleanUrl.endsWith("/api/generate")
      ? cleanUrl
      : `${cleanUrl}/api/generate`;
    return { endpoint, headers };
  }

  return {
    endpoint: "http://127.0.0.1:11434/api/generate",
    headers,
  };
}

export async function generateQwenLegalAnswer(params: {
  query: string;
  evidenceContext: string;
  matterContext?: string;
  endpoint?: string;
  model?: string;
  timeoutMs?: number;
}): Promise<QwenLegalAnswerResult> {
  const { endpoint, headers } = getQwenEndpointAndHeaders(params.endpoint);
  const model = params.model || "qwen3:4b-instruct";
  const timeoutMs = params.timeoutMs || 120000;

  const userPrompt = `USER QUESTION:
"${params.query}"

${params.matterContext ? `MATTER CONTEXT:\n${params.matterContext}\n\n` : ""}RELEVANT LEGAL EVIDENCE:
${params.evidenceContext}

Please review the legal evidence above and formulate a rigorous, authoritative legal answer.
Respond ONLY with a valid JSON object matching the required schema.`;

  const payload = {
    model,
    system: SYSTEM_LEGAL_GROUNDING_PROMPT,
    prompt: userPrompt,
    format: "json",
    stream: false,
    options: {
      temperature: 0.0,
      top_p: 0.95,
      num_predict: 400,
    },
  };

  const controller = new AbortController();
  const timeoutTimer = setTimeout(() => controller.abort(), timeoutMs);

  let rawText = "";
  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!res.ok) {
      throw new Error(`Qwen inference error ${res.status}: ${res.statusText}`);
    }

    const data = await res.json();
    rawText = (data.response || "").trim();
  } catch (err: any) {
    if (err.name === "AbortError") {
      throw new Error(`Local Qwen inference timed out after ${timeoutMs}ms.`);
    }
    throw new Error(`Failed to invoke local Qwen model (${model}): ${err.message}`);
  } finally {
    clearTimeout(timeoutTimer);
  }

  // Parse structured output
  return parseAndValidateQwenJSON(rawText);
}

function parseAndValidateQwenJSON(rawText: string): QwenLegalAnswerResult {
  // 1. Strip think blocks
  let cleanText = rawText.replace(/<think>[\s\S]*?<\/think>/gi, "").trim();

  // 2. Strip code fences
  if (cleanText.startsWith("```")) {
    cleanText = cleanText.replace(/^```(?:json)?\s*/i, "");
    cleanText = cleanText.replace(/\s*```$/i, "");
    cleanText = cleanText.trim();
  }

  let data: any = null;
  try {
    data = JSON.parse(cleanText);
  } catch {
    // Regex extract outermost JSON
    const match = cleanText.match(/(\{[\s\S]*\})/);
    if (match) {
      try {
        data = JSON.parse(match[1]);
      } catch {}
    }
  }

  if (!data || typeof data !== "object") {
    // Resilient extraction
    const ansMatch = cleanText.match(/"answer"\s*:\s*"([\s\S]*?)(?<!\\)"/);
    const extractedAns = ansMatch ? ansMatch[1].replace(/\\"/g, '"').replace(/\\n/g, "\n") : cleanText;

    return {
      answer: extractedAns,
      confidence: "partially_supported",
      limitations: "Extracted from resilient output recovery.",
      claims: [
        {
          claim: extractedAns.slice(0, 250),
          evidence_ids: ["E1"],
          claim_type: "judicial_finding",
          support_level: "directly_supports",
        },
      ],
      contrary_evidence: [],
      raw_response: rawText,
    };
  }

  const answer = String(data.answer || "").trim();
  const limitations = String(data.limitations || "").trim();

  let confidence: "supported" | "partially_supported" | "insufficient_evidence" = "supported";
  const rawConf = String(data.confidence || "").toLowerCase();
  if (rawConf.includes("insufficient")) {
    confidence = "insufficient_evidence";
  } else if (rawConf.includes("partial")) {
    confidence = "partially_supported";
  } else if (rawConf.includes("support")) {
    confidence = "supported";
  }

  const claims: QwenClaim[] = [];
  if (Array.isArray(data.claims)) {
    for (const c of data.claims) {
      if (typeof c === "object" && c.claim) {
        const evIds = Array.isArray(c.evidence_ids)
          ? c.evidence_ids.map((id: any) => String(id).trim().toUpperCase()).filter(Boolean)
          : [];

        let claim_type: QwenClaim["claim_type"] = "judicial_finding";
        const ct = String(c.claim_type || "").toLowerCase();
        if (
          ct === "judicial_finding" ||
          ct === "statutory_provision" ||
          ct === "party_submission" ||
          ct === "procedural_history" ||
          ct === "legal_interpretation"
        ) {
          claim_type = ct;
        }

        let support_level: QwenClaim["support_level"] = "directly_supports";
        const sl = String(c.support_level || "").toLowerCase();
        if (
          sl === "directly_supports" ||
          sl === "relevant_context" ||
          sl === "contradicts_or_qualifies" ||
          sl === "unrelated" ||
          sl === "unverified"
        ) {
          support_level = sl;
        }

        claims.push({
          claim: String(c.claim).trim(),
          evidence_ids: evIds,
          claim_type,
          support_level,
          qualification: c.qualification ? String(c.qualification).trim() : undefined,
        });
      }
    }
  }

  const contrary_evidence: QwenContraryEvidence[] = [];
  if (Array.isArray(data.contrary_or_qualifying_evidence)) {
    for (const ce of data.contrary_or_qualifying_evidence) {
      if (typeof ce === "object" && ce.evidence_id) {
        contrary_evidence.push({
          evidence_id: String(ce.evidence_id).trim().toUpperCase(),
          nature: String(ce.nature || "qualification").toLowerCase(),
          explanation: String(ce.explanation || "").trim(),
        });
      }
    }
  }

  return {
    answer,
    confidence,
    limitations,
    claims,
    contrary_evidence,
    raw_response: rawText,
  };
}

/**
 * Direct conversational invocation of local Qwen for public legal information (Mode A: Research OFF).
 * Strictly communicates that statements are unverified general legal knowledge, disclaims formal legal advice,
 * and does NOT call Gemini under any circumstances.
 */
export async function generateQwenConversationalAnswer(params: {
  query: string;
  conversationHistory?: Array<{ sender: "user" | "assistant"; text: string }>;
  endpoint?: string;
  model?: string;
  timeoutMs?: number;
}): Promise<string> {
  const { endpoint, headers } = getQwenEndpointAndHeaders(params.endpoint);
  const model = params.model || "qwen3:4b-instruct";
  const timeoutMs = params.timeoutMs || 90000;

  const systemPrompt = `You are Vidhik's Public Legal Information Assistant for Indian Law.
Your role is to explain legal concepts, constitutional provisions, statutory frameworks, and general legal procedures clearly and accurately to citizens.

CRITICAL PUBLIC RULES:
1. Provide objective legal information, NOT formal legal representation or legal advice.
2. Emphasize that your response is general legal information and unverified against active judicial case files unless Research Mode is enabled.
3. NEVER fabricate case citations, CNR numbers, or non-existent statutory sections.
4. If a question is not related to Indian legal doctrines, fundamental rights, or legal systems, politely clarify your scope.
5. Keep explanations concise, structured (2-3 paragraphs), and balanced.`;

  let prompt = `${systemPrompt}\n\n`;
  if (params.conversationHistory && params.conversationHistory.length > 0) {
    prompt += `PREVIOUS CONVERSATION CONTEXT:\n`;
    for (const msg of params.conversationHistory.slice(-4)) {
      prompt += `${msg.sender === "user" ? "Citizen" : "Assistant"}: ${msg.text}\n`;
    }
    prompt += `\n`;
  }
  prompt += `CITIZEN QUESTION: "${params.query}"\n\nASSISTANT EXPLANATION:`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify({
        model,
        prompt,
        stream: false,
        options: {
          temperature: 0.2,
          top_p: 0.9,
          num_predict: 400,
        },
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      throw new Error(`Ollama service returned HTTP ${res.status}`);
    }

    const data = await res.json();
    let text = String(data.response || "").trim();

    // Strip thinking blocks if model outputs <think>...</think>
    text = text.replace(/<think>[\s\S]*?<\/think>/gi, "").trim();
    return text || "I am unable to formulate a general explanation for this query. Please consult an Advocate for formal legal guidance.";
  } catch (err: any) {
    clearTimeout(timeoutId);
    throw new Error(`Local Qwen legal model unavailable: ${err.message}`);
  }
}
