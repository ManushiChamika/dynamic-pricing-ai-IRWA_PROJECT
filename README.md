# Dynamic Pricing AI (IRWA Project)

A FastAPI backend with a lightweight static HTML/JS UI for chat-driven dynamic pricing workflows. The system supports authentication, per-user UI settings, threaded conversations with edit/branch/delete, streaming responses (SSE), rolling summarization, and cost/usage metadata capture from multiple LLM providers (OpenRouter, OpenAI, Gemini via OpenAI-compatible endpoint).


## Quickstart

### Option 1: Easy Start (Windows)
**Double-click `run_app.bat`** in the project root folder. This will:
- Check Python installation
- Install dependencies if needed  
- Find an available port (8000, 8001, or 8002)
- Start the server and show you the URL to open

### Option 2: Manual Setup
1) Create and fill in your `.env` based on `.env.example`
- Copy `.env.example` to `.env` and add any provider keys you have.
- If you have no keys, the UI still works with a non‑LLM fallback response.

2) Install dependencies
- Python 3.10+
- pip install -r requirements.txt

3) Run the API server
- uvicorn backend.main:app --reload --port 8000
- Open http://localhost:8000/ui/index.html for the chat UI

4) Optional: run tests
- pytest -q


## Architecture Overview

- Backend: FastAPI app at `backend/main.py`
  - Serves static UI from `backend/ui` under `/ui`
  - Provides REST endpoints for auth, settings, threads, messages, export/import
  - SSE endpoint for token-by-token streaming
  - Stores chat threads/messages/summaries in `data/chat.db` (SQLite)
- Core agents
  - `core/agents/llm_client.py`: multi-provider LLM wrapper with fallbacks and streaming
  - `core/agents/user_interact/user_interaction_agent.py`: orchestrates tool-calling or streaming responses and captures usage metadata
  - Additional pricing/alerts/data collection agents and event bus under `core/agents/*`
- Data
  - `data/market.db`: sample market data used by tools/agents
  - `data/chat.db`: created on first run for chat persistence


## LLM Configuration

The chat backend supports any available OpenAI-compatible provider in this priority order:

1) OpenRouter (`OPENROUTER_API_KEY`, optional `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL`)
2) OpenAI (`OPENAI_API_KEY`, optional `OPENAI_MODEL`)
3) Gemini via Google’s OpenAI-compatible endpoint when `GEMINI_API_KEY` is set
   - Optional overrides: `GEMINI_MODEL` (default `gemini-2.0-flash`), `GEMINI_BASE_URL` (default `https://generativelanguage.googleapis.com/v1beta/openai/`)

If multiple providers are configured, the client falls back to the next one on error. If no providers are configured or available, the chat returns a clear non‑LLM fallback string.


## API Endpoints

- UI and Root
  - GET `/` → static landing (opens UI when available)
  - Static UI at `/ui` (served from `backend/ui`)

- Auth
  - POST `/api/register` { email, password, username? } → { ok, token, user, expires_at }
  - POST `/api/login` { email, password } → { ok, token, user, expires_at }
  - GET  `/api/me` ?token=… → { ok, user } (401 if invalid)
  - POST `/api/logout` { token? } → { ok } (also clears `fp_session` cookie when present)

- Per-user Settings (in-memory, keyed by session token)
  - GET `/api/settings` ?token=… → { ok, settings }
  - PUT `/api/settings` { token, settings } → { ok, settings }

- Threads & Messages
  - POST `/api/threads` { title? } → ThreadOut
  - GET  `/api/threads` → List[ThreadOut]
  - PATCH `/api/threads/{thread_id}` { title } → ThreadOut
  - DELETE `/api/threads/{thread_id}` → { ok }
  - GET  `/api/threads/{thread_id}/messages` → List[MessageOut]
  - POST `/api/threads/{thread_id}/messages` { user_name, content, parent_id? } → MessageOut (non-streaming)
  - POST `/api/threads/{thread_id}/messages/stream` { user_name, content, parent_id? } → SSE stream:
    - events: `thinking?`, `message` (deltas and final payload), `done`, `error`

- Message operations
  - PATCH `/api/messages/{message_id}` { content, branch?=true } → MessageOut (edit user message)
  - DELETE `/api/messages/{message_id}` → { ok }

- Export / Import / Summaries
  - GET  `/api/threads/{thread_id}/export` → { thread, messages }
  - POST `/api/threads/import` { title?, owner_id?, messages[] } → ThreadOut
  - GET  `/api/threads/{thread_id}/summaries` → { ok, summaries }


## UI Features

- Sidebar: list threads, rename/delete; export/import threads
- Chat: copy/edit/delete/branch messages
- Streaming: live tokens via SSE with optional “Thinking…” pre-event and Stop in the client
- Info: shows model tag, timestamps, cost/tokens/agents/tools when enabled
- Settings: toggles for model tag, timestamps, metadata panel, thinking, theme, streaming mode (sse), and mode (user/developer)
- Auth modal: login/register/logout; per-user settings persist when a valid token is supplied


## Environment Flags

Environment flags are read by the backend and agents to control behavior. See `.env.example` for all options. Key flags:

- DEV_MODE: Enables defaults for `show_timestamps`, `show_metadata_panel`, `show_thinking` in UI settings
- UI_LLM_MAX_TOKENS: Upper bound for tokens requested by UI turns (default 1024 if unset/0)
- LLM_PRICE_MAP: JSON object mapping per‑1K token prices for cost estimates. Keys can be `provider:model` or model only
- DEBUG_LLM: Enables verbose logging inside the LLM client
- SOUND_NOTIFICATIONS: Enables a short completion beep on supported platforms

Context assembly and summarization controls:
- UI_HISTORY_MAX_MSGS: Max recent messages included when there is no summary (default 24)
- UI_HISTORY_TAIL_AFTER_SUMMARY: Tail size after latest summary (default 12)
- UI_SUMMARIZE_AFTER_MSGS: Summarize after at least this many since last summary (default 12)
- UI_LONG_THREAD_MSGS: Treat as “long thread” above this many total messages (default 20)
- UI_SUMMARIZE_TOKEN_TRIGGER: Summarize when prompt+completion tokens exceed threshold (default 2000)
- UI_SUMMARIZE_PROB: Probability to summarize on long threads when other triggers don’t fire (default 0.25)

Advanced / integration flags:
- UI_REQUIRE_LOGIN: Reserved; not currently enforcing UI gating in `/` or `/ui`
- USE_MCP, MCP_*: For MCP/stdio integration paths used by agents; not required for basic chat
- SUMMARIZER_MODEL: Override model used for rolling summaries; falls back to default when unset


## Cost & Usage Metadata

Each assistant message may include:
- model: last model used
- token_in, token_out: prompt and completion token counts (when provided by SDK)
- cost_usd: estimated cost using `LLM_PRICE_MAP`
- api_calls: LLM + tool calls count for the turn
- agents/tools: derived metadata inferred from the tool-calling loop
- metadata: provider and tools_used details

These are displayed in the UI when the metadata panel is enabled.


## Notes & Troubleshooting

- No Streamlit: The project serves a static UI via FastAPI. Open `/ui` in your browser.
- Missing keys: Without LLM keys, chat still works but returns a clear non‑LLM fallback response.
- SQLite files: `data/chat.db` is created automatically. Market data lives in `data/market.db`.
- Windows PowerShell beep: If sound notification fails, it is silently ignored.
- Ports/CORS: CORS allows local dev from any `localhost`/`127.0.0.1` port.


## License

This repository does not include an explicit license file. Treat as proprietary unless a license is added.
