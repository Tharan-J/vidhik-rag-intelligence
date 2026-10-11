# VIDHIK — HYBRID PRODUCTION DEPLOYMENT RUNBOOK
## Render (Retrieval) + Vercel (Frontend) + Laptop AI Gateway (All Models via ngrok)

This guide provides end-to-end instructions for deploying and running **Vidhik** using our finalized hybrid architecture:
- **Vercel**: Next.js 16 Frontend & server-side API routes.
- **Render**: Python FastAPI Retrieval API (BM25 sparse + Qdrant Cloud hybrid retrieval). Does **not** load BGE-M3 into memory, fitting within Render's 512MB RAM limit.
- **Laptop**: All AI inference (BGE-M3 embeddings, Ollama Qwen generation, IndicTrans2 translation) behind an authenticated ngrok tunnel.
- **Qdrant Cloud**: Vector database holding the existing 29,345 legal chunks (1024-d BGE-M3 vectors in `vidhik_legal_chunks`).

---

## 1. System Architecture & Topology

```mermaid
graph TD
    Client["Browser / Jury Member"] -->|HTTPS| Vercel["Vercel: Next.js 16 Frontend\n(Landing Page, Lawyer Workspace, Public Chatbot)"]
    Vercel -->|Server-Side API Route| Render["Render: Python Retrieval Service\n(BM25 Lexical + Qdrant Cloud + RRF)"]
    Render -->|Dense Vector Queries| Qdrant["Qdrant Cloud\n('vidhik_legal_chunks' - 29,345 Vectors)"]
    Render -->|Query Embeddings /api/embed| Ngrok["ngrok HTTPS Tunnel\n(https://*.ngrok-free.app)"]
    Vercel -->|Qwen /api/generate & IndicTrans2 /api/translate| Ngrok
    Ngrok -->|Port 8010 (Bearer Protected)| LaptopGateway["Laptop AI Gateway\n(prototype/scripts/laptop_ai_gateway.py)"]
    LaptopGateway -->|Local Port 1024-d| BGEM3["Local BGE-M3 Engine\n(CPU/ONNX on Laptop)"]
    LaptopGateway -->|Port 11434| Ollama["Ollama (qwen3:4b-instruct)"]
    LaptopGateway -->|Port 8009| IndicTrans2["IndicTrans2 (CUDA Translation Daemon)"]
```

### Component Boundaries & Responsibilities

| Environment | Component | Port / Endpoint | Responsibility |
| :--- | :--- | :--- | :--- |
| **Vercel** | Next.js 16 Web App | `https://*.vercel.app` | UI, routing, lawyer matter workspace, public legal chat, auth gates, server-side API routes. Never leaks tokens to browser. |
| **Render** | Python Retrieval Service | `https://*.onrender.com` | BM25 lexical search (29,156 chunks), Qdrant queries, RRF fusion ($k=60$). Obtains query embeddings from Laptop Gateway (`POST /api/embed`). Degrades gracefully to BM25 when gateway is offline. |
| **Qdrant Cloud** | Vector Database | `https://*.aws.cloud.qdrant.io` | Pre-indexed 29,345 legal chunks (1024-d BGE-M3 vectors) with judicial metadata payloads. |
| **Laptop** | AI Gateway | Port `8010` (proxied via ngrok) | Authenticated, narrowly-scoped proxy for BGE-M3 embeddings, Qwen generation, and IndicTrans2 translation. |
| **Laptop** | Ollama | Port `11434` (local only) | `qwen3:4b-instruct` for structured legal evidence grounding and synthesis. |
| **Laptop** | IndicTrans2 | Port `8009` (local only) | AI4Bharat IndicTrans2 model on CUDA for multilingual legal translation with deterministic entity protection. |

---

## 2. Environment Variables Matrix

### A. Vercel (Frontend — Server-Side Only)
Configure under **Project Settings → Environment Variables**:

| Variable | Description | Example / Target Value |
| :--- | :--- | :--- |
| `RETRIEVAL_DAEMON_URL` | URL of deployed Render retrieval backend | `https://vidhik-retrieval.onrender.com` |
| `AI_GATEWAY_URL` | Public ngrok tunnel URL for laptop AI | `https://your-session.ngrok-free.app` |
| `AI_GATEWAY_TOKEN` | Shared secret token matching laptop gateway | `vidhik-jury-secret-token-2026` |

> [!CAUTION]
> Never prefix backend credentials (`QDRANT_API_KEY`, `AI_GATEWAY_TOKEN`) with `NEXT_PUBLIC_`. They must remain server-side only in Next.js API routes.

