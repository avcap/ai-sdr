# AI-SDR Repository Analysis

Expert review of the **exact codebase** (no guessing beyond what exists in the files).  
You are the human owner of this project.

---

## 1. High-level overview

### What is this project (ai-sdr) designed to do?

**AI SDR** is an **AI-powered Sales Development Representative (SDR) platform** for B2B outbound: prospecting, personalized outreach, reply tracking, and meeting booking. It is built as a **multi-tenant web app** with:

- **Campaign and lead management** (create campaigns, upload/edit leads, track status).
- **AI agents** for lead generation, personalization, copywriting, enrichment, and campaign execution.
- **Email sequences** with steps (email, delay, condition, action), scheduling, and enrollment.
- **Google integration**: OAuth (Gmail send, Sheets, Drive), so campaigns can send real email and track in Sheets.
- **Knowledge base**: upload company/sales docs, extract structured knowledge (Claude), and use it for suggestions and personalization.
- **Analytics**: campaign stats, funnel, activity, export; sequence analytics; campaign intelligence suggestions.

So in one sentence: **multi-tenant AI SDR that runs outreach campaigns and sequences using Gmail/Sheets and optional knowledge from uploaded docs.**

### Current end-to-end workflow or user journey

1. **Auth**  
   User signs in (NextAuth: credentials `demo@example.com` / `password` or Google OAuth). Frontend is Next.js; backend is FastAPI.

2. **Optional: Train your team**  
   Upload docs (PDF, DOCX, TXT, etc.) → backend extracts knowledge via **Claude** (`KnowledgeExtractionAgent`) → stored in Supabase `user_knowledge` / `training_documents`. Used later for campaign suggestions and personalization.

3. **Campaigns**  
   Create campaign (name, description, etc.) → add leads (manual or CSV upload) → optionally run **Prospector** (AI-generated leads), **Enrichment**, or **Copywriter** (personalize message).  
   **Execute campaign**: backend uses `agents.google_workflow.AISDRWorkflow` — validates leads, generates personalized email (OpenAI), sends via **Gmail** (user’s OAuth), creates a **Google Sheet** for tracking.  
   **Email blast**: generate one blast email (AI) and send to campaign leads; tracked in `email_blasts` / `email_blast_recipients`.

4. **Sequences**  
   Create sequence (steps: email, delay, condition, action) → assign to campaign or enroll leads → activate.  
   **Sequence execution**: `SequenceExecutionService` runs on an **APScheduler** interval (every 1 min in `main_supabase.py`). It activates scheduled enrollments and runs steps whose `next_action_at` is due; email steps send via Gmail (using tenant’s Google tokens). State is in Supabase (`sequence_enrollments`, `sequence_step_executions`).

5. **Analytics**  
   Dashboard: campaign list with stats; per-campaign: stats, activity, funnel, export; sequence analytics; campaign intelligence suggestions (from knowledge + LLM).

6. **Google Sheets**  
   User can list/preview/import Sheets (OAuth); campaign execution can create a Sheet and update rows.

### What is implemented vs stubbed or planned?

