# VIDHIK — HYBRID PRODUCTION DEPLOYMENT & JURY DEMONSTRATION RUNBOOK

This guide provides end-to-end instructions for deploying and running the **Vidhik** legal intelligence prototype using a hybrid architecture for jury demonstration.

---

## 1. System Architecture & Topology

```mermaid
graph TD
    Client["Browser / Jury Member"] -->|HTTPS| Vercel["Vercel: Next.js 16 Frontend\n(Landing Page, Lawyer Workspace, Public Chatbot)"]
    Vercel -->|Server-Side API Route| Railway["Railway: Python Backend\n(Retrieval Daemon, BGE-M3 Dense, BM25 Okapi)"]
    Railway -->|Vector Queries (HTTPS)| Qdrant["Qdrant Cloud\n('vidhik_legal_chunks' - 29,345 Vectors)"]
    Vercel -->|Inference via ngrok| Ngrok["ngrok HTTPS Tunnel\n(https://*.ngrok-free.app)"]
    Railway -.->|Optional Direct Inference| Ngrok
    Ngrok -->|Port 8010| LaptopGateway["Laptop AI Gateway\n(prototype/scripts/laptop_ai_gateway.py)"]
    LaptopGateway -->|Port 11434| Ollama["Ollama (Qwen3:4b-instruct)"]
    LaptopGateway -->|Port 8009| IndicTrans2["IndicTrans2 (CUDA Translation Daemon)"]
```

### Component Boundaries & Responsibilities:

| Environment | Component | Port / Endpoint | Responsibility |
| :--- | :--- | :--- | :--- |
| **Vercel** | Next.js 16 Web App | `https://*.vercel.app` | UI, routing, lawyer matter workspace, public legal chat, auth gates, API routes. |
| **Railway** | Python Backend | `https://*.up.railway.app` | BM25 lexical search (29,156 chunks), BGE-M3 dense embeddings, hybrid retrieval, probe & ingest APIs. |
| **Qdrant Cloud** | Vector Database | `https://*.aws.cloud.qdrant.io` | Pre-indexed 29,345 legal chunks (1024-d BGE-M3 vectors) with judicial metadata payloads. |
| **Laptop** | AI Gateway | Port `8010` (proxied via ngrok) | Authenticated, narrowly-scoped proxy for local AI inference. |
| **Laptop** | Ollama | Port `11434` (local only) | `qwen3:4b-instruct` for structured evidence grounding and legal synthesis. |
| **Laptop** | IndicTrans2 | Port `8009` (local only) | AI4Bharat IndicTrans2 model on CUDA for Tamil/Hindi translation with entity preservation. |

---

## 2. Environment Variables Matrix

### A. Vercel (Frontend — Server-Side Only)
Configure under **Project Settings → Environment Variables**:

| Variable | Description | Example / Target Value |
| :--- | :--- | :--- |
| `RETRIEVAL_DAEMON_URL` | URL of deployed Railway backend | `https://vidhik-backend.up.railway.app` |
| `AI_GATEWAY_URL` | Public ngrok tunnel URL for laptop AI | `https://your-session.ngrok-free.app` |
| `AI_GATEWAY_TOKEN` | Shared secret token matching laptop gateway | `vidhik-jury-secret-token-2026` |
| `NEXT_PUBLIC_API_URL` | Public backend URL (optional) | `https://vidhik-backend.up.railway.app` |

> [!CAUTION]
> Never prefix backend credentials (`QDRANT_API_KEY`, `AI_GATEWAY_TOKEN`) with `NEXT_PUBLIC_`. They must remain server-side only.

### B. Railway (Backend & Retrieval)
Configure under **Service → Variables**:

| Variable | Description | Example / Target Value |
| :--- | :--- | :--- |
| `HOST` | Socket binding address | `0.0.0.0` |
| `PORT` | Listening port (assigned dynamically by Railway) | `8008` (Railway sets this automatically) |
| `QDRANT_URL` | Qdrant Cloud Cluster URL | `https://3921ee99-e17d-4568-902d-930bd975fd67.sa-east-1-0.aws.cloud.qdrant.io` |
| `QDRANT_API_KEY` | Qdrant Cloud API Key | `<your-qdrant-api-key>` |
| `AI_GATEWAY_URL` | ngrok tunnel URL (for Python RAG engine) | `https://your-session.ngrok-free.app` |
| `AI_GATEWAY_TOKEN` | Shared secret token matching laptop gateway | `vidhik-jury-secret-token-2026` |

### C. Laptop (Local AI Gateway)
Configure in local shell or `.env`:

