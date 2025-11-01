# Dynamic Pricing AI

A FastAPI backend with a lightweight static HTML/JS UI for chat-driven dynamic pricing workflows. The system supports authentication, per-user UI settings, threaded conversations with edit/branch/delete, streaming responses (SSE), rolling summarization, and cost/usage metadata capture from multiple LLM providers (OpenRouter, OpenAI, Gemini via OpenAI-compatible endpoint).

<p align="center">
  <img src="assets/0.png" width="500" alt=""/>
</p>

## Screenshots
The following screenshots highlight the main interface and key functionalities of the application.

<p align="center">
  <img src="assets/1.jpg" width="300" alt=""/>
  <img src="assets/2.jpg" width="300" alt=""/>
  <img src="assets/3.jpg" width="300" alt=""/>
  <img src="assets/4.jpg" width="300" alt=""/>
  <img src="assets/5.jpg" width="300" alt=""/>
  <img src="assets/6.jpg" width="300" alt=""/>
  <img src="assets/7.jpg" width="300" alt=""/>
  <img src="assets/8.jpg" width="300" alt=""/>
  <img src="assets/9.jpg" width="300" alt=""/>
  <img src="assets/10.jpg" width="300" alt=""/>
  <img src="assets/11.jpg" width="300" alt=""/>
  <img src="assets/12.jpg" width="300" alt=""/>
  <img src="assets/13.jpg" width="300" alt=""/>
  <img src="assets/14.jpg" width="300" alt=""/>
  <img src="assets/15.jpg" width="300" alt=""/>
  <img src="assets/16.jpg" width="300" alt=""/>
  <img src="assets/17.jpg" width="300" alt=""/>
  <img src="assets/18.jpg" width="300" alt=""/>
</p>


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

3) Build and run the application
- cd frontend && npm install && npm run build && cd ..
- uvicorn backend.main:app --reload --port 8000
- Open http://localhost:8000 for the application
- Or use run_full_app.bat for hot-reload development (backend + frontend dev server)

4) Optional: run tests
- Backend: pytest -q
- Frontend: cd frontend && npm test


## Architecture Overview

- Backend: FastAPI app at `backend/main.py`
  - Serves React frontend build from `frontend/dist` at root (`/`)
  - Provides REST endpoints for auth, settings, threads, messages, export/import
  - SSE endpoint for token-by-token streaming
  - Stores chat threads/messages/summaries in `data/chat.db` (SQLite)
- Frontend: React 18 + TypeScript SPA at `frontend/src`
  - Multi-page application with routing (Landing, Auth, Chat, Pricing, Contact)
  - Built with Vite, styled with Tailwind CSS + shadcn/ui components
  - State management via Zustand (8 stores)
  - Real-time chat with SSE streaming
- Core agents
- `core/agents/llm_client.py`: multi-provider LLM wrapper with fallbacks and streaming
- `core/agents/user_interact/user_interaction_agent.py`: orchestrates tool-calling or streaming responses and captures usage metadata
- Additional pricing/alerts/data collection agents and event bus under `core/agents/*`
- Data
  - `data/market.db`: sample market data used by tools/agents
  - `data/chat.db`: created on first run for chat persistence

### Agent System & Workflow

The chat experience is powered by five specialised agents that cooperate through an internal supervisor hub:

| Agent | Responsibilities |
| --- | --- |
| **Interaction Agent** | Parses natural language chat turns, gathers missing details (SKU, cost, competitor URLs), and calls downstream tools while streaming results back to the user. |
| **Supervisor Agent** | Normalises catalog updates, records competitor sources, coordinates the remaining agents, and returns a step-by-step activity log for transparency. |
| **Data Collection Agent** | Scrapes or simulates competitor price quotes for the registered product and stores them as market ticks/market\_data rows. |
| **Pricing Optimizer Agent** | Loads the latest catalog and market context, runs the LLM-assisted optimisation workflow, and writes the resulting price proposal with confidence and rationale. |
| **Alert Agent** | Evaluates margin gaps and market undercuts, emitting high-priority alerts that the Interaction Agent surfaces in the chat UI. |

From the chat UI (or directly via `UserInteractionAgent` tools), you can now:

1. **Add or update a product entirely through conversation** (`register_product`).
2. **Run the full end-to-end workflow in one shot** (`run_agent_workflow`) – registers the product, gathers market data, optimises pricing, and checks alerts.
3. **Trigger individual capabilities** such as collecting fresh competitor data or forcing a price optimisation with a custom goal.

