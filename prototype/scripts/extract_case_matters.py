#!/usr/bin/env python3
"""
Dynamic Case Matter Extractor using Gemini 3.5 Flash Lite
=========================================================
Reads real court documents from the repository:
- DLHC010427042021.pdf.txt (DDA v. Ajab Singh & Co., Delhi High Court)
- SC_2021 INSC 194 (Govt. of Maharashtra v. Borse Brothers, Supreme Court)
- DLHC010035432020.pdf.txt (Niraj Silk Mills v. Commr of Customs, Delhi High Court)
- HCBM030041062018.pdf.txt (Bhimrao Yerge v. Kavita Yerge, Bombay High Court)

Invokes Gemini 3.5 Flash Lite to extract the complete, rich Matter model
(Overview, Status, Timeline, Documents, Issues, Sections, Authorities, Notes)
without any hardcoded dummy placeholders.
"""

import sys
import os
import json
import urllib.request
from pathlib import Path

PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROTOTYPE_ROOT.parent

# Read Gemini API Key
gemini_key = ""
env_path = PROTOTYPE_ROOT / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                gemini_key = line.strip().split("=", 1)[1].strip("\"'")
                break

if not gemini_key:
    # Try frontend/.env.local
    f_env = REPO_ROOT / "frontend" / ".env.local"
    if f_env.exists():
        with open(f_env) as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    gemini_key = line.strip().split("=", 1)[1].strip("\"'")
                    break

print("Found Gemini Key:", bool(gemini_key))

CASES_CONFIG = [
    {
        "id": "MAT-2024-001",
        "file_type": "text",
        "path": "research/rag_readiness_audit/high_court/extracted_text/DLHC010427042021.pdf.txt",
        "doc_id": "HC_7_26_DLHC010427042021.pdf",
        "client": "Delhi Development Authority",
    },
    {
        "id": "MAT-2024-002",
        "file_type": "bm25",
        "doc_id": "SC_2021 INSC 194_2021_3_193_254_EN.pdf",
        "client": "M/s Borse Brothers Engineers & Contractors Pvt. Ltd.",
    },
    {
        "id": "MAT-2024-003",
        "file_type": "text",
        "path": "research/rag_readiness_audit/high_court/extracted_text/DLHC010035432020.pdf.txt",
        "doc_id": "DLHC010035432020.pdf",
        "client": "Niraj Silk Mills & Hanuman Prasad and Sons",
    },
    {
        "id": "MAT-2024-004",
        "file_type": "text",
        "path": "research/rag_readiness_audit/high_court/extracted_text/HCBM030041062018.pdf.txt",
        "doc_id": "HCBM030041062018.pdf",
        "client": "Bhimrao Shivram Yerge",
    },
]

def get_case_text(case_cfg):
    if case_cfg["file_type"] == "text":
        p = REPO_ROOT / case_cfg["path"]
        if p.exists():
            with open(p, encoding="utf-8", errors="ignore") as f:
                return f.read(14000)
    elif case_cfg["file_type"] == "bm25":
        import pandas as pd
        map_p = PROTOTYPE_ROOT / "indexes" / "bm25" / "bm25_mapping.parquet"
        if map_p.exists():
            df = pd.read_parquet(map_p)
            match = df[df["document_id"] == case_cfg["doc_id"]]
            if len(match) > 0:
                return "\n\n".join(match.head(10)["text"].tolist())[:14000]
    return ""