| Variable | Description | Default Value |
| :--- | :--- | :--- |
| `GATEWAY_TOKEN` | Shared secret token required in Bearer header | `vidhik-jury-secret-token-2026` |
| `OLLAMA_URL` | Local Ollama endpoint | `http://127.0.0.1:11434` |
| `TRANSLATION_URL` | Local translation daemon endpoint | `http://127.0.0.1:8009` |

---

## 3. Laptop AI Setup Procedure (Step-by-Step)

Before the demonstration, open three terminal windows on the development laptop:

### Terminal 1: Start Ollama (Qwen3)
```bash
# Verify Ollama is running and qwen3:4b-instruct is pulled
ollama list
# If not already running as a system service:
ollama serve
```

### Terminal 2: Start IndicTrans2 Translation Daemon
```bash
# Activate your conda/python environment with PyTorch & CUDA
conda activate myenv
cd /home/tharan/Seeds/vidhik/vidhik-rag-intelligence

# Start translation daemon on port 8009
python prototype/scripts/translation_daemon.py 8009
```
*Verify with:* `curl -s http://127.0.0.1:8009/health` → `{"status": "healthy", "device": "cuda"}`

### Terminal 3: Start Vidhik Local AI Gateway
```bash
cd /home/tharan/Seeds/vidhik/vidhik-rag-intelligence

# Launch authenticated gateway on port 8010
python prototype/scripts/laptop_ai_gateway.py --port 8010 --token "vidhik-jury-secret-token-2026"
```
*Verify with:* `curl -s http://127.0.0.1:8010/health` → `{"status": "healthy", "ollama": {"available": true}, "indictrans2": {"available": true}}`

### Terminal 4: Launch ngrok Tunnel
```bash
ngrok http 8010
```
Note the generated HTTPS forwarding URL (e.g. `https://a1b2-c3d4.ngrok-free.app`).

---

## 4. Railway Backend Deployment Procedure