| Area | Implemented | Stubbed / partial / planned |
|------|-------------|-----------------------------|
| Campaign CRUD, leads, upload | ✅ Full (Supabase or SQLite) | — |
| Google OAuth (Gmail, Sheets, Drive) | ✅ Implemented in `integrations/google_oauth_service.py`, used in `google_workflow` and sequence execution | — |
| Sending email (Gmail vs SMTP) | ✅ Gmail via OAuth in workflow/sequence; ✅ SMTP in `integrations/email_service.py` (used by sequence execution when no Gmail token) | — |
| AI personalization (one-off message) | ✅ OpenAI in `google_workflow.PersonalizationTool` | — |
| AI lead generation (Prospector) | ✅ `agents/prospector_agent.py` (OpenAI) | Generates fictional leads (placeholder LinkedIn URLs, etc.) |
| Copywriter / variations | ✅ `agents/copywriter_agent.py` (OpenAI/Anthropic), API and UI | Some Claude paths are placeholders (e.g. “placeholder - would need Anthropic client”) |
| Enrichment agent | ✅ `agents/enrichment_agent.py` | — |
| Smart campaign / smart outreach | ✅ Orchestrator and execute/save endpoints | Smart outreach “send” is placeholder (no real LinkedIn/email send in agent) |
| Knowledge extraction | ✅ Claude in `knowledge_extraction_agent.py`, stored in Supabase | — |
| Knowledge retrieval for agents | ✅ `KnowledgeService` reads from Supabase (no vector search) | RAG/vector retrieval **not** implemented (see §5) |
| Sequence execution (scheduler) | ✅ APScheduler in `main_supabase.py`, email/delay/condition/action steps | Reply detection “not implemented yet” (TODO in `sequence_execution_service`) |
| Campaign intelligence suggestions | ✅ From knowledge + LLM in `CampaignIntelligenceService` | — |
| Phase 3 (adaptive strategy, market intel, LLM recommendation, knowledge fusion, predictive analytics) | ✅ Endpoints and services exist | Some depend on Grok; Grok service returns mock when key missing |
| LinkedIn | ❌ | LinkedIn sending “not implemented yet” in backend; `integrations/linkedin_service.py` has OAuth/message stubs |
| CrewAI “Crew” orchestration | ❌ | `agents/workflow.py` defines CrewAI Agents/Tasks but **RagTool is imported and never used**; `google_workflow` does **not** use Crew, it uses a fixed tool chain (Prospecting → Personalization → Gmail/Sheets/Coordinator) |

So: the **real** execution path today is **custom tool chain** in `agents/google_workflow.py` (and optionally `agents/workflow.py` for a non-Google, simulated path). CrewAI is present in code but the main flow doesn’t rely on it.

---

## 2. Current functionality

### What can the system do right now if you run it today?

- **Backend (Supabase)**  
  Run `python backend/main_supabase.py` (or `uvicorn backend.main_supabase:app --host 0.0.0.0 --port 8000`).  
  Requires: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and for AI: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`; for Google: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`.  
  Optional: `GROK_API_KEY`, `SMTP_*` for fallback email, `JWT_SECRET` for auth.

- **Frontend**  
  Run `cd frontend && npm run dev`.  
  Uses `NEXT_PUBLIC_BACKEND_URL` or `http://localhost:8000` to call the backend.

- **Auth**  
  Sign in with credentials `demo@example.com` / `password` or Google OAuth (if configured).  
  Backend uses a hardcoded demo user in `get_current_user()` in `main_supabase.py`; multi-tenant backend `backend_multi_tenant.py` has a “placeholder for auth” and “TODO: Implement proper JWT authentication”.

- **Flows that work end-to-end**  
  - Create campaign → add/upload leads → execute campaign (with Google OAuth: real Gmail sends + Sheet creation).  
  - Create sequence → add steps → enroll leads → activate → scheduler runs steps (email steps send via Gmail).  
  - Train your team: upload docs → extract knowledge → use in campaign suggestions / copy.  
  - Prospector: generate leads (synthetic); Copywriter: personalize; Enrichment: validate/enrich; Campaign intelligence: suggestions from knowledge.  
  - Email blast: generate one blast email (AI) and send to campaign leads; tracking in DB.

### Main commands, entrypoints, scripts

| Command / script | What it does |
|------------------|--------------|
| `./start.sh` | Activates venv, copies `.env` from `env.example` if missing, starts **backend/main.py** (SQLite) and **frontend** `npm run dev`. Does **not** start the Supabase backend. |
| `./start_backend.sh` | Sets Supabase/Anthropic env vars from env, runs **backend_multi_tenant.py** (simpler Supabase CRUD API, no full AI workflow). |
| `python backend/main.py` | Starts FastAPI with SQLite, optional Redis/Celery; uses `agents.google_workflow` and same Google/OAuth integrations. |
| `python backend/main_supabase.py` | Starts **full** FastAPI backend with Supabase: campaigns, sequences, train-your-team, phase3, campaign intelligence, sequence scheduler, email blast, etc. |
| `python backend_multi_tenant.py` | Starts minimal multi-tenant API (tenants, users, campaigns, knowledge) — no sequence execution, no Google workflow. |
| `python demo_google_integration.py` | Demo script: checks Google OAuth config and runs a dry-run of `AISDRWorkflow` with sample leads/campaign (no real send unless you wire it). |
| `pip install -r requirements.txt` | Python deps (CrewAI, FastAPI, OpenAI, Anthropic, Supabase, Google libs, etc.). |
| `cd frontend && npm install && npm run dev` | Frontend on port 3000. |

