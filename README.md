# VIDHIK — Indian Legal Intelligence & Judicial Authority Verification System

> **"Research the law. Trace every authority. Zero hallucination."**

Vidhik is a specialized, production-ready legal intelligence system engineered specifically for the Indian judicial and constitutional framework. Unlike generic LLM wrappers that hallucinate non-existent case laws and corrupt legal citations, Vidhik enforces strict **cryptographic and citation-level evidence grounding** across Supreme Court, High Court, and statutory precedents.

---

## 🏛️ Key Capabilities & Product Features

### 1. Dual User Journeys

#### A. Advocate Matter Workspace (`/lawyer`)
*Designed for practicing advocates, corporate legal teams, and judicial researchers:*
- **Active Matter Dossiers**: Structured workspaces organizing case briefs, pleadings, FIRs, and judgments.
- **Targeted Document Intelligence Probes**: Instant extraction and verification of:
  - Parties & Procedural Posture (Petitioner, Respondent, Impugned Orders)
  - Core Legal Issues & Substantive Controversy
  - Statutory Mapping (e.g., Limitation Act, Commercial Courts Act, Arbitration Act, IPC/BNS)
  - Procedural Chronology & Timeline of Events
- **Cryptographic Provenance**: Every cited authority is tied to page-number, paragraph coordinates, and SHA-256 verified document manifests.
- **Audit Trails**: Full verification status (`VERIFIED_EXACT`, `VERIFIED_PASS`, `UNVERIFIED`) for every proposition.

#### B. Public Multilingual Legal Assistant (`/chat`)
*Designed for citizens seeking transparent, accessible legal information without authentication barriers:*
- **Dual Analytical Modes**:
  - **Mode A: Conversational Legal Information (Research OFF)**: Explains legal concepts, fundamental rights, procedural remedies, and statutory provisions via local Qwen with explicit public disclaimers that the information is general and unverified against active judicial files.
  - **Mode B: Judicial Research Mode (Research ON)**: Real-time hybrid retrieval (BGE-M3 + BM25) across 29,156 frozen court chunks. Answers are strictly constrained to retrieved judicial evidence, citing `[E1]`, `[E2]` inline and displaying verified court metadata.
  - **Strict Abstention Guarantee**: If authoritative evidence is insufficient or targets are irrelevant, the system explicitly abstains rather than inventing legal rules.

### 2. High-Fidelity Multilingual Representation (IndicTrans2)
- Translates legal analyses into **Tamil (தமிழ்)**, **Hindi (हिन्दी)**, **Kannada (ಕನ್ನಡ)**, and **Marathi (मराठी)**.
- **Protected Entity Preservation**: Uses deterministic slot-tagging (`__LEGAL_ENT_0__`) to guarantee that court names (*Supreme Court of India*), statutory provisions (*Article 116*, *Section 34*), case citations (*2021 INSC 194*), and judicial dispositions (*dismissed*, *allowed*, *quashed*) are **never corrupted or mistranslated**.
- **Side-by-Side Verification**: Single-click toggling between the translated vernacular and original authoritative English text.

---

## ⚙️ Technical Architecture & Pipeline

```
[ User Query ]
      │
      ▼
[ Query Analysis & Target Extractor ]
      │
      ├─────────────────────────────────────────┐
      │ (Mode B: Research ON)                   │ (Mode A: Research OFF)
      ▼                                         ▼
[ Hybrid Retrieval Pipeline ]           [ Conversational Assistant ]
 ├─ Dense: BGE-M3 (1024-d, Qdrant Cloud)   └─ Local Ollama Qwen3
 ├─ Sparse: BM25 Okapi (29,156 Chunks)
 └─ Fusion: Reciprocal Rank Fusion (RRF)
      │
      ▼
[ Relevance & Evidence Verification Gate ]
 ├─ Lexical statutory & token matching
 └─ Coordinate verification (Page / Para)
      │
      ▼
[ Evidence-Constrained Generator ]
 └─ Local Ollama (qwen3:4b-instruct via Gateway)
      │
      ▼
[ Multilingual Transformation Layer ]
 └─ IndicTrans2 (CUDA daemon on Port 8009)
 └─ Protected Entity Alignment & Verification Audit
      │
      ▼
[ Structured Legal Answer with Provenance ]
```

---

## 🌐 Hybrid Production Deployment Topology

Vidhik is built for a reliable, hybrid jury demonstration across 4 environments:

| Environment | Component | Purpose |
| :--- | :--- | :--- |
| **Vercel** | Next.js 16 (App Router) | Global edge hosting for landing page, lawyer workspace, and public chat interface. |
| **Railway** | Python Backend | Fast retrieval daemon, BGE-M3 embedding engine, and in-memory BM25 index. |
| **Qdrant Cloud** | Vector Database | 29,345 pre-embedded legal judgment chunks in collection `vidhik_legal_chunks`. |
| **Laptop / ngrok** | Local AI Gateway | Local GPU inference for Ollama `qwen3:4b-instruct` and AI4Bharat IndicTrans2. |

For detailed step-by-step deployment instructions, environment variables, and live demonstration scripts, refer to [DEPLOYMENT.md](file:///home/tharan/Seeds/vidhik/vidhik-rag-intelligence/DEPLOYMENT.md).

---

## 🚀 Quickstart for Local Development

### Prerequisites
- Node.js 18+ & npm
- Python 3.10+ with CUDA (optional for GPU translation)
- Ollama with `qwen3:4b-instruct`

### 1. Start Local AI Services (Terminal 1 & 2)
```bash
# Terminal 1: Local Ollama
ollama serve

# Terminal 2: IndicTrans2 Translation Daemon
python prototype/scripts/translation_daemon.py 8009
```

### 2. Start Backend Retrieval Daemon (Terminal 3)
```bash
cd prototype
python scripts/retrieval_daemon.py 8008
```

### 3. Start Frontend (Terminal 4)
```bash
cd frontend
npm install
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to open the Vidhik application.

---

## 🔒 Security & Judicial Integrity Safeguards

- **Zero Fabricated Precedents**: The model is prohibited from citing any case that does not exist in the retrieved evidence set.
- **Server-Side Credential Isolation**: Qdrant Cloud API keys and AI Gateway tokens are strictly managed server-side. No credentials exist in browser bundles.
- **Matter Isolation**: Lawyer dossiers, private uploaded briefs, and FIR records are protected behind lawyer authentication and isolated from public chatbot access.
- **Graceful Fault Reporting**: If the local AI inference host sleeps or disconnects, the system returns a clear `503 Service Unavailable` status rather than silently hallucinating or falling back to unverified third-party models.

---

## 📄 License & Attribution

- Built for Indian Legal Technology & Judicial Research.
- Court judgments and case materials are public legal records subject to their respective court registries.