### Option A: Railway Dashboard (Recommended)
1. Log in to [Railway](https://railway.app/).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select `vidhik-rag-intelligence`.
4. Under **Settings**:
   - Build Type: **Dockerfile** (uses the root `Dockerfile` in the repository).
5. Under **Variables**, add:
   - `HOST`: `0.0.0.0`
   - `QDRANT_URL`: `https://3921ee99-e17d-4568-902d-930bd975fd67.sa-east-1-0.aws.cloud.qdrant.io`
   - `QDRANT_API_KEY`: `<your_qdrant_api_key>`
   - `AI_GATEWAY_URL`: `<your_current_ngrok_url>`
   - `AI_GATEWAY_TOKEN`: `vidhik-jury-secret-token-2026`
6. Click **Deploy**.
7. Under **Settings → Networking**, generate a public domain (e.g. `vidhik-backend.up.railway.app`).
8. Verify health check:
   ```bash
   curl -s https://vidhik-backend.up.railway.app/health
   ```
   Expected response:
   ```json
   {"status":"healthy","qdrant_connected":true,"qdrant_collection":"vidhik_legal_chunks","bm25_chunks":29156}
   ```

### Option B: Railway CLI
```bash
railway login
railway init
railway up
railway variables set HOST=0.0.0.0 QDRANT_URL="https://3921ee99-e17d-4568-902d-930bd975fd67.sa-east-1-0.aws.cloud.qdrant.io" QDRANT_API_KEY="<key>" AI_GATEWAY_URL="<ngrok_url>" AI_GATEWAY_TOKEN="vidhik-jury-secret-token-2026"
```

---

## 5. Vercel Frontend Deployment Procedure

### Option A: Vercel Dashboard (Recommended)
1. Log in to [Vercel](https://vercel.com/).
2. Click **Add New...** → **Project**.
3. Import `vidhik-rag-intelligence`.
4. In the Project Configuration:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
5. Under **Environment Variables**, add:
   - `RETRIEVAL_DAEMON_URL`: `https://vidhik-backend.up.railway.app`
   - `AI_GATEWAY_URL`: `<your_current_ngrok_url>`
   - `AI_GATEWAY_TOKEN`: `vidhik-jury-secret-token-2026`
6. Click **Deploy**.

### Option B: Vercel CLI
```bash
cd frontend
vercel --prod
```

---

## 6. End-to-End Jury Live Demonstration Checklist

Execute this sequence to demonstrate all core capabilities live:

1. **Open the Vercel Production URL**:
   - Access `https://your-vidhik-app.vercel.app/`
   - Verify authoritative design, typography, and responsive navigation.

2. **Navigate to Public Legal Chatbot**:
   - Click **Get Started** on the hero section or navbar.
   - Verify instant navigation to `/chat` (Public Multilingual Legal Assistant) without any login prompt.

3. **Demonstrate Conversational Mode (Research OFF)**:
   - Keep the toggle set to **Research OFF**.
   - Submit: *"What is anticipatory bail under Indian law?"*
   - Verify response generated from local Qwen explains Section 438 of CrPC/BNSS with the disclaimer: *"This response provides general legal information only"*.

4. **Demonstrate Evidence-Grounded Mode (Research ON)**:
   - Switch toggle to **Research ON**.
   - Submit: *"What is the limitation period for filing an appeal in arbitration under the Commercial Courts Act?"*
   - Observe real-time retrieval from Qdrant Cloud + BM25 across 29,156 legal chunks.
   - Verify answer cites authoritative authorities (e.g. *Govt. of Maharashtra v. Borse Brothers [2021 INSC 194]* and *DDA v. Ajab Singh [DLHC010427042021]*).
   - Inspect the **Verified Authorities** card showing exact page numbers, paragraph coordinates, and confidence score.

5. **Demonstrate IndicTrans2 Multilingual Translation**:
   - Change language selector in navbar to **Tamil (தமிழ்)** or **Hindi (हिन्दी)**.
   - Click the question again or submit a query.
   - Verify translation preserves protected legal citations (*Supreme Court of India*, *Article 116*, *Borse Brothers*) using IndicTrans2.
   - Click **View Original English** button to demonstrate bilingual transparency.

6. **Demonstrate Lawyer Workspace**:
   - In navbar, click **Lawyer Portal** (`/login`).
   - Enter credentials: `arjun.sharma@vidhik.legal` / `advocate@2026`.
   - Access `/lawyer` Matter Workspace.
   - Open matter `MAT-2026-0891` (*Maharashtra vs Borse Brothers*).
   - Inspect evidence tabs, statutory provisions, and document intelligence probes.

7. **Demonstrate Gateway Safeguards & Error Handling**:
   - Temporarily pause the laptop AI gateway (`Ctrl+C` in Terminal 3).
   - Submit a chat query in the browser.
   - Verify the UI displays a clean status alert: *"Local legal AI model (Ollama Qwen) is currently unavailable"*, confirming that the system does NOT fabricate answers or secretly fall back to external providers.
   - Restart the gateway to resume normal operation.

---

## 7. Known Constraints & Failure Mitigations

| Scenario | Behavior | Mitigation |
| :--- | :--- | :--- |
| **Laptop sleep or screen closed** | ngrok disconnects; cloud requests fail with HTTP 503. | Set laptop to "Do not sleep when plugged in". |
| **ngrok restarts & changes URL** | Old URL returns 404 or connection failure. | Update `AI_GATEWAY_URL` in Vercel & Railway dashboards (takes ~30s). Alternatively, use an ngrok reserved domain: `ngrok http --domain=your-name.ngrok-free.app 8010`. |
| **Inference Cold Start** | First Qwen request takes 8–12 seconds while model weights are loaded into VRAM. | Warm up model before jury demo with: `curl -s -X POST http://127.0.0.1:8010/api/generate -H "Authorization: Bearer vidhik-jury-secret-token-2026" -d '{"prompt":"warmup"}'`. |
| **Ephemeral Container Storage** | Railway container restarts wipe local `/tmp` files. | All 29,345 dense vectors reside permanently in Qdrant Cloud; BM25 index reconstructs dynamically in RAM from `bm25_mapping.parquet` upon boot. No critical data is lost. |
| **Vercel Serverless Timeout** | Complex RAG research may exceed Vercel's default 10s limit. | `frontend/vercel.json` configures `maxDuration: 60` seconds for all API routes. |

---

## 8. Rollback Procedure

If any deployment step fails:
1. **Frontend Rollback**:
   In Vercel Dashboard → **Deployments** → Select previous deployment → Click **Promote to Production**.
2. **Backend Rollback**:
   In Railway Dashboard → **Deployments** → Select previous deployment → Click **Rollback**.
3. **Local Development Fallback**:
   If jury wifi fails, present entirely offline using:
   - Terminal 1: `ollama serve` (port 11434)
   - Terminal 2: `python prototype/scripts/translation_daemon.py 8009`
   - Terminal 3: `python prototype/scripts/retrieval_daemon.py 8008`
   - Terminal 4: `cd frontend && npm run dev` (port 3000)
