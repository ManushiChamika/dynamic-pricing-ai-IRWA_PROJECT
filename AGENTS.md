# Agent Instructions

Monorepo with Python/FastAPI backend and TypeScript/React frontend. Backend in `backend/`, frontend in `frontend/`.

## Backend (Python)

**Run:** "C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT\run_full_app.bat"
**Test:** `pytest` (all), `pytest path/to/test_file.py` (single)
**Lint:** `black .`, `isort .`, `flake8 .` before committing
**Style:** snake_case functions/vars, PascalCase classes; fully typed (mypy strict); use `HTTPException` in API endpoints

## Frontend (TypeScript/React)

**Run:** "C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT\run_full_app.bat"
**Build:** `npm run build`
**Test:** `npm run test` (all), `npm run test -- path/to/test_file.tsx` (single)
**Lint/Format:** `npm run lint:fix`, `npm run format` before committing
**Style:** camelCase functions/vars, PascalCase components/types; Tailwind CSS only; strong TypeScript typing

## Important

- **ALWAYS EXPLAIN BEFORE ACTING**: State intent and reasoning before any file modification, command, or deletion.
- Ask user to run full app when chrome MCP tools needed; do not self-start services for that.
- No comments in code.
- Minimize handwritten code; prefer mature libraries with thin wrappers.
- Testing credentials: demo@example.com / 1234567890
- Move deleted files to recycle bin (do not permanently delete).
- Commit locally frequently (no pushes unless instructed). Explain intermediate/advanced git actions.
- Inform if restart required for a change to take effect.
- DO NOT CREATE BRANCHES.

## Current Modernization Status (Migration Plan Alignment)

Planned/ongoing migrations to reduce custom LOC:
- Config: Migrating to `pydantic-settings` (`core/settings.py` planned) replacing `os.getenv` usage.
- LLM: Adopting LangChain via thin wrapper `LangChainLLMClient` maintaining failover, streaming, tool calling, cost tracking.
- Event Bus: Transitioning to Blinker signals (Redis future option) with async task scheduling.
- Auth: Parallel rollout of `fastapi-users` (session/cookie transport) before removing legacy auth.
- Database CRUD: Introducing FastCRUD-style repositories with optimistic locking extensions.
- SSE Client: Replacing custom client with `react-eventsource` (auth headers supported).
- Frontend Forms: Migrating to React Hook Form + Zod for validation.
- Global State: Using Zustand for auth/session and cross-component state.
- Server State: Standardizing API access with Axios + TanStack Query (caching, mutations, optimistic updates).
- Type Generation: Using `@hey-api/openapi-ts` to generate TS types and query hooks from `openapi.json`.
- Testing Backend: Converting to async tests with `httpx.AsyncClient` + `pytest-asyncio`.
- Testing Frontend: Using Vitest + React Testing Library for components/hooks.
- Observability: Adding OpenTelemetry tracing + Prometheus metrics (API, event bus, LLM calls).

## Anti-Corruption Layer Wrappers
Use thin wrappers to isolate external libraries:
- Config: `get_settings()`
- LLM: `LangChainLLMClient` (maintains legacy method signatures)
- Event Bus: `EventBus` abstraction over Blinker (future Redis)
- Repositories: `BaseRepo` customizing CRUD + locking
- SSE: `useChatStream()` encapsulates streaming client

## Rollback Strategy (General)
Maintain legacy implementation until new path validated; use feature flags or conditional imports; revert quickly on anomalies while capturing metrics.

---

## Architecture Quick Reference

### Core Directories
- **`core/`**: Business logic, agent definitions, database models, event bus
- **`backend/routers/`**: FastAPI API endpoints with dependency injection
- **`scripts/`**: Database migrations, data population, smoke tests
- **`data/`**: SQLite databases (market.db, auth.db, chat.db) + events.jsonl

### Event-Driven Communication
(Currently migrating from custom bus to Blinker)
- 9 topics: MARKET_TICK, PRICE_PROPOSAL, PRICE_UPDATE, OPTIMIZATION_REQUEST, MARKET_FETCH_REQUEST, MARKET_FETCH_ACK, MARKET_FETCH_DONE, ALERT
- Logging: events appended to `data/events.jsonl`
- Async handlers scheduled via `asyncio.create_task` (avoid blocking)

### MCP Integration
- Controlled by `USE_MCP`; use factory functions (e.g., `get_price_optimizer_client()`) to avoid hardcoding.

### LLM Orchestration
- Legacy multi-provider failover (OpenRouter → OpenAI → Gemini) migrating to LangChain wrapper preserving streaming + tool calling.
- Deterministic fallbacks required when LLM unavailable.
- Streaming path emits SSE events (`thinking`, `message`, `done`, `error`).

### Streaming (SSE)
- 7 event types: thinking, agent, tool_call, message, thread_renamed, done, error.
- Client migration to `react-eventsource` with proper auth header handling.

### Governance & Pricing
- **AutoApplier**: guardrails (min_margin 12%, max_delta 10%), CAS updates, decision logging.
- **GovernanceExecutionAgent**: state transitions (RECEIVED → APPROVED/REJECTED etc.). Do not write directly to `pricing_list`.

### Market Data Collection
- 3-event pattern (REQUEST, ACK, DONE). Unique `request_id` required. Handle FAILED gracefully.

### Testing Strategy (Evolving)
- Backend: shift to async tests; mock LLM providers and DataRepo.
- Smoke: `scripts/smoke_*.py` for end-to-end validation.
- Frontend: Vitest for components/hooks; MSW optional for API mocking.
- Event bus tests verify delivery + error isolation.

---

## Common Tasks

### Add New Agent
1. Create agent class in `core/agents/`
2. Define system prompt/workflow steps
3. Use LangChain wrapper for LLM operations
4. Subscribe to signals/event topics in `start()`
5. Publish results through EventBus abstraction
6. Add smoke test in `scripts/`

### Add New API Endpoint
1. Define route in `backend/routers/`
2. Apply `Depends(get_current_user)` and repository dependency
3. Use Pydantic models
4. Run `python scripts/export_openapi.py` (then regenerate TS types)
5. Test with mocked repositories

### Add Frontend Feature
1. Add/extend Zustand store if global state needed
2. Use Axios + TanStack Query hook for API access
3. Build UI with Tailwind + shared components
4. SSE-driven updates via `useChatStream()` when streaming needed

### Debug Issues
- Events: inspect `data/events.jsonl`
- LLM: check usage metrics in wrapper (tokens/cost)
- Database: use scripts in `scripts/debug/`
- Streaming: browser Network tab SSE inspection
- Tracing: review OpenTelemetry spans (once active)

### Reset Demo Environment
```bash
python scripts/init_db.py
python scripts/create_sample_catalog.py
python scripts/insert_mock_market_data.py
```

---

## Key Resources
- Architecture deep dive: `suggestions_for_agents.md`
- API spec: `openapi.json`
- Event journal: `data/events.jsonl`
- Tool manifest: `agent_tools.json`
- Migration plan: `docs/LIBRARY_MIGRATION_PLAN.md`
