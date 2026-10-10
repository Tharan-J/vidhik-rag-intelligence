#!/usr/bin/env python3
"""
Vidhik Document Intelligence & In-Memory Retrieval Daemon
===========================================================
- Connects to Qdrant Cloud ('vidhik_legal_chunks') for dense vector storage & retrieval.
- Uses BGE-M3 (1024-d) dense embeddings for document ingestion and semantic queries.
- Manages an in-memory CPU RAM Cache to avoid redundant Qdrant calls and slash Gemini token costs.
- Serves as the authoritative Document Intelligence layer for the Vidhik Lawyer Workspace:
    POST /ingest : Chunks uploaded court record, embeds with BGE-M3, upserts to Qdrant Cloud.
    POST /probe  : Targeted Document Intelligence probes (parties, holding, timeline, issues, sections, authorities) with CPU cache.
    POST /search : High-speed hybrid vector + BM25 retrieval.
    GET  /health : Subsystem readiness probe.
    GET  /cache/stats : In-memory CPU cache statistics.
    POST /cache/clear : Evicts in-memory cache.
"""

import sys
import os

# Suppress oneDNN and TensorFlow banner noise
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import json
import time
import uuid
import re
import threading
import logging
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Any, Optional

logger = logging.getLogger("VidhikRetrievalDaemon")

PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_ROOT))

# Load Environment Variables from prototype/.env
ENV_FILE = PROTOTYPE_ROOT / ".env"
ENV_VARS = {}
if ENV_FILE.exists():
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                ENV_VARS[k.strip()] = v.strip().strip("\"'")

QDRANT_URL = ENV_VARS.get("QDRANT_URL", os.environ.get("QDRANT_URL", ""))
QDRANT_API_KEY = ENV_VARS.get("QDRANT_API_KEY", os.environ.get("QDRANT_API_KEY", ""))
COLLECTION_NAME = "vidhik_legal_chunks"

print("=" * 70)
print("STARTING VIDHIK DOCUMENT INTELLIGENCE & RETRIEVAL DAEMON")
print(f"Qdrant URL: {QDRANT_URL}")
print("=" * 70)

# Initialize Qdrant Client
qdrant_client = None
if QDRANT_URL and QDRANT_API_KEY:
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import (
            PointStruct,
            Filter,
            FieldCondition,
            MatchValue,
        )
        qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=15)
        print("Connected to Qdrant Cloud successfully.")
    except Exception as e:
        print(f"Warning: Failed to initialize QdrantClient: {e}")

# Initialize BGE-M3 Embedding Engine
embed_engine = None
try:
    from ingestion.embed import BGEM3EmbeddingEngine
    print("Loading BGE-M3 Embedding Engine in memory...")
    embed_engine = BGEM3EmbeddingEngine()
    print("BGE-M3 Embedding Engine loaded successfully.")
except Exception as e:
    print(f"Warning: Failed to load BGE-M3 Embedding Engine: {e}")

# Initialize BM25 Retriever
from retrieval.bm25 import BM25Retriever
import pandas as pd

t0 = time.time()
RETRIEVER = BM25Retriever()
print(f"BM25 Retriever ready in {time.time() - t0:.2f}s ({RETRIEVER.corpus_size:,} chunks).")

MAPPING_PATH = PROTOTYPE_ROOT / "indexes" / "bm25" / "bm25_mapping.parquet"
DF_MAPPING = None
if MAPPING_PATH.exists():
    DF_MAPPING = pd.read_parquet(MAPPING_PATH)
    print(f"Loaded parquet mapping ({len(DF_MAPPING):,} rows).")

# Load Document Metadata from Master Audit CSV
DOCUMENT_METADATA = {}
AUDIT_CSV_PATH = PROTOTYPE_ROOT.parent / "research" / "rag_readiness_audit" / "master_document_audit.csv"
if AUDIT_CSV_PATH.exists():
    try:
        df_audit = pd.read_csv(AUDIT_CSV_PATH, usecols=["document_id", "filename", "title", "court_name"])
        for _, row in df_audit.iterrows():
            t = str(row["title"]) if pd.notna(row["title"]) else ""
            c = str(row["court_name"]) if pd.notna(row["court_name"]) else "Indian Judiciary"
            if pd.notna(row["filename"]):
                DOCUMENT_METADATA[str(row["filename"]).strip()] = (t, c)
            if pd.notna(row["document_id"]):
                DOCUMENT_METADATA[str(row["document_id"]).strip()] = (t, c)
        print(f"Loaded metadata for {len(DOCUMENT_METADATA):,} documents from audit CSV.")
    except Exception as e:
        print(f"Warning: Failed to load audit metadata: {e}")

