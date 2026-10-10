# Vidhik Frontend — Next.js 16 Legal Intelligence Application

This is the Next.js 16 frontend application for **Vidhik**, providing both the **Advocate Matter Workspace** and the **Public Multilingual Legal Assistant**.

## Key Features & Routes

- `/` — Vidhik Landing Page highlighting legal verification guarantees and quick access.
- `/chat` — Public Multilingual Legal Assistant (Mode A: Conversational Legal Information, Mode B: Evidence-Grounded Research).
- `/login` — Advocate Workspace authentication portal.
- `/lawyer` — Authenticated lawyer matter management workspace.
- `/lawyer/matters/[matterId]` — Deep-dive matter dossier with evidence inspection, statutory mapping, timeline, and document intelligence probes.
- `/api/public/chat` — Server-side public chatbot endpoint connecting to local Qwen, IndicTrans2, and retrieval daemon.
- `/api/translate` — Real-time legal translation endpoint with protected entity preservation.
- `/api/research` — Grounded legal research endpoint.

## Local Development

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Production Build

```bash
npm run build
npm start
```

## Environment Configuration

Configure server-side environment variables in `.env.local` or Vercel dashboard:
- `RETRIEVAL_DAEMON_URL` — URL of deployed Railway backend.
- `AI_GATEWAY_URL` — ngrok URL for laptop AI inference.
- `AI_GATEWAY_TOKEN` — Bearer token for AI Gateway.