The orchestration layer lives in `core/agents/user_interact/agent_hub.py`, which provides synchronous helpers so chat tool calls update SQLite state (`app/data.db`) without additional setup scripts.


## LLM Configuration

The chat backend supports any available OpenAI-compatible provider in this priority order:

1) OpenRouter (`OPENROUTER_API_KEY`, optional `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL`)
2) OpenAI (`OPENAI_API_KEY`, optional `OPENAI_MODEL`)
3) Gemini via Google’s OpenAI-compatible endpoint when `GEMINI_API_KEY` is set
   - Optional overrides: `GEMINI_MODEL` (default `gemini-2.0-flash`), `GEMINI_BASE_URL` (default `https://generativelanguage.googleapis.com/v1beta/openai/`)

If multiple providers are configured, the client falls back to the next one on error. If no providers are configured or available, the chat returns a clear non‑LLM fallback string.


## API Endpoints

- UI and Root
  - GET `/` → React frontend SPA (served from `frontend/dist`)
  - React Router handles client-side routing (/auth, /chat, /pricing, /contact)

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

The React frontend includes:
- Multi-page navigation: Landing, Auth, Chat, Pricing, Contact
- Sidebar: list threads, rename/delete; export/import threads
- Chat: copy/edit/delete/branch messages with SSE streaming
- Info: shows model tag, timestamps, cost/tokens/agents/tools when enabled
- Settings: toggles for model tag, timestamps, metadata panel, thinking, theme, streaming mode
- Auth modal: login/register/logout; per-user settings persist when a valid token is supplied
- Theme support: light/dark mode with smooth transitions
- Real-time notifications via toast system


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

- React Frontend: The project serves a React SPA via FastAPI. Build with `npm run build` in `frontend/` directory.
- Development: Use `run_full_app.bat` for concurrent backend + frontend dev servers with hot-reload.
- Missing keys: Without LLM keys, chat still works but returns a clear non‑LLM fallback response.
- SQLite files: `data/chat.db` is created automatically. Market data lives in `data/market.db`.
- Windows PowerShell beep: If sound notification fails, it is silently ignored.
- Ports/CORS: CORS allows local dev from any `localhost`/`127.0.0.1` port.


## Repository Structure

