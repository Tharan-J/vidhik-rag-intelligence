"""
Validation script for Section 5 of Stage 7: Real Query Validation.
Runs Query A, B, C, D against the live Vidhik FastAPI service (port 8000).
Captures latency, confidence, claims, evidence, and provenance integrity.
"""

import json
import time
import urllib.request
import urllib.error

QUERIES = [
    {
        "id": "Query A (Direct)",
        "query": "What is the limitation period for filing an appeal?",
        "category": "Direct legal question",
    },
    {
        "id": "Query B (Conceptual)",
        "query": "What are the essential elements required to establish negligence?",
        "category": "Conceptual legal question",
    },
    {
        "id": "Query C (Procedural)",
        "query": "What factors are considered when deciding whether delay should be condoned?",
        "category": "Procedural question",
    },
    {
        "id": "Query D (Evidence-sensitive)",
        "query": "What are the statutory regulations governing deep sea asteroid mining under Indian maritime law?",
        "category": "Evidence-sensitive / Insufficient evidence question",
    },
]

API_URL = "http://localhost:8000/api/v1/query"

def run_query(item):
    print(f"\n==================================================")
    print(f"Executing: {item['id']} - {item['query']}")
    print(f"Category: {item['category']}")
    print(f"==================================================")

    payload = json.dumps({"query": item["query"]}).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            elapsed = time.time() - t0
            status_code = resp.status
            data = json.loads(resp.read().decode("utf-8"))

            print(f"HTTP Status: {status_code}")
            print(f"Client Elapsed Time: {elapsed:.2f}s")
            print(f"Backend Reported Time: {data.get('execution_time_seconds', 0):.2f}s")
            print(f"Confidence: {data.get('confidence')}")
            print(f"Retrieval Count: {data.get('retrieval_count')}")
            print(f"Evidence Count: {data.get('evidence_count')}")
            print(f"Claims Count: {len(data.get('claims', []))}")
            print(f"Answer Preview: {data.get('answer', '')[:200]}...")
            
            # Verify evidence IDs
            ev_ids = [e["evidence_id"] for e in data.get("evidence", [])]
            print(f"Evidence IDs: {ev_ids}")

            # Verify claims link to evidence
            for i, c in enumerate(data.get("claims", [])):
                print(f"  Claim {i+1}: {c.get('claim')[:80]}...")
                print(f"    Evidence IDs: {c.get('evidence_ids')}")
                for auth in c.get("authorities", []):
                    print(f"    Authority: {auth.get('court')} | {auth.get('case_title')} | p.{auth.get('page_number')}")

            return {
                "id": item["id"],
                "query": item["query"],
                "status": status_code,
                "elapsed": round(elapsed, 2),
                "backend_elapsed": data.get("execution_time_seconds"),
                "confidence": data.get("confidence"),
                "claims_count": len(data.get("claims", [])),
                "evidence_count": data.get("evidence_count", len(data.get("evidence", []))),
                "retrieval_count": data.get("retrieval_count", 0),
                "answer_snippet": data.get("answer", "")[:150],
                "limitations": data.get("limitations", []),
                "success": True,
            }
    except Exception as e:
        elapsed = time.time() - t0
        print(f"FAILED: {e}")
        return {
            "id": item["id"],
            "query": item["query"],
            "status": "ERROR",
            "elapsed": round(elapsed, 2),
            "error": str(e),
            "success": False,
        }

if __name__ == "__main__":
    results = []
    for item in QUERIES:
        res = run_query(item)
        results.append(res)
    
    with open("query_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n\nAll validation queries complete. Saved to query_validation_results.json")