# In-Memory CPU Cache Implementation
class CPUMemoryCache:
    """
    High-speed thread-safe in-memory CPU cache.
    Stores retrieved matter chunks and probe results in RAM.
    Avoids redundant Qdrant Cloud network round-trips and slashes Gemini token costs.
    """
    def __init__(self, max_items=2000):
        self.lock = threading.Lock()
        self.cache: Dict[str, Any] = {}
        self.max_items = max_items
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                self.hits += 1
                return self.cache[key]
            self.misses += 1
            return None

    def set(self, key: str, value: Any):
        with self.lock:
            if len(self.cache) >= self.max_items:
                # Evict oldest 25% of keys
                keys_to_evict = list(self.cache.keys())[:int(self.max_items * 0.25)]
                for k in keys_to_evict:
                    del self.cache[k]
            self.cache[key] = value

    def clear(self):
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "cached_items_count": len(self.cache),
                "cache_hits": self.hits,
                "cache_misses": self.misses,
                "hit_ratio": round(self.hits / max(1, self.hits + self.misses), 3),
            }

CPU_CACHE = CPUMemoryCache()
DYNAMIC_CHUNKS: List[Dict[str, Any]] = []

def generate_point_id(document_id: str, chunk_id: str) -> str:
    """Deterministic UUID point ID for Qdrant Cloud."""
    key = f"{document_id}_{chunk_id}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))

def structure_and_chunk_text(
    text: str,
    document_id: str,
    case_title: str,
    court: str,
    matter_id: str = "",
    target_words: int = 350
) -> List[Dict[str, Any]]:
    """
    Structure-aware legal chunker preserving page and paragraph coordinates.
    """
    chunks = []
    if not text or not text.strip():
        return chunks

    # Detect explicit page markers (e.g. '--- PAGE 4 ---' or 'Page 4')
    page_blocks = re.split(r"(?:--- PAGE (\d+) ---|\[Page (\d+)\]|\n\s*Page\s+(\d+)\s*\n)", text)
    
    # If no explicit markers found, estimate pages based on ~2,500 characters per page
    if len(page_blocks) <= 1:
        chars_per_page = 2500
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        current_words = []
        current_chunk_idx = 1
        current_page = 1
        current_para = 1
        
        for p in paragraphs:
            p_words = p.split()
            current_words.extend(p_words)
            
            # Estimate page from accumulated characters
            current_page = max(1, round(len(" ".join(current_words)) / chars_per_page))
            
            if len(current_words) >= target_words:
                chunk_text = " ".join(current_words)
                chunk_id = f"chunk_{current_chunk_idx:04d}"
                chunks.append({
                    "document_id": document_id,
                    "matter_id": matter_id,
                    "chunk_id": chunk_id,
                    "case_title": case_title,
                    "court": court,
                    "text": chunk_text,
                    "page_start": current_page,
                    "page_end": current_page,
                    "paragraph_start": f"Para {current_para}",
                    "paragraph_end": f"Para {current_para + len(paragraphs) // max(1, len(chunks) + 1)}",
                })
                current_chunk_idx += 1
                current_para += 1
                current_words = []
        
        if current_words:
            chunk_text = " ".join(current_words)
            chunk_id = f"chunk_{current_chunk_idx:04d}"
            chunks.append({
                "document_id": document_id,
                "matter_id": matter_id,
                "chunk_id": chunk_id,
                "case_title": case_title,
                "court": court,
                "text": chunk_text,
                "page_start": current_page,
                "page_end": current_page,
                "paragraph_start": f"Para {current_para}",
                "paragraph_end": f"Para {current_para}",
            })
    else:
        # Process structured page blocks
        current_page = 1
        current_chunk_idx = 1
        for block in page_blocks:
            if not block:
                continue
            if block.isdigit():
                current_page = int(block)
                continue
            
            words = block.split()
            for i in range(0, len(words), target_words):
                slice_words = words[i:i + target_words]
                if len(slice_words) < 20 and chunks:
                    # Append small trailing fragment to previous chunk
                    chunks[-1]["text"] += " " + " ".join(slice_words)
                    continue
                
                chunk_text = " ".join(slice_words)
                chunk_id = f"chunk_{current_chunk_idx:04d}"
                chunks.append({
                    "document_id": document_id,
                    "matter_id": matter_id,
                    "chunk_id": chunk_id,
                    "case_title": case_title,
                    "court": court,
                    "text": chunk_text,
                    "page_start": current_page,
                    "page_end": current_page,
                    "paragraph_start": f"Page {current_page} Section",
                    "paragraph_end": f"Page {current_page} Section",
                })
                current_chunk_idx += 1

    return chunks