def extract_matter_with_gemini(case_cfg, text_sample):
    prompt = f"""
You are Vidhik's Legal Intelligence Extraction Engine.
Analyze the following verbatim judicial record from an Indian court:

--- CASE TEXT EXCERPT ---
{text_sample}
--- END EXCERPT ---

Task:
Extract a comprehensive, realistic, production-ready Matter model for an Indian advocate workspace representing the client: "{case_cfg['client']}".
Matter ID: "{case_cfg['id']}"

Strict Requirements:
- Extract factual details directly from the provided text (case title, case number, court, judges, advocates, parties, factual background, statutory sections, timeline dates, and framed issues).
- Do NOT use generic placeholders like "Lorem ipsum", "John Doe", "Document 1", or "Issue 1".
- Construct 4-6 specific documents mentioned or filed in the case (e.g. Memo of Appeal, Objections under Section 34, Reply Affidavit, Trial Court/Tribunal Award, Stay Application) with realistic page counts, sizes, dates, and extractedMetadata.
- Construct 4-6 timeline events in chronological order with actual dates found in the text.
- Construct 3-5 distinct legal issues (questions of law and fact) framed in the matter.
- Construct 3-6 statutory sections cited and interpreted (e.g. Section 34, 37 Arbitration Act, Section 5, 29 Limitation Act, Section 13(1A) Commercial Courts Act, Customs Act, CPC, CrPC etc.) with exact description and case impact.
- Construct 2-4 precedent authorities cited in the decision.
- Construct 2-3 strategic litigation notes for counsel.
- Valid MatterStage is one of: "Filed" | "Notice" | "Pleadings" | "Evidence" | "Arguments" | "Judgment".

Return ONLY a valid JSON object matching this schema:
{{
  "id": "{case_cfg['id']}",
  "title": "Clear case title",
  "caseNumber": "Actual case number",
  "court": "Actual court",
  "matterType": "Jurisdiction type (e.g. Commercial Appellate / Writ / Civil / Arbitration)",
  "status": "Arguments" | "Evidence" | "Pleadings" | "Filed" | "Judgment",
  "currentStage": "Arguments" | "Evidence" | "Pleadings" | "Filed" | "Judgment",
  "client": "{case_cfg['client']}",
  "createdAt": "YYYY-MM-DD",
  "updatedAt": "Recent time",
  "lastKnownEvent": "Description of last procedural event",
  "nextImportantEvent": "Description of upcoming step",
  "summary": "Factual and legal overview of the dispute (3-4 sentences)",
  "aiSummary": {{
    "summary": "AI summary of procedural posture",
    "current_status": "Current status in court",
    "important_dates": [
      {{ "label": "event name", "date": "YYYY-MM-DD", "source": "document name" }}
    ],
    "key_issues": ["Issue 1", "Issue 2"],
    "documents_requiring_attention": ["Doc1.pdf"],
    "generated_at": "2026-10-08T14:30:00Z",
    "originating_documents": ["Doc1.pdf", "Doc2.pdf"]
  }},
  "parties": {{
    "petitioner": "Petitioner name & capacity",
    "respondent": "Respondent name & capacity",
    "counsel": "Advocates appearing",
    "court": "Coram / Bench"
  }},
  "importantDates": {{
    "filingDate": "YYYY-MM-DD",
    "lastHearing": "YYYY-MM-DD",
    "nextHearing": "YYYY-MM-DD"
  }},
  "documents": [
    {{
      "id": "DOC-xxx",
      "matterId": "{case_cfg['id']}",
      "name": "filename.pdf",
      "type": "Pleadings" | "Orders" | "Judgments" | "Applications" | "Evidence" | "Other",
      "date": "YYYY-MM-DD",
      "pages": 24,
      "uploadedAt": "YYYY-MM-DD",
      "status": "active",
      "fileSize": "1.8 MB",
      "extractionStatus": "completed",
      "extractedMetadata": {{
        "document_type": "Exact document classification",
        "case_number": "case number",
        "court": "court",
        "parties": ["Party 1", "Party 2"],
        "dates": ["date 1"],
        "sections": ["Section X"],
        "important_points": ["Point 1", "Point 2"],
        "extraction_source": "Gemini 3.5 Flash Lite",
        "extracted_at": "2026-10-08T14:30:00Z"
      }}
    }}
  ],
  "timeline": [
    {{
      "id": "TL-xxx",
      "matterId": "{case_cfg['id']}",
      "date": "YYYY-MM-DD",
      "title": "Event title",
      "description": "Event description",
      "source": "court_record" | "ai_extraction",
      "courtStage": "Pleadings" | "Arguments" | "Evidence" | "Filed"
    }}
  ],
  "issues": [
    {{
      "id": "ISSUE-xxx",
      "matterId": "{case_cfg['id']}",
      "issueNumber": "Issue 1",
      "title": "Issue title",
      "description": "Detailed description of legal question",
      "source": "ai_suggestion",
      "confirmed": true,
      "relatedDocuments": ["filename.pdf"],
      "relatedSections": ["Section X"],
      "relatedAuthorities": ["Precedent 1"]
    }}
  ],
  "sections": [
    {{
      "id": "SEC-xxx",
      "act": "Name of Statute",
      "section": "Section number",
      "heading": "Section heading",
      "description": "Substantive rule under this section",
      "sourceDocument": "filename.pdf"
    }}
  ],
  "authorities": [
    {{
      "id": "AUTH-xxx",
      "caseTitle": "Cited Landmark Case",
      "caseNumber": "Citation / Reporter",
      "court": "Court level",
      "year": "YYYY",
      "relevance": "Why cited in this matter",
      "supportingEvidence": "Legal principle established"
    }}
  ],
  "notes": [
    {{
      "id": "NOTE-xxx",
      "matterId": "{case_cfg['id']}",
      "title": "Tactical Note Title",
      "content": "Specific legal advice or argument plan",
      "updatedAt": "Recent",
      "tags": ["Limitation", "Strategy"]
    }}
  ]
}}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={gemini_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        raw_text = res["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw_text)

def main():
    extracted_matters = []
    for cfg in CASES_CONFIG:
        print(f"\nProcessing {cfg['id']} ({cfg['client']})...")
        text = get_case_text(cfg)
        print(f"Sample length: {len(text)} chars.")
        if not text:
            print("Warning: no text found for", cfg["id"])
            continue

        try:
            matter_data = extract_matter_with_gemini(cfg, text)
            print(f"Success extracting {cfg['id']}: '{matter_data.get('title')}'")
            print(f"  - Documents: {len(matter_data.get('documents', []))}")
            print(f"  - Timeline: {len(matter_data.get('timeline', []))}")
            print(f"  - Issues: {len(matter_data.get('issues', []))}")
            print(f"  - Sections: {len(matter_data.get('sections', []))}")
            print(f"  - Authorities: {len(matter_data.get('authorities', []))}")
            extracted_matters.append(matter_data)
        except Exception as e:
            print(f"Error extracting {cfg['id']}: {e}")

    out_file = REPO_ROOT / "frontend" / "src" / "lib" / "data" / "extracted_matters.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(extracted_matters, f, indent=2)
    print(f"\nSaved {len(extracted_matters)} fully extracted matters to {out_file}!")

if __name__ == "__main__":
    main()
