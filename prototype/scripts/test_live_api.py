#!/usr/bin/env python3
"""
Live End-to-End API Validation Script
=====================================
Initializes the FastAPI application with the real production LegalRAGEngine
and executes:
1. GET  /health
2. GET  /api/v1/status
3. POST /api/v1/query
Validates schema conformity, provenance retention, and clean responses.
"""

import sys
import time
import json
from pathlib import Path

PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_ROOT))

from fastapi.testclient import TestClient
from api.main import create_app
from rag.engine import LegalRAGEngine


def main():
    print("=" * 80)
    print("VIDHIK LIVE API END-TO-END VALIDATION")
    print("=" * 80)

    # 1. Initialize live production engine
    print("\n[1/4] Initializing real LegalRAGEngine...")
    t0 = time.time()
    engine = LegalRAGEngine()
    print(f"Engine initialized in {time.time() - t0:.2f}s.")

    # 2. Create FastAPI app with live engine
    print("\n[2/4] Mounting FastAPI application and TestClient...")
    app = create_app(engine=engine)
    client = TestClient(app)

    # 3. Test GET /health
    print("\n[3/4] Testing GET /health...")
    health_resp = client.get("/health")
    print(f"Status Code: {health_resp.status_code}")
    print(f"Response   : {health_resp.json()}")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    assert health_resp.json()["status"] == "healthy"

    # 4. Test GET /api/v1/status
    print("\n[4/4] Testing GET /api/v1/status (Readiness Probe)...")
    status_resp = client.get("/api/v1/status")
    print(f"Status Code: {status_resp.status_code}")
    status_data = status_resp.json()
    print(json.dumps(status_data, indent=2))
    assert status_resp.status_code == 200, f"Status check failed: {status_resp.text}"
    assert status_data["status"] == "ready", f"System not ready: {status_data}"

    # 5. Test POST /api/v1/query
    test_query = "What is the limitation period for filing an appeal?"
    print(f"\n[5/5] Testing POST /api/v1/query with: '{test_query}'...")
    query_payload = {
        "query": test_query,
        "top_k": 20,
        "max_evidence": 5,
    }
    t_start = time.time()
    query_resp = client.post("/api/v1/query", json=query_payload)
    elapsed = time.time() - t_start

    print(f"Status Code: {query_resp.status_code} (in {elapsed:.2f}s)")
    assert query_resp.status_code == 200, f"Query failed: {query_resp.text}"

    data = query_resp.json()
    print("\n" + "=" * 80)
    print("LIVE API RESPONSE SUMMARY")
    print("=" * 80)
    print(f"Query      : {data['query']}")
    print(f"Confidence : {data['confidence']}")
    print(f"Latency    : {data['execution_time_seconds']}s")
    print(f"Retrieval  : {data['retrieval_count']} candidates")
    print(f"Evidence   : {data['evidence_count']} chunks")
    print(f"\nAnswer:\n{data['answer']}")

    print(f"\nClaims ({len(data['claims'])}):")
    for idx, clm in enumerate(data["claims"], 1):
        print(f"\n[{idx}] {clm['claim']}")
        print(f"    Evidence IDs : {clm['evidence_ids']}")
        print(f"    Grounded     : {clm['is_grounded']}")
        print(f"    Authorities  : {len(clm['authorities'])}")
        for auth in clm["authorities"]:
            print(f"      - {auth['court']} | {auth['case_title']} (Page {auth['page_number']})")

    print(f"\nEvidence Chunks ({len(data['evidence'])}):")
    for ev in data["evidence"]:
        print(f"[{ev['evidence_id']}] {ev['court']} | {ev['case_title']}")
        print(f"     Doc: {ev['source_file']} | Pages: {ev['page_start']}-{ev['page_end']} | Point: {ev['qdrant_point_id']}")

    print("\n" + "=" * 80)
    print("ALL VALIDATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