So: for the **full** app (sequences, scheduler, intelligence, blast) you must run **backend/main_supabase.py** and point frontend to it; `start.sh` alone gives you the SQLite backend.

### Configuration and environment variables

- **Backend**  
  See `env.example` and `env.google.example`.  
  Required for Supabase backend: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.  
  For AI: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`.  
  For Google: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` (e.g. `http://localhost:3000/auth/google/callback` or `/api/auth/callback/google` to match NextAuth).  
  Optional: `GROK_API_KEY`, `GROK_API_URL`; SMTP vars; `JWT_SECRET_KEY`; Phase 3 model names and thresholds.

- **Frontend**  
  NextAuth and Google: `NEXTAUTH_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `NEXTAUTH_URL`.  
  API: `NEXT_PUBLIC_BACKEND_URL` (default `http://localhost:8000`).  
  Some API routes use `BACKEND_URL` (server-side) or hardcoded `http://localhost:8000` (e.g. `frontend/pages/api/auth/google/disconnect.js`).

- **Database**  
  Supabase (PostgreSQL). Schema in `supabase_schema.sql`; migrations in `supabase_migrations/` and `phase3_sequence_execution.sql`, `add_email_blast_tracking.sql`, etc. Tables: tenants, users, campaigns, leads, user_knowledge, training_documents, sequences, sequence_steps, sequence_enrollments, sequence_step_executions, agent_results, audit_logs, email_blasts, etc.

---

## 3. Architecture & components

### Overall architecture

- **Frontend**: Next.js 14, NextAuth (credentials + Google), Tailwind, Recharts.  
  Pages: dashboard, campaigns (list + detail), sequences (list, edit, analytics), knowledge-bank, auth.  
  API routes under `frontend/pages/api/*` proxy to the FastAPI backend (using `NEXT_PUBLIC_BACKEND_URL` or `BACKEND_URL`).

- **Backend**: FastAPI. Two “full” entrypoints:  
  - **main.py**: SQLite, optional Redis/Celery.  
  - **main_supabase.py**: Supabase only, APScheduler for sequence execution.  
  One “slim” entrypoint: **backend_multi_tenant.py** (Supabase CRUD, no scheduler, no workflow).

- **Agents** (under `agents/`):  
  - **google_workflow.py**: `AISDRWorkflow` — ProspectingTool, PersonalizationTool (OpenAI), GmailTool, GoogleSheetsTool, OutreachTool, CoordinatorTool. No CrewAI; just a fixed pipeline.  
  - **workflow.py**: CrewAI Agents and Tasks (Prospecting, Personalization, Outreach, Coordinator) with tools that **simulate** outreach (no real send).  
  - **prospector_agent.py**, **copywriter_agent.py**, **enrichment_agent.py**, **smart_outreach_agent.py**, **smart_campaign_orchestrator.py**: used by API routes; OpenAI/Anthropic.  
  - **knowledge_extraction_agent.py**: Claude, extracts structured knowledge from uploaded files.  
  - **adaptive_ai_agent.py**, **adaptive_prompt_processor.py**: Phase 3 style adaptation.

- **Services** (under `services/`):  
  - **SupabaseService**: all DB access (tenants, users, campaigns, leads, knowledge, sequences, enrollments, steps, executions, email blasts, etc.).  
  - **KnowledgeService**: get and aggregate user knowledge from Supabase by task type (no vectors).  
  - **SequenceExecutionService**: activate scheduled enrollments and execute steps (email/delay/condition/action) using Gmail/SMTP and Supabase.  
  - **CampaignIntelligenceService**: suggestions from knowledge + LLM.  
  - **AISequenceGenerator** (e.g. `services/ai_sequence_generator.py`): AI sequence generation.  
  - **LLM selector**, **knowledge fusion**, **market monitoring**, **predictive analytics**: Phase 3.