```
dynamic-pricing-ai-IRWA_PROJECT/
├── ai_commit/                        # Auto-commit CLI tooling for MCP workflows
│   ├── cli.py
│   ├── git_context.py
│   ├── prompt.py
│   ├── validator.py
│   ├── pyproject.toml
│   └── providers/
│       └── opencode.py
├── app/                              # Persisted chat threads and legacy sqlite snapshot
│   ├── chat_threads/
│   │   └── *.json
│   └── data.db.old
├── assets/                           # Marketing/product imagery (PNG/JPG)
├── backend/                          # FastAPI service layer
│   ├── main.py                       # ASGI app wiring routers/deps
│   ├── deps.py                       # Dependency injection helpers
│   ├── routers/                      # Endpoint routers (auth, prices, streaming, etc.)
│   │   ├── auth.py
│   │   ├── catalog.py
│   │   ├── messages.py
│   │   ├── streaming.py
│   │   └── threads.py
│   ├── tests/                        # API + workflow regression suites
│   │   ├── test_alerts_api.py
│   │   ├── test_catalog_api.py
│   │   ├── test_integration_workflow.py
│   │   └── ...
│   ├── test_auth_settings_api.py     # Additional top-level endpoint tests
│   ├── test_chat_api.py
│   └── __init__.py
├── core/                             # Cross-cutting business logic & agents
│   ├── agents/
│   │   ├── llm_client.py             # Multi-provider LLM orchestration
│   │   ├── supervisor.py             # Agent orchestration logic
│   │   ├── auto_applier.py
│   │   ├── auto_applier_db.py
│   │   ├── alert_service/            # Alerting agent components
│   │   │   ├── api.py
│   │   │   ├── engine.py
│   │   │   └── tools.py
│   │   ├── data_collector/           # Market data collection agent
│   │   │   ├── agent.py
│   │   │   ├── collector.py
│   │   │   ├── repo.py
│   │   │   └── connectors/web_scraper.py
│   │   ├── price_optimizer/          # Price optimization algorithms & tools
│   │   │   ├── agent.py
│   │   │   ├── algorithms.py
│   │   │   └── optimizer.py
│   │   ├── user_interact/            # User interaction agent bundle
│   │   │   ├── user_interaction_agent.py
│   │   │   ├── context.py
│   │   │   └── tools.py
│   │   └── pricing_optimizer_bus/
│   │       └── pricing_ui_integration.py
│   ├── evaluation/                   # Metrics & performance evaluation
│   │   ├── evaluation_engine.py
│   │   └── metrics.py
│   ├── events/                       # Event journal + schemas
│   │   ├── journal.py
│   │   └── schemas.py
│   ├── observability/                # Logging/telemetry plumbing
│   │   └── logging.py
│   ├── auth_service.py
│   ├── chat_db.py
│   ├── config.py
│   ├── tool_registry.py
│   └── workflow_templates.py
├── data/                             # SQLite backups and exported datasets
│   ├── auth.db.old
│   ├── market.db.old
│   └── ...
├── docs/                             # Documentation, reports, and archives
│   ├── archives/
│   ├── chat-context/
│   ├── planning/
│   ├── testing/
│   ├── system_architecture.mmd
│   └── VIVA_PREPARATION.md
├── frontend/                         # Vite + React + TypeScript web client
│   ├── src/
│   │   ├── components/               # Chat, landing, settings, UI atoms
│   │   ├── contexts/
│   │   ├── hooks/
│   │   ├── lib/                      # API client, utilities
│   │   ├── pages/
│   │   ├── stores/                   # Zustand stores
│   │   ├── utils/
│   │   ├── workers/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── styles.css
│   ├── e2e/                          # Playwright scenarios
│   ├── public/
│   ├── node_modules/
│   ├── package.json
│   ├── playwright.config.ts
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   ├── vitest.config.ts
│   ├── tsconfig.json
│   └── eslint.config.js
├── loadtests/
│   └── locustfile.py
├── scripts/                          # Automation, migrations, smoke tests
│   ├── debug/
│   ├── git/
│   ├── misc/
│   ├── run_autonomous_data_collector.py
│   ├── smoke_end_to_end.py
│   ├── sync_market_to_catalog.py
│   └── ...
├── tests/                            # System-level & LLM integration suites
│   ├── conftest.py
│   ├── test_llm_integration.py
│   ├── test_prices_endpoint.py
│   ├── test_workflow_templates_failures.py
│   └── ...
├── .env.example                      # Environment variable template
├── .gitignore
├── LICENSE
├── README.md
├── agent_tools.json
├── fix_catalog_patches.py
├── fix_prices_patches.py
├── fix_tests.py
├── launcher_config.ini
├── llm_agent_friendly_codebase_research.json
├── openapi.json
├── pytest.ini
├── requirements.txt
├── run_app.bat
├── run_full_app.bat
├── run_llm_tests.bat
├── test_price_optimizer_integration.py
├── test_title_generation.py
└── test_user_interaction_optimization.py
```

## Development

### Backend Development
- **Language**: Python 3.10+
- **Framework**: FastAPI with SQLAlchemy ORM
- **Dependencies**: See `requirements.txt`
- **Run**: `uvicorn backend.main:app --reload --port 8000`
- **Tests**: `pytest -q` or `pytest path/to/test_file.py`
- **Lint**: `black .`, `isort .`, `flake8 .`

### Frontend Development
- **Language**: TypeScript + React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State**: Zustand
- **Dependencies**: See `frontend/package.json`
- **Run**: `npm run dev` (from `frontend/`)
- **Build**: `npm run build`
- **Tests**: `npm run test` or `npm run test -- path/to/test.tsx`
- **Lint**: `npm run lint:fix` and `npm run format`

### Full App (Both Services)
Run `run_full_app.bat` on Windows or equivalent shell script on other platforms.

## Testing Credentials

For development & testing:
- Email: `demo@example.com`
- Password: `1234567890`

## Key Features

### Backend
- Multi-provider LLM support with automatic fallback (OpenRouter → OpenAI → Gemini)
- SSE streaming for real-time token output
- Thread-based conversation persistence
- User authentication with 7-day session tokens
- Cost tracking and usage analytics
- Modular agent architecture for catalog registration, data collection, pricing optimisation, alerts, and supervisory orchestration
- Chat-triggered product onboarding and price recommendation workflows via the Interaction Agent

### Frontend
- Real-time streaming chat with visual feedback
- Thread management (create, rename, delete, export/import)
- Message branching and editing
- Theme support (light/dark)
- Settings persistence per user
- Responsive design with Tailwind CSS


## License
This project is licensed under the MIT License