def resolve_case_metadata(doc_id: str, text: str = "") -> (str, str):
    """Resolve authentic case title and court from audit metadata or text caption."""
    clean_id = doc_id.replace(".pdf", "")
    is_sc = "SC_" in doc_id or "INSC" in doc_id
    is_hc = "HC_" in doc_id or "DLHC" in doc_id
    default_court = "Supreme Court of India" if is_sc else ("Delhi High Court" if is_hc else "Indian Judiciary")

    if doc_id in DOCUMENT_METADATA:
        t, c = DOCUMENT_METADATA[doc_id]
        if t: return t, c
    if f"{doc_id}.pdf" in DOCUMENT_METADATA:
        t, c = DOCUMENT_METADATA[f"{doc_id}.pdf"]
        if t: return t, c

    if "2021 INSC 194" in doc_id:
        return "Govt. of Maharashtra v. M/s Borse Brothers Engineers & Contractors Pvt. Ltd.", "Supreme Court of India"
    if "DLHC010427042021" in doc_id:
        return "Delhi Development Authority v. M/s Ajab Singh & Co.", "Delhi High Court"

    if text:
        first_lines = text[:500]
        for line in first_lines.split("\n")[:8]:
            line_str = line.strip()
            if (" v. " in line_str or " vs. " in line_str or " VS " in line_str or " Vs " in line_str) and len(line_str) < 140:
                return line_str, default_court

    return clean_id, default_court

def get_workspace_matter_chunks():
    """Load verified evidence chunks directly from extracted_matters.json."""
    matters_file = PROTOTYPE_ROOT.parent / "frontend" / "src" / "lib" / "data" / "extracted_matters.json"
    chunks = []
    if not matters_file.exists():
        return chunks
    try:
        with open(matters_file, "r", encoding="utf-8") as f:
            matters = json.load(f)
        for m in matters:
            title = m.get("title", "")
            court = m.get("court", "Supreme Court of India")
            doc_name = (m.get("documents", [{}])[0].get("name", "") if m.get("documents") else f"{title}.pdf")
            
            for idx, ev in enumerate(m.get("evidence", [])):
                chunks.append({
                    "document_id": doc_name,
                    "chunk_id": ev.get("paragraphId", f"ev_{idx+1}"),
                    "text": ev.get("evidenceExcerpt", ""),
                    "case_title": title,
                    "court": court,
                    "page": ev.get("pageNumber", "Record"),
                    "para": ev.get("paragraphId", "Para"),
                    "claim": ev.get("claim", ""),
                })
            for idx, sec in enumerate(m.get("sections", [])):
                chunks.append({
                    "document_id": doc_name,
                    "chunk_id": sec.get("section", f"sec_{idx+1}"),
                    "text": f"{sec.get('act', '')} - {sec.get('section', '')}: {sec.get('heading', '')} - {sec.get('description', '')}",
                    "case_title": title,
                    "court": court,
                    "page": sec.get("page", "Record"),
                    "para": sec.get("section", "Section"),
                    "claim": sec.get("description", ""),
                })
            summ = m.get("sourceSummary") or m.get("summary") or ""
            if summ:
                chunks.append({
                    "document_id": doc_name,
                    "chunk_id": "holding",
                    "text": summ,
                    "case_title": title,
                    "court": court,
                    "page": "Judgment",
                    "para": "Holding",
                    "claim": "Summary of Court Judgment",
                })
    except Exception as e:
        print(f"Error reading extracted_matters.json: {e}")

    # Also load test documents if available on disk
    test_pdf = PROTOTYPE_ROOT.parent / "test" / "Dr Balram Singh .pdf"
    if test_pdf.exists():
        try:
            import fitz
            doc = fitz.open(test_pdf)
            for page_num in range(len(doc)):
                txt = doc[page_num].get_text("text").strip()
                if txt:
                    for p_idx, para in enumerate(txt.split("\n\n")):
                        para_str = " ".join(line.strip() for line in para.splitlines() if line.strip())
                        if len(para_str) > 50:
                            chunks.append({
                                "document_id": "Dr Balram Singh .pdf",
                                "chunk_id": f"P{page_num+1:03d}_PAR{p_idx+1:03d}",
                                "text": para_str,
                                "case_title": "Dr Balram Singh and Others v. Union of India and Another",
                                "court": "Supreme Court of India",
                                "page": str(page_num + 1),
                                "page_start": page_num + 1,
                                "page_number": f"Page {page_num + 1}",
                                "paragraph_start": f"Para {p_idx+1}",
                                "para": f"Para {p_idx+1}",
                                "claim": "",
                            })
        except Exception as e:
            pass

    return chunks