- **Integrations** (under `integrations/`):  
  - **google_oauth_service.py**: OAuth flow, Gmail send, Sheets, Drive (used by workflow and sequence execution).  
  - **email_service.py**: SMTP/IMAP (sending and optional reply parsing).  
  - **linkedin_service.py**: OAuth and message stubs (sending not implemented).  
  - **google_sheets_service.py**: legacy/service-account style (if used).  
  - **grok_service.py**: Grok API for market intel; fallback to mock if no key.

### Multi-agent vs single-agent

- **Multi-agent**: Several agents with distinct roles (Prospector, Copywriter, Enrichment, Smart Outreach, Smart Campaign, Knowledge Extraction). They are invoked by the API layer for specific tasks (generate leads, personalize, suggest campaigns, etc.); there is no single “orchestrator” that runs a full Crew.  
- **CrewAI** in `workflow.py` defines a Crew with four agents and tasks, but the **live** campaign execution path uses **google_workflow.py**, which does **not** use CrewAI—it’s a linear tool chain.  
- So: **multi-agent in the sense of multiple specialized agents**; **not** a single CrewAI Crew driving the main flow.

### Data flow (inputs → processing → outputs)

- **Campaign execute**:  
  Request (campaign_id, user context) → load campaign + leads from Supabase → get user Google tokens → `AISDRWorkflow.execute_campaign` → ProspectingTool validates leads → PersonalizationTool (OpenAI) generates message per lead → OutreachTool sends via Gmail → CoordinatorTool creates/updates Sheet → results and logs stored in Supabase.

- **Sequence execution**:  
  Scheduler (every 1 min) → `SequenceExecutionService.process_all_sequences` → activate enrollments where `next_action_at` passed → for each active enrollment due for next step, load step → if email: personalize body/subject, send via Gmail (or SMTP), log to `sequence_step_executions`, advance `current_step` and `next_action_at`.

- **Knowledge**:  
  Upload file → store in `training_documents` → KnowledgeExtractionAgent (Claude) extracts structured fields → save to `user_knowledge`.  
  Later: CampaignIntelligenceService / KnowledgeService reads from `user_knowledge` (no vector search) and feeds context to LLM for suggestions or copy.

---

## 4. Tools, frameworks, and services

### AI / LLM frameworks

- **CrewAI** (`crewai`, `crewai_tools`): Used in `agents/workflow.py` (Agent, Task, Crew, Process). **RagTool** is imported but never instantiated or used. The main execution path does not use CrewAI.
- **OpenAI API**: Used directly (`openai` client) in `google_workflow.PersonalizationTool`, `prospector_agent`, `copywriter_agent`, `enrichment_agent`, `smart_outreach_agent`, `smart_campaign_orchestrator`, `campaign_intelligence_service`, `ai_sequence_generator`, etc.
- **Anthropic**: Used in `knowledge_extraction_agent`, `campaign_intelligence_service`, `sales_playbook_service`, and others for Claude.

So: **custom agent loop** (Python functions and tools) + **direct OpenAI and Anthropic clients**. CrewAI is present but not the main engine.

### Model providers / APIs

- **OpenAI**: GPT (e.g. gpt-3.5-turbo in `google_workflow`) for personalization, lead generation, copy, enrichment, campaign suggestions.
- **Anthropic**: Claude for knowledge extraction and some campaign/copy analysis.
- **Grok** (x.ai): `integrations/grok_service.py`; used for Phase 3 market intelligence; returns mock if `GROK_API_KEY` missing.

### Web, task queues, schedulers

- **FastAPI**: All backend entrypoints.
- **Uvicorn**: Run app (e.g. `backend/main_supabase:app`, port 8000).
- **APScheduler** (`AsyncIOScheduler`): In `main_supabase.py`; runs `sequence_execution_service.process_all_sequences` every 1 minute.
- **Celery**: Optional in `main.py` (Redis broker); not used in `main_supabase.py`.

### Databases and storage

- **Supabase (PostgreSQL)**: Primary for `main_supabase.py` and `backend_multi_tenant.py`. All tables (tenants, users, campaigns, leads, knowledge, sequences, enrollments, steps, executions, email blasts, etc.).
- **SQLite**: Used only by `main.py` (SQLAlchemy models: campaigns, leads, outreach_logs, user_google_accounts, user_knowledge).
- **Redis**: Optional in `main.py` for Celery; not required for Supabase backend.
- **File storage**: Uploaded training docs stored in paths (e.g. `uploads/training/`); content and metadata in Supabase. No vector DB.

