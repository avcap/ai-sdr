# AI SDR

A multi-tenant AI-powered Sales Development Representative platform for B2B outbound prospecting, personalized outreach, and campaign execution. The system uses a CrewAI multi-agent workflow for campaign execution and supports email sequences, knowledge extraction from documents, and integrations with Gmail and Google Sheets.

## Features

- **CrewAI workflow**: Four-agent crew (Prospector, Personalization, Outreach, Coordinator) runs on campaign execute. The crew validates leads, generates personalized copy, and coordinates the pipeline via sequential tasks.
- **Campaign and lead management**: Create campaigns, add or upload leads (CSV), and track status through the UI and API.
- **Specialized agents**: Prospector (lead generation), Enrichment (validation and scoring), Copywriter (message personalization), and Smart Campaign Orchestrator (prompt to campaign with quality gates).
- **Email sequences**: Multi-step sequences (email, delay, condition, action) with enrollment and scheduled execution. Steps run on an interval; email steps send via Gmail or SMTP.
- **Knowledge base**: Upload company or sales documents; the system extracts structured knowledge with Claude and uses it for campaign suggestions and copy context.
- **Integrations**: Google OAuth (Gmail, Sheets, Drive), SMTP/IMAP. Optional Grok for market intelligence.

## Tech stack

- **Backend**: FastAPI, Supabase (PostgreSQL), APScheduler for sequence execution
- **Frontend**: Next.js 14, NextAuth (credentials and Google)
- **AI**: CrewAI, OpenAI, Anthropic (Claude)

## Prerequisites

- Python 3.8+
- Node.js 16+
- A Supabase project (schema in `supabase_schema.sql`; run migrations as needed)

## Setup

1. Clone the repository and create a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy environment configuration and set variables:

   ```
   cp env.example .env
   ```

   Required for the Supabase backend: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`. For AI features: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`. For Google (Gmail, Sheets): `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`. See `env.example` for the full list.

3. Frontend:

   ```
   cd frontend
   npm install
   cp env.local.example .env.local
   ```

   Set `NEXTAUTH_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `NEXTAUTH_URL` (e.g. `http://localhost:3000`) in `.env.local`.

## Running the application

**Backend (Supabase, full API and sequence scheduler):**

```
python backend/main_supabase.py
```

Serves at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

**Frontend:**

```
cd frontend && npm run dev
```

Serves at `http://localhost:3000`. Set `NEXT_PUBLIC_BACKEND_URL` to `http://localhost:8000` if the backend runs elsewhere.

Sign in with the configured credentials or Google OAuth. Create a campaign, add leads, and use Execute to run the CrewAI workflow. Sequences, knowledge extraction, and other features are available from the dashboard and campaign pages.

## Repository structure

- `agents/` – CrewAI workflow (`workflow.py`), Google-integrated pipeline (`google_workflow.py`), and specialized agents (Prospector, Copywriter, Enrichment, etc.)
- `backend/` – FastAPI app (`main_supabase.py` for Supabase; `main.py` for SQLite)
- `frontend/` – Next.js app and API routes
- `integrations/` – Email, Google OAuth, Google Sheets, LinkedIn (stubs), Grok
- `services/` – Supabase, knowledge, sequence execution, campaign intelligence

For a detailed analysis of what is implemented and how the system works, see `REPO_ANALYSIS.md`.