class FastRetrievalHandler(BaseHTTPRequestHandler):
    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def finish(self):
        try:
            super().finish()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-gateway-token, ngrok-skip-browser-warning")
        self.send_header("ngrok-skip-browser-warning", "true")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "healthy",
                "qdrant_connected": bool(qdrant_client),
                "qdrant_collection": COLLECTION_NAME,
                "embed_engine_ready": bool(embed_engine),
                "bm25_chunks": RETRIEVER.corpus_size,
                "dynamic_chunks_in_memory": len(DYNAMIC_CHUNKS),
                "cache": CPU_CACHE.stats(),
            }).encode("utf-8"))
            return

        if path == "/cache/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(CPU_CACHE.stats()).encode("utf-8"))
            return

        if path == "/search":
            query = params.get("q", [""])[0]
            top_k = int(params.get("top_k", [5])[0])
            doc_filter = params.get("doc", [None])[0]

            if not query.strip():
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Empty query"}).encode("utf-8"))
                return

            t_start = time.time()
            cache_key = f"search:{query.strip()}:{top_k}:{doc_filter}"
            cached_res = CPU_CACHE.get(cache_key)
            if cached_res:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "query": query,
                    "count": len(cached_res),
                    "duration_ms": 0.2,
                    "cached": True,
                    "results": cached_res,
                }).encode("utf-8"))
                return

            results = self.execute_hybrid_search(query.strip(), top_k=top_k, doc_filter=doc_filter)
            CPU_CACHE.set(cache_key, results)
            dur = time.time() - t_start

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "query": query,
                "count": len(results),
                "duration_ms": round(dur * 1000, 2),
                "cached": False,
                "results": results,
            }).encode("utf-8"))
            return

        if path == "/doc":
            doc_id = params.get("id", [""])[0]
            max_chunks = int(params.get("max", [20])[0])

            cache_key = f"doc:{doc_id}:{max_chunks}"
            cached_doc = CPU_CACHE.get(cache_key)
            if cached_doc:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(cached_doc).encode("utf-8"))
                return

            doc_results = []
            # 1. Check in-memory DYNAMIC_CHUNKS
            local_chunks = [c for c in DYNAMIC_CHUNKS if c.get("document_id") == doc_id or doc_id in c.get("document_id", "")]
            for idx, c in enumerate(local_chunks[:max_chunks], 1):
                doc_results.append({
                    "chunk_id": c.get("chunk_id", f"chk_{idx}"),
                    "page": c.get("page_start", 1),
                    "para": c.get("paragraph_start", f"Para {idx}"),
                    "text": c.get("text", ""),
                })

            # 2. Check Qdrant Cloud
            if not doc_results and qdrant_client is not None:
                try:
                    from qdrant_client.models import Filter, FieldCondition, MatchValue
                    pts, _ = qdrant_client.scroll(
                        collection_name=COLLECTION_NAME,
                        scroll_filter=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=doc_id))]),
                        limit=max_chunks,
                        with_payload=True
                    )
                    for pt in pts:
                        payload = pt.payload or {}
                        doc_results.append({
                            "chunk_id": payload.get("chunk_id", ""),
                            "page": payload.get("page_start", 1),
                            "para": payload.get("paragraph_start", ""),
                            "text": payload.get("text", ""),
                        })
                except Exception as e:
                    print(f"Error scrolling Qdrant for doc {doc_id}: {e}")

            title, court = resolve_case_metadata(doc_id)
            res_payload = {
                "document_id": doc_id,
                "case_title": title,
                "court": court,
                "chunks_count": len(doc_results),
                "chunks": doc_results,
            }
            CPU_CACHE.set(cache_key, res_payload)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res_payload).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        
        try:
            data = json.loads(post_body)
        except Exception:
            data = {}

        # -------------------------------------------------------------
        # 1. /ingest : Parse, Chunk, BGE-M3 Embed, Upsert to Qdrant Cloud
        # -------------------------------------------------------------
        if parsed.path == "/ingest":
            t0 = time.time()
            document_id = data.get("document_id", "UPLOADED_DOC.pdf")
            matter_id = data.get("matter_id", f"MAT-{int(time.time())}")
            text = data.get("text", "")
            case_title = data.get("case_title", document_id)
            court = data.get("court", "Supreme Court of India")

            if not text or len(text.strip()) < 20:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Text is too short for RAG ingestion"}).encode("utf-8"))
                return

            # Stage A: Structure-Aware Chunking
            chunks = structure_and_chunk_text(
                text=text,
                document_id=document_id,
                case_title=case_title,
                court=court,
                matter_id=matter_id,
                target_words=350,
            )

            # Stage B: Dense Vector Embedding with BGE-M3
            chunk_texts = [c["text"] for c in chunks]
            dense_vectors = []
            if embed_engine is not None and chunk_texts:
                try:
                    dense_vectors = embed_engine.encode_dense_batch(chunk_texts)
                except Exception as e:
                    print(f"Error encoding dense vectors with BGE-M3: {e}")

            # Stage C: Upsert directly to Qdrant Cloud ('vidhik_legal_chunks')
            points_upserted = 0
            if qdrant_client is not None and dense_vectors:
                from qdrant_client.models import PointStruct
                points = []
                for idx, c in enumerate(chunks):
                    pt_id = generate_point_id(c["document_id"], c["chunk_id"])
                    payload = {
                        "document_id": c["document_id"],
                        "matter_id": c["matter_id"],
                        "chunk_id": c["chunk_id"],
                        "court": c["court"],
                        "case_title": c["case_title"],
                        "text": c["text"],
                        "page_start": c["page_start"],
                        "page_end": c["page_end"],
                        "paragraph_start": c["paragraph_start"],
                        "paragraph_end": c["paragraph_end"],
                        "custom_point_id": f"{c['document_id']}_{c['chunk_id']}",
                        "source_file": c["document_id"],
                    }
                    points.append(PointStruct(
                        id=pt_id,
                        vector={"dense": dense_vectors[idx]},
                        payload=payload,
                    ))

                # Batch upsert in sizes of 64
                batch_size = 64
                for i in range(0, len(points), batch_size):
                    batch = points[i:i + batch_size]
                    try:
                        qdrant_client.upsert(
                            collection_name=COLLECTION_NAME,
                            points=batch,
                            wait=False,
                        )
                        points_upserted += len(batch)
                    except Exception as e:
                        print(f"Error upserting batch to Qdrant Cloud: {e}")

            # Stage D: Populate in-memory CPU cache & DYNAMIC_CHUNKS
            for c in chunks:
                DYNAMIC_CHUNKS.append(c)

            # Cache complete document chunk list in CPU memory
            CPU_CACHE.set(f"doc:{document_id}:all_chunks", chunks)
            CPU_CACHE.set(f"matter:{matter_id}:all_chunks", chunks)

            dur = round(time.time() - t0, 2)
            print(f"[RAG Ingestion] Document '{document_id}' ingested into Qdrant Cloud: {points_upserted} points in {dur}s.")

            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "ingested",
                    "document_id": document_id,
                    "matter_id": matter_id,
                    "chunks_created": len(chunks),
                    "qdrant_points_upserted": points_upserted,
                    "qdrant_collection": COLLECTION_NAME,
                    "cached_in_cpu_memory": True,
                    "duration_seconds": dur,
                }).encode("utf-8"))
            except (BrokenPipeError, ConnectionResetError):
                print(f"[RAG Ingestion Warning] Client disconnected before receiving ingestion response for '{document_id}'")
            return

        # -------------------------------------------------------------
        # 2. /probe : Targeted Document Intelligence Probes via Qdrant & Cache
        # -------------------------------------------------------------
        if parsed.path == "/probe":
            document_id = data.get("document_id", "")
            matter_id = data.get("matter_id", "")
            probe_type = data.get("probe_type", "parties_and_posture")
            custom_query = data.get("query", "")
            top_k = int(data.get("top_k", 4))

            # Check in-memory CPU RAM cache first (Zero LLM token cost & zero latency)
            cache_key = f"probe:{document_id or matter_id}:{probe_type}:{custom_query}:{top_k}"
            cached_hits = CPU_CACHE.get(cache_key)
            if cached_hits:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "probe_type": probe_type,
                    "document_id": document_id,
                    "results": cached_hits,
                    "cached": True,
                    "source": "cpu_memory_cache",
                }).encode("utf-8"))
                return

            # Construct targeted legal probe query
            PROBE_QUERIES = {
                "parties_and_posture": "cause title petitioner appellant respondent court coram bench case number filing proceeding",
                "holding_and_directions": "judgment operative order pronouncement held decree dismissed allowed directions",
                "procedural_history": "order passed notice issued hearing date filing dates interim application chronology",
                "issues_and_grounds": "questions of law framed issues points for determination grounds of appeal challenge",
                "statutes_and_sections": "sections acts statutory provisions applicability limitation arbitration constitution cpc crpc",
                "authorities_and_precedents": "precedents cited authorities case law judgment relied upon supreme court reported citation",
            }
            query_text = custom_query or PROBE_QUERIES.get(probe_type, "court order judgment")

            # Execute dense probe against Qdrant Cloud filtered by document_id
            probe_results = self.execute_document_probe(
                document_id=document_id,
                matter_id=matter_id,
                query=query_text,
                top_k=top_k,
            )

            # Store in CPU memory cache
            CPU_CACHE.set(cache_key, probe_results)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "probe_type": probe_type,
                "document_id": document_id,
                "results": probe_results,
                "cached": False,
                "source": "qdrant_cloud",
            }).encode("utf-8"))
            return

        # -------------------------------------------------------------
        # 3. /search : Global Hybrid Search
        # -------------------------------------------------------------
        if parsed.path == "/search":
            query = data.get("query", "")
            top_k = int(data.get("top_k", 5))
            doc_filter = data.get("doc_id", None)

            if not query.strip():
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Empty query"}).encode("utf-8"))
                return

            t_start = time.time()
            cache_key = f"search:{query.strip()}:{top_k}:{doc_filter}"
            cached_res = CPU_CACHE.get(cache_key)
            if cached_res:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "query": query,
                    "count": len(cached_res),
                    "duration_ms": 0.2,
                    "cached": True,
                    "results": cached_res,
                }).encode("utf-8"))
                return

            results = self.execute_hybrid_search(query.strip(), top_k=top_k, doc_filter=doc_filter)
            CPU_CACHE.set(cache_key, results)
            dur = time.time() - t_start

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "query": query,
                "count": len(results),
                "duration_ms": round(dur * 1000, 2),
                "cached": False,
                "results": results,
            }).encode("utf-8"))
            return

        if parsed.path == "/cache/clear":
            CPU_CACHE.clear()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "cleared"}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def execute_document_probe(
        self,
        document_id: str,
        matter_id: str,
        query: str,
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Query Qdrant Cloud filtered by document_id or matter_id using dense vector cosine similarity.
        Falls back to in-memory chunks if Qdrant filter index is indexing.
        """
        results = []

        # 1. Try Qdrant Cloud dense vector query with filter
        if qdrant_client is not None and embed_engine is not None:
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                query_vec = embed_engine.encode_query(query)

                filter_conditions = []
                if document_id:
                    filter_conditions.append(FieldCondition(key="document_id", match=MatchValue(value=document_id)))
                elif matter_id:
                    filter_conditions.append(FieldCondition(key="matter_id", match=MatchValue(value=matter_id)))

                q_filter = Filter(must=filter_conditions) if filter_conditions else None

                q_resp = qdrant_client.query_points(
                    collection_name=COLLECTION_NAME,
                    query=query_vec,
                    using="dense",
                    query_filter=q_filter,
                    limit=top_k,
                    with_payload=True,
                )

                for idx, pt in enumerate(q_resp.points, 1):
                    payload = pt.payload or {}
                    results.append({
                        "evidence_id": f"E{idx}",
                        "qdrant_point_id": str(pt.id),
                        "document_id": payload.get("document_id", document_id),
                        "chunk_id": payload.get("chunk_id", f"chk_{idx}"),
                        "score": round(float(pt.score), 4),
                        "court": payload.get("court", "Court Record"),
                        "case_title": payload.get("case_title", document_id),
                        "page_number": f"Page {payload.get('page_start', 1)}",
                        "paragraph_id": str(payload.get("paragraph_start", f"Para {idx}")),
                        "text": payload.get("text", ""),
                        "preview": (payload.get("text", "")[:350] + "..."),
                    })

                if results:
                    return results
            except Exception as e:
                print(f"Qdrant document probe error: {e}")

        # 2. Fallback to in-memory matching on DYNAMIC_CHUNKS or cached chunks
        doc_chunks = [c for c in DYNAMIC_CHUNKS if (document_id and c["document_id"] == document_id) or (matter_id and c.get("matter_id") == matter_id)]
        if not doc_chunks:
            doc_chunks = DYNAMIC_CHUNKS[-20:] if DYNAMIC_CHUNKS else []

        q_terms = [w.lower() for w in query.split() if len(w) > 2]
        scored_chunks = []
        for c in doc_chunks:
            c_text_lower = c["text"].lower()
            score = sum(10 for t in q_terms if t in c_text_lower)
            if score > 0:
                scored_chunks.append((score, c))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        for idx, (sc, c) in enumerate(scored_chunks[:top_k], 1):
            results.append({
                "evidence_id": f"E{idx}",
                "qdrant_point_id": generate_point_id(c["document_id"], c["chunk_id"]),
                "document_id": c["document_id"],
                "chunk_id": c["chunk_id"],
                "score": round(float(sc) / 100.0, 4),
                "court": c.get("court", "Court Record"),
                "case_title": c.get("case_title", document_id),
                "page_number": f"Page {c.get('page_start', 1)}",
                "paragraph_id": str(c.get("paragraph_start", f"Para {idx}")),
                "text": c["text"],
                "preview": (c["text"][:350] + "..."),
            })

        return results

    def execute_hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        doc_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search across Qdrant Cloud dense vector points + BM25 corpus + in-memory matter chunks.
        """
        combined = []
        seen_texts = set()

        # 1. Search in-memory dynamic and matter chunks
        all_matter_chunks = get_workspace_matter_chunks() + DYNAMIC_CHUNKS
        q_lower = query.lower()
        STOPWORDS = {
            "the", "and", "under", "with", "from", "that", "this", "which", "for", "are",
            "was", "were", "been", "have", "has", "had", "does", "did", "not", "but",
            "any", "all", "each", "into", "over", "such", "than", "then", "there", "their",
            "about", "against", "between", "through", "during", "before", "after", "above",
            "below", "upon", "down", "off", "out", "only", "same", "some", "what", "when",
            "where", "who", "whom", "why", "how", "act", "law", "court", "case", "order"
        }
        q_words = [w for w in re.findall(r"\b[a-z]{3,}\b", q_lower) if w not in STOPWORDS]
        scored_workspace = []

        for chk in all_matter_chunks:
            if doc_filter and chk.get("document_id") != doc_filter:
                continue
            chk_text_lower = chk["text"].lower()
            score = sum(8 for w in q_words if re.search(rf"\b{re.escape(w)}\b", chk_text_lower))
            key_terms = ["article 14", "article 15", "article 16", "section 34", "section 37", "section 5"]
            matched_key_terms = [
                term for term in key_terms
                if re.search(rf"\b{re.escape(term)}\b", q_lower) and re.search(rf"\b{re.escape(term)}\b", chk_text_lower)
            ]
            if matched_key_terms:
                score += 35
            # Only consider meaningful hits with at least 2 content words or statutory match
            if matched_key_terms or score >= 16:
                scored_workspace.append((score, chk))

        scored_workspace.sort(key=lambda x: x[0], reverse=True)
        for sc, chk in scored_workspace[:3]:
            txt_sub = chk["text"][:100]
            if txt_sub in seen_texts: continue
            seen_texts.add(txt_sub)
            combined.append({
                "evidence_id": f"E{len(combined)+1}",
                "qdrant_point_id": generate_point_id(chk["document_id"], chk.get("chunk_id", "chk")),
                "document_id": chk["document_id"],
                "chunk_id": chk.get("chunk_id", "chunk_001"),
                "score": round(float(sc), 4),
                "court": chk.get("court", "Court Record"),
                "case_title": chk.get("case_title", chk["document_id"]),
                "page_number": f"Page {chk.get('page_start', chk.get('page', 1))}",
                "paragraph_id": str(chk.get("paragraph_start", chk.get("para", "Para 1"))),
                "text": chk["text"],
                "preview": chk["text"][:350].strip() + ("..." if len(chk["text"]) > 350 else ""),
            })

        # 2. Search Qdrant Cloud dense vector collection
        if qdrant_client is not None and embed_engine is not None:
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                query_vec = embed_engine.encode_query(query)
                q_filter = Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=doc_filter))]) if doc_filter else None

                q_resp = qdrant_client.query_points(
                    collection_name=COLLECTION_NAME,
                    query=query_vec,
                    using="dense",
                    query_filter=q_filter,
                    limit=top_k,
                    with_payload=True,
                )

                for pt in q_resp.points:
                    payload = pt.payload or {}
                    txt = payload.get("text", "")
                    txt_sub = txt[:100]
                    if txt_sub in seen_texts: continue
                    seen_texts.add(txt_sub)

                    doc_id = payload.get("document_id", "")
                    title, court = resolve_case_metadata(doc_id, txt)
                    combined.append({
                        "evidence_id": f"E{len(combined)+1}",
                        "qdrant_point_id": str(pt.id),
                        "document_id": doc_id,
                        "chunk_id": payload.get("chunk_id", ""),
                        "score": round(float(pt.score), 4),
                        "court": payload.get("court", court),
                        "case_title": payload.get("case_title", title),
                        "page_number": f"Page {payload.get('page_start', 1)}",
                        "paragraph_id": str(payload.get("paragraph_start", "Para 1")),
                        "text": txt,
                        "preview": txt[:350].strip() + ("..." if len(txt) > 350 else ""),
                    })
                    if len(combined) >= top_k + 3:
                        break
            except Exception as e:
                print(f"Qdrant query error during hybrid search: {e}")

        # 3. Search BM25 corpus for lexical coverage
        if len(combined) < top_k + 3:
            bm25_hits = RETRIEVER.search(query=query, top_k=top_k)
            for h in bm25_hits:
                txt_sub = h.text[:100]
                if txt_sub in seen_texts: continue
                seen_texts.add(txt_sub)
                title, court = resolve_case_metadata(h.document_id, h.text)
                combined.append({
                    "evidence_id": f"E{len(combined)+1}",
                    "qdrant_point_id": generate_point_id(h.document_id, h.chunk_id),
                    "document_id": h.document_id,
                    "chunk_id": h.chunk_id,
                    "score": round(float(h.score), 4),
                    "court": court,
                    "case_title": title,
                    "page_number": "Reported",
                    "paragraph_id": "Holding",
                    "text": h.text,
                    "preview": h.text[:350].strip() + ("..." if len(h.text) > 350 else ""),
                })
                if len(combined) >= top_k + 3:
                    break

        return combined[:top_k + 3]

    def log_message(self, format, *args):
        return

class SilentThreadingHTTPServer(ThreadingHTTPServer):
    """Threading HTTPServer that gracefully suppresses BrokenPipeError and ConnectionResetError
    when clients disconnect prematurely (browser cancellations, timeouts, page navigation)."""
    def handle_error(self, request, client_address):
        exc_type, exc_val, _ = sys.exc_info()
        if exc_type in (BrokenPipeError, ConnectionResetError) or isinstance(
            exc_val, (BrokenPipeError, ConnectionResetError)
        ):
            return
        super().handle_error(request, client_address)

def run_daemon(host=None, port=None):
    if host is None:
        host = os.environ.get("HOST", "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
    if port is None:
        port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8008))
    server_address = (host, port)
    httpd = SilentThreadingHTTPServer(server_address, FastRetrievalHandler)
    print(f"Vidhik Document Intelligence Daemon listening on http://{host}:{port} (PID: {os.getpid()})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == "__main__":
    host = os.environ.get("HOST", None)
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8008))
    run_daemon(host=host, port=port)