---

## 5. Retrieval / RAG and data

- **RAG / vector search**: **Not implemented.**  
  - `agents/workflow.py` and `agents/google_workflow.py` import `RagTool` from `crewai_tools` but **never** instantiate or use it.  
  - There is no embedding pipeline, no vector store (no Chroma, Pinecone, Faiss, etc.), and no semantic retrieval in the codebase.  
  - `services/knowledge_service.py` and Supabase only do **structured** retrieval (e.g. by tenant, user, document type); no vector similarity.

- **Knowledge retrieval today**:  
  `KnowledgeService.get_user_knowledge()` loads from Supabase `user_knowledge` (and related) and aggregates by task type. Used by campaign intelligence and copywriting to build context for LLM calls. So: **document ingestion and structured retrieval exist; RAG is not implemented.**

---

## 6. Integrations

| Integration | Wired in code? | What it does | Partial / placeholder? |
|------------|----------------|--------------|-------------------------|
| **Google OAuth** | ✅ Yes | `integrations/google_oauth_service.py`: auth URL, token exchange, refresh. Used by backend for Gmail send, Sheets, Drive. Frontend: NextAuth Google provider. | No. |
| **Gmail** | ✅ Yes | Send email via user’s OAuth token (google_workflow GmailTool, sequence execution). | No. |
| **Google Sheets** | ✅ Yes | Create spreadsheet, add rows, update lead status (CoordinatorTool in google_workflow). List/preview/import from frontend. | No. |
| **Google Drive** | ✅ Yes | Read/write CSV in Drive (GoogleDriveTool in google_workflow). | No. |
| **SMTP/IMAP** | ✅ Yes | `integrations/email_service.py`: send via SMTP; IMAP for inbox (e.g. reply detection). Sequence execution can use SMTP when Gmail not used. | Reply detection in sequence_execution_service is TODO. |
| **LinkedIn** | Partial | `integrations/linkedin_service.py`: OAuth URL and token exchange; message sending stubbed. Backend comment: “LinkedIn sending not implemented yet”. | Yes — placeholder. |
| **Grok** | ✅ Yes | Phase 3 market intelligence; real API if `GROK_API_KEY` set, else mock. | Optional; mock when no key. |
| **CRM** | ❌ | No CRM (Salesforce, HubSpot, etc.) in repo. | — |

---

## 7. Limitations and missing pieces

### Not implemented or implied by names/TODOs

- **LinkedIn**: Sending not implemented; only OAuth and stubs.
- **Reply detection**: Sequence execution has a TODO: “Implement reply detection via Gmail API” (e.g. to auto-complete on reply).
- **CrewAI in production path**: Crew and RagTool unused in the main execution flow.
- **RAG**: No embeddings or vector retrieval.
- **JWT auth**: Backend uses a hardcoded demo user; `backend_multi_tenant.py` has “TODO: Implement proper JWT authentication”.
- **Google auth in multi-tenant backend**: `backend_multi_tenant.py` returns “Google authentication not implemented yet” for some flows.
- **Smart outreach “send”**: In `smart_outreach_agent`, “Send message (placeholder for actual sending)” and “placeholder implementation”.
- **Copywriter**: One Claude path is “placeholder - would need Anthropic client”.
- **Migration**: `migrate_to_supabase.py` says “Google account migration not implemented”.
- **Sequence process-queue**: Endpoint exists (`/sequences/process-queue`) but may be for manual trigger; main automation is the 1-min scheduler.

### Prototype vs production-ready

- **Production-ready in spirit**: Campaign/lead CRUD, Google OAuth, Gmail/Sheets/Drive, sequence execution with real sends, knowledge extraction and storage, campaign intelligence, email blast.  
- **Prototype / demo**: Auth (hardcoded demo user, placeholder JWT), LinkedIn, reply detection, some agent “send” paths still placeholders.  
- **Config**: Default `start.sh` runs SQLite backend; full Supabase + scheduler requires running `main_supabase.py` explicitly.

### Obvious bugs or incomplete flows

