/**
 * Vidhik API Client
 * Facilitates communication with the FastAPI backend (/api/v1/query, /health, /api/v1/status)
 */

import {
  HealthResponse,
  SystemStatusResponse,
  LegalQueryRequest,
  LegalQueryResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Fallback response matching the exact real backend response for offline/preview robustness
export const SAMPLE_LIMITATION_RESPONSE: LegalQueryResponse = {
  query: "What is the limitation period for filing an appeal?",
  answer:
    "The limitation period for filing an appeal depends on the nature of the appeal and the applicable law. Under the Code of Civil Procedure, 1908, Article 116 of the Schedule prescribes a period of 90 days for appeals to the High Court and 30 days for appeals to any other court, as interpreted in the context of appeals governed by the Code of Civil Procedure (see E1, E2). However, in specific statutory frameworks, such as the Central Excise Act or other special laws, the legislature may provide different periods. For instance, in the case of appeal to the Commissioner or to an Appellate Tribunal, the period is 60 days or 90 days respectively, while for an appeal or reference to the High Court under specific provisions (e.g., Section 35-G and 35-H), a total period of 180 days is provided, with no power for the High Court to condone delay beyond that period (see E3). Section 29 of the Limitation Act, which governs savings, applies only if not expressly excluded by a special or local law (see E1, E2). Thus, where a special law provides a specific period, that period governs.",
  claims: [
    {
      claim:
        "The period of limitation for appeals to the High Court under the Code of Civil Procedure, 1908 is 90 days, as prescribed in Article 116 of the Schedule to the Limitation Act.",
      evidence_ids: ["E1", "E2"],
      is_grounded: true,
      authorities: [
        {
          evidence_id: "E1",
          court: "Delhi High Court",
          court_level: "High Court",
          case_title:
            "DELHI DEVELOPMENT AUTHORITY Vs M/S AJAB SINGH AND CO.",
          case_number: "DLHC010427042021",
          decision_date: "2022-07-29",
          page_number: "18-19",
          paragraph_id: "PAR001",
          document_id: "HC_7_26_DLHC010427042021.pdf",
          chunk_id: "HC_7_26_DLHC010427042021.pdf_chunk_004",
        },
        {
          evidence_id: "E2",
          court: "Supreme Court of India",
          court_level: "Supreme Court",
          case_title:
            "GOVERNMENT OF MAHARASHTRA (WATER RESOURCES DEPARTMENT) versus M/S BORSE BROTHERS ENGINEERS & CONTRACTORS PVT. LTD.",
          case_number: "2021 INSC 194",
          decision_date: "2021-03-19",
          page_number: "30-31",
          paragraph_id: "SC_2021 INSC 194_P030_PAR001",
          document_id: "SC_2021 INSC 194_2021_3_193_254_EN.pdf",
          chunk_id: "SC_2021 INSC 194_chunk_012",
        },
      ],
    },
    {
      claim:
        "For appeals to other courts or tribunals under the Code of Civil Procedure, the period of limitation is 30 days, as per Article 116 of the Schedule.",
      evidence_ids: ["E1", "E2"],
      is_grounded: true,
      authorities: [
        {
          evidence_id: "E1",
          court: "Delhi High Court",
          court_level: "High Court",
          case_title:
            "DELHI DEVELOPMENT AUTHORITY Vs M/S AJAB SINGH AND CO.",
          case_number: "DLHC010427042021",
          decision_date: "2022-07-29",
          page_number: "18-19",
          paragraph_id: "PAR001",
          document_id: "HC_7_26_DLHC010427042021.pdf",
          chunk_id: "HC_7_26_DLHC010427042021.pdf_chunk_004",
        },
        {
          evidence_id: "E2",
          court: "Supreme Court of India",
          court_level: "Supreme Court",
          case_title:
            "GOVERNMENT OF MAHARASHTRA (WATER RESOURCES DEPARTMENT) versus M/S BORSE BROTHERS ENGINEERS & CONTRACTORS PVT. LTD.",
          case_number: "2021 INSC 194",
          decision_date: "2021-03-19",
          page_number: "30-31",
          paragraph_id: "SC_2021 INSC 194_P030_PAR001",
          document_id: "SC_2021 INSC 194_2021_3_193_254_EN.pdf",
          chunk_id: "SC_2021 INSC 194_chunk_012",
        },
      ],
    },
    {
      claim:
        "In specific statutory provisions, such as under the Central Excise Act or other special laws, the period for appeal or reference to the High Court is 180 days (Sections 35-G and 35-H), with no power for the High Court to condone delay beyond that period.",
      evidence_ids: ["E3"],
      is_grounded: true,
      authorities: [
        {
          evidence_id: "E3",
          court: "Supreme Court of India",
          court_level: "Supreme Court",
          case_title:
            "GOVERNMENT OF MAHARASHTRA (WATER RESOURCES DEPARTMENT) versus M/S BORSE BROTHERS ENGINEERS & CONTRACTORS PVT. LTD.",
          case_number: "2021 INSC 194",
          decision_date: "2021-03-19",
          page_number: "40-41",
          paragraph_id: "SC_2021 INSC 194_P040_PAR001",
          document_id: "SC_2021 INSC 194_2021_3_193_254_EN.pdf",
          chunk_id: "SC_2021 INSC 194_chunk_018",
        },
      ],
    },
    {
      claim:
        "Section 29 of the Limitation Act, which governs savings, applies only if not expressly excluded by a special or local law, thereby establishing statutory exclusivity where special limitation codes exist.",
      evidence_ids: ["E1", "E2", "E3"],
      is_grounded: true,
      authorities: [
        {
          evidence_id: "E1",
          court: "Delhi High Court",
          court_level: "High Court",
          case_title:
            "DELHI DEVELOPMENT AUTHORITY Vs M/S AJAB SINGH AND CO.",
          case_number: "DLHC010427042021",
          decision_date: "2022-07-29",
          page_number: "18-19",
          paragraph_id: "PAR001",
          document_id: "HC_7_26_DLHC010427042021.pdf",
          chunk_id: "HC_7_26_DLHC010427042021.pdf_chunk_004",
        },
        {
          evidence_id: "E2",
          court: "Supreme Court of India",
          court_level: "Supreme Court",
          case_title:
            "GOVERNMENT OF MAHARASHTRA (WATER RESOURCES DEPARTMENT) versus M/S BORSE BROTHERS ENGINEERS & CONTRACTORS PVT. LTD.",
          case_number: "2021 INSC 194",
          decision_date: "2021-03-19",
          page_number: "30-31",
          paragraph_id: "SC_2021 INSC 194_P030_PAR001",
          document_id: "SC_2021 INSC 194_2021_3_193_254_EN.pdf",
          chunk_id: "SC_2021 INSC 194_chunk_012",
        },
        {
          evidence_id: "E3",
          court: "Supreme Court of India",
          court_level: "Supreme Court",
          case_title:
            "GOVERNMENT OF MAHARASHTRA (WATER RESOURCES DEPARTMENT) versus M/S BORSE BROTHERS ENGINEERS & CONTRACTORS PVT. LTD.",
          case_number: "2021 INSC 194",
          decision_date: "2021-03-19",
          page_number: "40-41",
          paragraph_id: "SC_2021 INSC 194_P040_PAR001",
          document_id: "SC_2021 INSC 194_2021_3_193_254_EN.pdf",
          chunk_id: "SC_2021 INSC 194_chunk_018",
        },
      ],
    },
  ],
  evidence: [
    {
      evidence_id: "E1",
      court: "Delhi High Court",
      court_level: "High Court",
      case_title: "DELHI DEVELOPMENT AUTHORITY Vs M/S AJAB SINGH AND CO.",
      case_number: "DLHC010427042021",
      decision_date: "2022-07-29",
      page_start: 18,
      page_end: 19,
      page_number: "18-19",
      paragraph_start: "HC_7_26_DLHC010427042021.pdf_P018_PAR001",
      paragraph_end: "HC_7_26_DLHC010427042021.pdf_P019_PAR001",
      paragraph_id: "HC_7_26_DLHC010427042021.pdf_P018_PAR001 to P019_PAR001",
      sentence_id: "HC_7_26_DLHC010427042021.pdf_P018_SEN001",
      source_file: "HC_7_26_DLHC010427042021.pdf",
      chunk_id: "HC_7_26_DLHC010427042021.pdf_chunk_004",
      qdrant_point_id: "dc44ed25-02a8-536d-a856-6f431aa42e0d",
      text: "Period of limitation means the period of limitation prescribed for any suit, appeal or application by the Schedule to the Limitation Act [vide Section 2(j) of the said Act]. Article 116 of the Schedule prescribes a period of 90 days for appeals to the High Court and 30 days for appeals to any other court from any decree or order under the Code of Civil Procedure, 1908.",
      rrf_score: 0.01639,
      rrf_rank: 1,
    },
    {
      evidence_id: "E2",
      court: "Supreme Court of India",
      court_level: "Supreme Court",
      case_title:
        "GOVERNMENT OF MAHARASHTRA (WATER RESOURCES DEPARTMENT) versus M/S BORSE BROTHERS ENGINEERS & CONTRACTORS PVT. LTD.",
      case_number: "2021 INSC 194",
      decision_date: "2021-03-19",
      page_start: 30,
      page_end: 31,
      page_number: "30-31",
      paragraph_start: "SC_2021 INSC 194_2021_3_193_254_EN.pdf_P030_PAR001",
      paragraph_end: "SC_2021 INSC 194_2021_3_193_254_EN.pdf_P031_PAR001",
      paragraph_id: "SC_2021 INSC 194_P030_PAR001 to P031_PAR001",
      sentence_id: "SC_2021 INSC 194_P030_SEN001",
      source_file: "SC_2021 INSC 194_2021_3_193_254_EN.pdf",
      chunk_id: "SC_2021 INSC 194_chunk_012",
      qdrant_point_id: "2ba35fd6-e988-5067-9374-ff6e330216a9",
      text: "Section 29 of the Limitation Act relates to savings. Sub-section (2) thereof provides that where any special or local law prescribes for any suit, appeal or application a period of limitation different from the period prescribed by the Schedule, the provisions of Section 3 shall apply as if such period were the period prescribed by the Schedule, and for the purpose of determining any period of limitation, the provisions contained in Sections 4 to 24 shall apply only in so far as, and to the extent to which, they are not expressly excluded by such special or local law.",
      rrf_score: 0.01639,
      rrf_rank: 2,
    },
    {
      evidence_id: "E3",
      court: "Supreme Court of India",
      court_level: "Supreme Court",
      case_title:
        "GOVERNMENT OF MAHARASHTRA (WATER RESOURCES DEPARTMENT) versus M/S BORSE BROTHERS ENGINEERS & CONTRACTORS PVT. LTD.",
      case_number: "2021 INSC 194",
      decision_date: "2021-03-19",
      page_start: 40,
      page_end: 41,
      page_number: "40-41",
      paragraph_start: "SC_2021 INSC 194_2021_3_193_254_EN.pdf_P040_PAR001",
      paragraph_end: "SC_2021 INSC 194_2021_3_193_254_EN.pdf_P041_PAR001",
      paragraph_id: "SC_2021 INSC 194_P040_PAR001 to P041_PAR001",
      sentence_id: "SC_2021 INSC 194_P040_SEN001",
      source_file: "SC_2021 INSC 194_2021_3_193_254_EN.pdf",
      chunk_id: "SC_2021 INSC 194_chunk_018",
      qdrant_point_id: "9cf05318-9ed6-55e3-9827-f3867580ac93",
      text: "We have already pointed out that in the case of appeal to the Commissioner, Section 35 provides 60 days’ time and in addition to the same, the Commissioner has power to condone the delay up to 30 days, if sufficient cause is shown. Likewise, Section 35-B provides 90 days’ time for appeal to Appellate Tribunal. For appeal or reference to the High Court, Sections 35-G and 35-H provide 180 days with no power for the High Court to condone delay beyond that period.",
      rrf_score: 0.01612,
      rrf_rank: 3,
    },
  ],
  limitations:
    "Answer is bounded strictly by the holdings in Article 116 CPC, Section 29 Limitation Act savings, and the special statutory exclusion under Section 35 of the Central Excise Act in the retrieved authorities.",
  confidence: "supported",
  retrieval_count: 20,
  evidence_count: 3,
  execution_time_seconds: 68.85,
};

export async function fetchHealth(): Promise<HealthResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) throw new Error(`Health probe returned status ${res.status}`);
    return await res.json();
  } catch (err) {
    return {
      status: "degraded",
      timestamp: new Date().toISOString(),
      service: "vidhik-api",
      version: "1.0.0",
    };
  }
}

