import { NextResponse } from "next/server";

const SUPPORTED_LANGUAGES = ["ta", "hi", "kn", "mr"];

export async function POST(request: Request) {
  try {
    // 1. Establish and enforce authorization context
    const authHeader =
      request.headers.get("authorization") ||
      request.headers.get("x-lawyer-token") ||
      request.headers.get("x-api-key");
    const callerMatterId =
      request.headers.get("x-matter-id") ||
      request.headers.get("x-workspace-matter-id");

    const isAuthenticated = Boolean(authHeader || callerMatterId);

    if (!isAuthenticated) {
      return NextResponse.json(
        {
          error: {
            code: "UNAUTHENTICATED",
            message:
              "UNAUTHENTICATED: Valid authorization context (x-lawyer-token or x-matter-id) is required for multilingual legal representation.",
          },
        },
        { status: 401 }
      );
    }

    const body = await request.json();
    const englishAnswer =
      body.english_answer || body.englishAnswer || body.text || "";
    const targetLanguage = (
      body.target_language ||
      body.targetLanguage ||
      body.language ||
      ""
    ).toLowerCase().trim();
    const matterId = body.matter_id || body.matterId || callerMatterId || "GLOBAL";
    const evidence = body.evidence || [];
    const claims = body.claims || [];

    // Matter isolation check: if caller specifies matter in header and body, ensure no cross-matter conflict
    if (callerMatterId && body.matterId && callerMatterId !== body.matterId) {
      return NextResponse.json(
        {
          error: {
            code: "CROSS_MATTER_FORBIDDEN",
            message: `Matter isolation violation: caller matter '${callerMatterId}' cannot access matter '${body.matterId}'.`,
          },
        },
        { status: 403 }
      );
    }

    // 2. Validate English Answer
    if (!englishAnswer || !englishAnswer.trim()) {
      return NextResponse.json(
        {
          error: {
            code: "EMPTY_ANSWER",
            message: "english_answer cannot be empty or whitespace only.",
          },
        },
        { status: 400 }
      );
    }

    // 3. Validate Supported Target Language
    if (!SUPPORTED_LANGUAGES.includes(targetLanguage)) {
      return NextResponse.json(
        {
          error: {
            code: "UNSUPPORTED_LANGUAGE",
            message: `Unsupported language code '${targetLanguage}'. Supported: ${SUPPORTED_LANGUAGES.join(", ")}`,
          },
        },
        { status: 400 }
      );
    }

    // 4. Resolve Translation Gateway or Daemon
    const rawToken = process.env.AI_GATEWAY_TOKEN || process.env.GATEWAY_TOKEN;
    const gatewayToken = rawToken ? rawToken.trim().replace(/^["']|["']$/g, "") : undefined;
    const reqHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "true",
    };
    if (gatewayToken) {
      reqHeaders["Authorization"] = `Bearer ${gatewayToken}`;
      reqHeaders["x-gateway-token"] = gatewayToken;
    }

    let daemonUrl = process.env.TRANSLATION_DAEMON_URL;
    if (!daemonUrl && process.env.AI_GATEWAY_URL) {
      const cleanUrl = process.env.AI_GATEWAY_URL.replace(/\/+$/, "");
      daemonUrl = cleanUrl.endsWith("/api/translate")
        ? cleanUrl
        : (cleanUrl.endsWith("/translate") ? cleanUrl : `${cleanUrl}/api/translate`);
    }
    if (!daemonUrl) {
      daemonUrl = "http://127.0.0.1:8009/translate";
    }

    let translationResponse: Response;

    try {
      translationResponse = await fetch(daemonUrl, {
        method: "POST",
        headers: reqHeaders,
        body: JSON.stringify({
          english_answer: englishAnswer.trim(),
          target_language: targetLanguage,
          matter_id: matterId,
          evidence: evidence,
          claims: claims,
        }),
        signal: AbortSignal.timeout(45000),
      });
    } catch (netErr: any) {
      return NextResponse.json(
        {
          error: {
            code: "TRANSLATION_SERVICE_UNAVAILABLE",
            message:
              "The IndicTrans2 legal translation service daemon is temporarily unavailable.",
            details: netErr.message,
          },
        },
        { status: 503 }
      );
    }

    if (!translationResponse.ok) {
      const errData = await translationResponse.json().catch(() => ({}));
      return NextResponse.json(
        {
          error: {
            code: "TRANSLATION_SERVICE_ERROR",
            message:
              errData.error ||
              `Translation daemon failed with status ${translationResponse.status}`,
          },
        },
        { status: translationResponse.status }
      );
    }

    const data = await translationResponse.json();

    // 5. Fail safely if placeholder corruption was detected
    if (data.verification?.verification_status === "FAIL_UNRESOLVED_PLACEHOLDERS") {
      return NextResponse.json(
        {
          error: {
            code: "CORRUPTED_TRANSLATION_REJECTED",
            message:
              "Translation rejected: unresolved or corrupted entity placeholders detected in output.",
            details: data.unresolved_placeholders,
          },
          verification: data.verification,
        },
        { status: 422 }
      );
    }

    return NextResponse.json(data, { status: 200 });
  } catch (err: any) {
    return NextResponse.json(
      {
        error: {
          code: "INTERNAL_ERROR",
          message: err.message || "An unexpected error occurred during translation.",
        },
      },
      { status: 500 }
    );
  }
}