- **Backend entrypoint**: `start.sh` runs `main.py` (SQLite), not `main_supabase.py`; so the “sequence scheduler” and full Supabase API are not started by the default script.
- **Auth**: No real JWT validation; demo user is hardcoded; frontend and backend auth are not fully aligned for multi-tenant production.
- **One API route**: `frontend/pages/api/auth/google/disconnect.js` hardcodes `http://localhost:8000` instead of using `NEXT_PUBLIC_BACKEND_URL`.
- **Sequence execution**: If Gmail token is missing or expired, email steps can fail; error handling and retries are present but reply detection is missing.

---

## 8. How to demo it (for an interviewer / screen share)

### Goal

Show the app running with Supabase: sign in, create a campaign, add leads, run AI (e.g. Prospector or Copywriter), execute campaign with Google (if you have OAuth set up), or show sequences and knowledge.

### Prerequisites

- Python 3.8+ with venv; Node 16+.
- Supabase project: run `supabase_schema.sql` (and migrations like `phase3_sequence_execution.sql`, `add_email_blast_tracking.sql` if your schema doesn’t have them).
- `.env` in project root: at least `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`. For Google: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`.
- Frontend: copy `env.local.example` to `.env.local`, set `NEXTAUTH_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `NEXTAUTH_URL=http://localhost:3000`.

### Step 1: Backend (full Supabase API + scheduler)

```bash
cd /path/to/ai-sdr
source venv/bin/activate
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
# Optional: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
python backend/main_supabase.py
```

Expect: “Uvicorn running on http://0.0.0.0:8000”, “Sequence execution scheduler started”.

### Step 2: Frontend

```bash
cd frontend
npm install
npm run dev
```

Expect: “Ready on http://localhost:3000”.

### Step 3: Sign in

- Open http://localhost:3000.  
- Redirect to sign-in. Use **demo@example.com** / **password** (or Google if configured).  
- Redirect to dashboard.

### Step 4: Campaign and leads

- Go to Campaigns → Create campaign (name, description, etc.) → Save.  
- Open campaign → Add leads (manual or CSV upload with name, company, title, optional email).  
- Show campaign stats and lead list.

### Step 5: AI features (choose one or two)

- **Prospector**: From campaign or Prospector UI, “Generate leads” — show AI-generated (synthetic) leads; save to campaign.  
- **Copywriter**: “Personalize message” for a lead — show generated subject/body.  
- **Train your team**: Upload a PDF or doc → “Extract knowledge” → show extracted knowledge in Knowledge Bank or in campaign suggestions.  
- **Campaign intelligence**: Open dashboard or campaign intelligence — show “suggestions” based on knowledge (if any) and LLM.

### Step 6: Execute campaign (if Google OAuth is configured)

- Connect Google in the app (Settings or similar).  
- On campaign, run “Execute”.  
- Backend will: validate leads, generate personalized emails (OpenAI), send via Gmail, create a Google Sheet.  
- Show Sheet and/or inbox to confirm sends.

### Step 7: Sequences (optional)

- Create a sequence: add steps (e.g. email 1 → delay 2 days → email 2).  
- Assign to campaign or enroll leads; activate.  
- Wait for scheduler (1 min) or trigger step execution; show that email step was sent (and in `sequence_step_executions` if you show DB).

### Step 8: Email blast (optional)

- From campaign, “Generate blast email” (AI) then “Send blast”.  
- Show that recipients are tracked in DB and in UI if available.

### What to say

- “This is a multi-tenant AI SDR: campaigns, leads, AI personalization and copy, and sequence automation.”  
- “Execution uses the user’s Google account: real Gmail and Sheets.”  
- “Knowledge is extracted from uploads with Claude and used for suggestions and copy; no vector RAG yet.”  
- “Sequence engine runs on a 1-minute scheduler and sends real emails from Gmail.”  
- “LinkedIn and reply detection are not implemented; auth is still demo/placeholder for production.”

---

**Summary**: The repo implements a working AI SDR with Supabase, Google (Gmail/Sheets/Drive), Claude/OpenAI for knowledge and copy, and a sequence execution engine. The main flow is a custom tool chain in `google_workflow`, not CrewAI. RAG is not implemented; LinkedIn is stubbed. For a full demo, run `backend/main_supabase.py` and the frontend, and use the steps above.