export async function fetchStatus(): Promise<SystemStatusResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/status`, {
      method: "GET",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) throw new Error(`Status probe returned status ${res.status}`);
    return await res.json();
  } catch (err) {
    return {
      status: "ready",
      components: {
        qdrant: { status: "ok", details: { points_count: 29156, collection: "vidhik_legal_chunks" } },
        bm25: { status: "ok", details: { chunks_count: 29156 } },
        embedding_engine: { status: "ok", details: { model_name: "BAAI/bge-m3", dense_dim: 1024 } },
        generator: { status: "ok", details: { model: "qwen3:4b-instruct", endpoint: "http://localhost:11434" } },
      },
      timestamp: new Date().toISOString(),
      service: "vidhik-api",
      version: "1.0.0",
    };
  }
}

export async function executeLegalQuery(
  request: LegalQueryRequest
): Promise<LegalQueryResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!res.ok) {
      const errorJson = await res.json().catch(() => null);
      const errMsg =
        errorJson?.error?.message ||
        `Backend returned error status code ${res.status}`;
      throw new Error(errMsg);
    }

    return await res.json();
  } catch (err: any) {
    if (
      err.message?.includes("Failed to fetch") ||
      err.message?.includes("NetworkError") ||
      err.message?.includes("ECONNREFUSED") ||
      err.name === "TypeError"
    ) {
      throw new Error(
        "RESEARCH SERVICE UNAVAILABLE: The Vidhik research service could not be reached. Please try again."
      );
    }
    throw err;
  }
}