### B. Render (Retrieval Service)
Configure under **Service Settings → Environment**:

| Variable | Description | Target Value |
| :--- | :--- | :--- |
| `HOST` | Socket binding address | `0.0.0.0` |
| `PORT` | Listening port (assigned dynamically by Render) | `8008` |
| `QDRANT_URL` | Qdrant Cloud Cluster URL | `https://3921ee99-e17d-4568-902d-930bd975fd67.sa-east-1-0.aws.cloud.qdrant.io` |
| `QDRANT_API_KEY` | Qdrant Cloud API Key | `<your-qdrant-api-key>` |
| `AI_GATEWAY_URL` | ngrok tunnel URL (used by Render to request BGE-M3 embeddings) | `https://your-session.ngrok-free.app` |
| `AI_GATEWAY_TOKEN` | Shared secret token matching laptop gateway | `vidhik-jury-secret-token-2026` |
| `EMBEDDING_MODE` | Instructs retrieval daemon to use gateway embeddings | `gateway` |

### C. Laptop (Local AI Gateway & Inference)
Configure in local shell or `.env`:

| Variable | Description | Default Value |
| :--- | :--- | :--- |
| `GATEWAY_TOKEN` / `AI_GATEWAY_TOKEN` | Shared secret token required in Bearer header | `vidhik-jury-secret-token-2026` |
| `OLLAMA_URL` | Local Ollama endpoint | `http://127.0.0.1:11434` |
| `TRANSLATION_URL` | Local translation daemon endpoint | `http://127.0.0.1:8009` |

---

## 3. Laptop AI Setup Procedure (Step-by-Step)

Before the demonstration or during testing, start the four laptop processes:

### Terminal 1: Start Ollama (Qwen3)
```bash
ollama serve
# Verify qwen3:4b-instruct is pulled
ollama list
```

### Terminal 2: Start IndicTrans2 Translation Daemon
```bash
cd /home/tharan/Seeds/vidhik/vidhik-rag-intelligence
python prototype/scripts/translation_daemon.py 8009
```
*Verify with:* `curl -s http://127.0.0.1:8009/health`

### Terminal 3: Start Vidhik Local AI Gateway
```bash
cd /home/tharan/Seeds/vidhik/vidhik-rag-intelligence
python prototype/scripts/laptop_ai_gateway.py --port 8010 --token "vidhik-jury-secret-token-2026"
```
*Verify with:* `curl -s http://127.0.0.1:8010/health`
Should output: `{"status": "healthy", "embedding": {"available": true, "model": "BAAI/bge-m3", "dimension": 1024}, "ollama": {"available": true}, ...}`

### Terminal 4: Launch ngrok Tunnel
```bash
ngrok http 8010
```
Note the generated HTTPS forwarding URL (e.g. `https://your-session.ngrok-free.app`) and configure it in Render and Vercel.

---

## 4. Render Retrieval Service Deployment Procedure

1. Log in to [Render](https://render.com/).
2. Create a **New Web Service** connected to your repository (`vidhik-rag-intelligence`).
3. Settings:
   - **Environment**: `Docker` (builds from root `Dockerfile`).
   - **Instance Type**: Starter / Free (512 MiB RAM).
   - **Health Check Path**: `/health`.
4. Environment Variables:
   - `QDRANT_URL`: `https://3921ee99-e17d-4568-902d-930bd975fd67.sa-east-1-0.aws.cloud.qdrant.io`
   - `QDRANT_API_KEY`: `<your-qdrant-api-key>`
   - `AI_GATEWAY_URL`: `<your-ngrok-url>`
   - `AI_GATEWAY_TOKEN`: `vidhik-jury-secret-token-2026`
   - `EMBEDDING_MODE`: `gateway`

Because `torch` and `FlagEmbedding` are removed from the Render build:
- The container builds quickly and uses only ~120 MiB of RAM.
- BM25 and Qdrant client initialize instantly.
- Render passes its health check without downloading or loading BGE-M3.

---

## 5. Degraded Mode Operation

If the laptop gateway is temporarily unreachable (e.g., laptop sleep, network reconnection):
- Render does **not** crash.
- Retrieval automatically degrades to BM25 lexical search over the 29,156 chunk corpus.
- The API response explicitly flags `degraded: true` and `retrieval_mode: "bm25_degraded"`.
- When the gateway reconnects, hybrid retrieval resumes automatically without restarting Render.
