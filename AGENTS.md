# Agent Instructions

Monorepo with Python/FastAPI backend and TypeScript/React frontend. Backend in `backend/`, frontend in `frontend/`.

## Backend (Python)

**Run:** using "C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT\run_full_app.bat"

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

- **ALWAYS EXPLAIN BEFORE ACTING**: Before executing any action, clearly state what you are going to do and explain the reasoning behind it. This includes file modifications, command executions, deletions, and any other operations.
- when you want to use chrome mcp tools do not attempt to run the backend and the frontend yourself just ask the user to run the full app and provide the necessary details
- No comments in code
- Try to achieve the desired functionality with minimum code
- Testing credentials: demo@example.com / 1234567890
-  Important : when you delete files move them to recycle bin do not permanently delete.
-  Commit frequently . do not push without instruction . commit super frequently . do local commits only
- i am new to git when you do something intermediate or advanced inform me what is happening
- If you made a change then tell me weather i have to restart to see the changes
- DO NOT MAKE ANY BRANCHES


## Feel free to do long horizon tasks

---

## Architecture Quick Reference

### Core Directories
- **`core/`**: Business logic, agent definitions, database models, event bus
- **`backend/routers/`**: FastAPI API endpoints with dependency injection
- **`scripts/`**: Database migrations, data population, smoke tests
- **`data/`**: SQLite databases (market.db, auth.db, chat.db) + events.jsonl

### Event-Driven Communication
Agents communicate via pub-sub event bus (`core/agents/agent_sdk/bus_factory.py`):
- **9 event topics**: MARKET_TICK, PRICE_PROPOSAL, PRICE_UPDATE, OPTIMIZATION_REQUEST, MARKET_FETCH_REQUEST, MARKET_FETCH_ACK, MARKET_FETCH_DONE, ALERT
- **Auto-logging**: All events → `data/events.jsonl` for debugging
- **Pattern**: Publish typed events (`await get_bus().publish(Topic.X.value, payload)`), subscribe in agent `start()` method
- **Rule**: Never block in event callbacks - offload heavy work to background threads

### MCP Integration
Dual-mode operation via `USE_MCP` env var:
- **`USE_MCP=true`**: Route tools through MCP servers (distributed)
- **`USE_MCP=false`**: Direct local function calls (dev/test)
- **Pattern**: Use factory functions like `get_price_optimizer_client()` - never hardcode MCP choice
- **Servers**: Data Collector MCP, Price Optimizer MCP

### LLM Orchestration
Multi-provider failover (OpenRouter → OpenAI → Gemini):
- **Autonomous agents**: System prompt defines workflow, LLM selects tools
- **Fallback**: Always implement deterministic heuristics for when LLM unavailable
- **Streaming**: Use `chat_with_tools_stream()` for real-time updates
- **Tool execution**: `core/agents/chat_executor.py` handles sync/async bridge

### Streaming (SSE)
Backend emits 7 event types to frontend:
1. `thinking` - Shows "Thinking..." indicator
2. `agent` - Active agent name for badge display
3. `tool_call` - Tool execution start/end
4. `message` - Text deltas or final message with token counts
5. `thread_renamed` - Auto-generated title
6. `done` - Stream completion
7. `error` - Error details

**Rule**: Always emit events in order, flush after each, always emit `done` or `error` to close stream

### Governance & Pricing
Two agents enforce business rules:
1. **AutoApplier** (`core/agents/auto_applier.py`):
   - Guardrails: `min_margin` (12%), `max_delta` (10%), `auto_apply` toggle
   - Optimistic concurrency with compare-and-swap
   - Logs all decisions to `decision_log` table
2. **GovernanceExecutionAgent** (`core/agents/governance_execution_agent.py`):
   - Decision states: RECEIVED, APPROVED, REJECTED, APPLIED_AUTO, APPLY_FAILED, STALE
   - WAL mode for concurrent reads during writes

**Rule**: Never write to `pricing_list` directly - always go through governance agents

### Market Data Collection
Request/response pattern (3 events):
1. Publish `MARKET_FETCH_REQUEST` with `request_id`, `sku`, `sources`, `urls`
2. Receive `MARKET_FETCH_ACK` with `job_id` and status
3. Receive `MARKET_FETCH_DONE` with `tick_count`

**Rule**: Always generate unique `request_id`, handle `FAILED` status gracefully

### Testing Strategy
- **Unit tests**: Mock `DataRepo`, monkeypatch env vars (`USE_MCP`, API keys)
- **Smoke tests**: Full workflows in `scripts/smoke_*.py`
- **LLM tests**: Test both enabled and fallback modes
- **Event tests**: Verify publish/subscribe, check `events.jsonl` output

---

## Common Tasks

### Add New Agent
1. Create agent class in `core/agents/`
2. Define system prompt with clear workflow steps
3. Implement fallback heuristics for LLM unavailability
4. Subscribe to events in `start()` method
5. Publish results via event bus
6. Add smoke test in `scripts/`

### Add New API Endpoint
1. Define route in `backend/routers/`
2. Use `Depends(get_current_user)` for auth, `Depends(get_repo)` for DB
3. Use Pydantic models for request/response validation
4. Run `python scripts/export_openapi.py` to update `openapi.json`
5. Test with mocked `DataRepo`

### Add Frontend Feature
1. Add Zustand store if new global state needed (`src/store/`)
2. Create React Query hook for API calls (`src/hooks/`)
3. Build UI with Tailwind CSS + components from `components/ui/`
4. Data flow: API → React Query → Zustand → Components

### Debug Issues
- **Events**: Check `data/events.jsonl` for event history
- **LLM**: Check `self.last_usage` in LLMClient for token counts/costs
- **Database**: Use `scripts/debug/` tools
- **Streaming**: Monitor browser Network tab for SSE events

### Reset Demo Environment
```bash
python scripts/init_db.py
python scripts/create_sample_catalog.py
python scripts/insert_mock_market_data.py
```

---

## Key Resources
- **Full architecture details**: `suggestions_for_agents.md`
- **API spec**: `openapi.json`
- **Event journal**: `data/events.jsonl`
- **Agent tool manifest**: `agent_tools.json`
