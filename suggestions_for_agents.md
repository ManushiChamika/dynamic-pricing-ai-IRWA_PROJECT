# Suggestions for Improving AGENTS.md

This document provides a more detailed set of instructions and context for an AI agent working within this repository. The goal is to supplement the existing `AGENTS.md` with deeper insights into the project's architecture, tooling, and workflows, enabling the agent to perform tasks more efficiently, accurately, and safely.

## Table of Contents
1.  [Expanded Project Architecture](#1-expanded-project-architecture)
2.  [Environment & Configuration](#2-environment--configuration)
3.  [Database Interaction](#3-database-interaction)
4.  [API Specification](#4-api-specification)
5.  [Key Dependencies & Technologies](#5-key-dependencies--technologies)
6.  [Important Scripts & Automation](#6-important-scripts--automation)
7.  [Git Workflow & Commit Style](#7-git-workflow--commit-style)
8.  [Security Best Practices](#8-security-best-practices)
9.  [Agent Persona & Communication](#9-agent-persona--communication)

---

### 1. Expanded Project Architecture

While the monorepo is split into `frontend/` and `backend/`, other directories are critical.

-   **`core/`**: This is a vital Python package containing the primary business logic, including agent definitions, database models, and core services. Before modifying backend behavior, always inspect this directory to understand the underlying architecture.
-   **`scripts/`**: Contains numerous Python scripts for database migrations, data population, testing, and automation. It is a valuable resource for understanding and performing common administrative tasks.
-   **`data/`**: This directory appears to be the storage location for SQLite database files (e.g., `market.db`, `auth.db`). The agent must be aware that the application state is stored here.
-   **`openapi.json`**: A machine-readable specification of the FastAPI backend's API. This is the source of truth for all API endpoints, their parameters, and response structures.

**Suggestion:** The agent should always begin backend-related tasks by examining the contents of `core/` and `backend/routers/` to understand the application's logic and API structure.

---

### 2. Environment & Configuration

The project uses a `.env` file for configuration, based on the `.env.example` template.

-   **Setup:** The agent should be instructed to always check `.env.example` to understand required environment variables for features like LLM API keys, database connections, and feature flags.
-   **Feature Flags:** The `.env` file contains important flags like `DEV_MODE`, `USE_MCP`, and `UI_REQUIRE_LOGIN`. The agent should be capable of modifying these flags for debugging or testing purposes, and should inform the user when a change is made.

**Suggestion:** Before running the application or any script that might rely on external services, the agent should verify that a `.env` file exists and contains the necessary variables by first reading `.env.example`.

---

### 3. Database Interaction

The application uses SQLite databases, managed via SQLAlchemy.

-   **ORM:** All database interactions in the Python backend are handled by the SQLAlchemy ORM. The agent should prefer using the defined models (likely in `core/` or `backend/`) rather than writing raw SQL queries.
-   **Initialization:** The script `scripts/init_db.py` is critical for setting up the database schema. If the database state is corrupted or needs to be reset, this script is the correct tool to use.
-   **Migrations & Data Population:** The `scripts/` directory contains many scripts for migrating (`migrate_*.py`) and populating (`populate_*.py`, `create_sample_catalog.py`) the database. The agent should use these scripts to manage data rather than making manual changes.

**Suggestion:** For any task involving database schema changes or data manipulation, the agent should first look for an existing script in the `scripts/` directory. If none exists, it should create a new script to perform the operation, ensuring reproducibility.

---

### 4. API Specification

The `openapi.json` file provides a complete contract for the backend API.

-   **Reference:** When performing frontend tasks that involve API calls, the agent should first consult `openapi.json` to understand the exact endpoint, expected request payload, and response structure. This will reduce errors and increase accuracy.
-   **Maintenance:** The `scripts/export_openapi.py` script is likely used to generate the `openapi.json` file. After adding or modifying an API endpoint in the FastAPI application, this script should be run to keep the specification up-to-date.

**Suggestion:** The agent should be taught to use `openapi.json` as its primary reference for all API-related work. When backend API changes are made, the agent should automatically run the export script and commit the updated `openapi.json`.

---

### 5. Key Dependencies & Technologies

A brief overview of the main technologies used:

**Backend (Python):**
-   **Framework:** FastAPI
-   **Database:** SQLAlchemy (for SQLite)
-   **AI/ML:** `transformers`, `torch`, `langchain`, `openai`
-   **Testing:** `pytest`, `hypothesis`

**Frontend (TypeScript/React):**
-   **Framework:** React with Vite
-   **Styling:** Tailwind CSS, Radix UI (for headless components)
-   **State Management:** Zustand
-   **Data Fetching:** TanStack React Query
-   **Testing:** Vitest, Playwright (for E2E)

**Suggestion:** The agent should leverage the features of these libraries. For example, when adding a new API call in the frontend, it should use React Query for caching and state management. When writing backend code, it should adhere to FastAPI's dependency injection pattern.

---

### 6. Important Scripts & Automation

The `scripts/` directory is a toolbox. The agent should be aware of and use these scripts.

-   **Database Setup:** `init_db.py`
-   **Sample Data:** `create_sample_catalog.py`, `insert_mock_market_data.py`
-   **Data Sync/Migration:** `sync_market_to_catalog.py`, various `migrate_*.py` scripts
-   **Smoke Tests:** `smoke_*.py` scripts provide a way to run quick end-to-end checks for different parts of the system.

**Suggestion:** Create a workflow where the agent can be asked to "reset and populate the demo environment," which would chain commands like `python scripts/init_db.py` and `python scripts/create_sample_catalog.py`.

---

### 7. Git Workflow & Commit Style

The current instructions are minimal. They can be improved for better clarity and history management.

-   **Commit Message Convention:** While the user requested no branches, adopting a structured commit message format (like Conventional Commits) would greatly improve the readability of the git log.
    -   Example: `feat(backend): add new endpoint for user profiles`
    -   Example: `fix(frontend): correct button alignment on login page`
    -   Example: `docs(readme): update setup instructions`
-   **Explanation:** The agent should continue to explain intermediate/advanced git actions, but it should frame them in the context of this convention.

**Suggestion:** Propose to the user the adoption of the Conventional Commits standard. The agent can then be instructed to always format its commit messages accordingly, making the project history much more valuable.

---

### 8. Security Best Practices

Security is not mentioned in the current guide but is crucial.

-   **Secrets:** The agent must be reminded to never commit secrets or sensitive information. It should check for the presence of secrets in the `.env` file and ensure `*.env` is in `.gitignore`.
-   **Dependency Scanning:** The agent should be able to run security audits on dependencies.
    -   **Frontend:** `npm audit`
    -   **Backend:** `pip-audit` or a similar tool should be installed and used.
-   **Input Validation:** When adding new API endpoints, the agent must use Pydantic models for strict input validation to prevent common injection vulnerabilities.

**Suggestion:** Add a pre-commit hook that runs a security check (e.g., for secrets) and dependency audit, and instruct the agent on how to interpret and fix any reported issues.

---

### 10. Deep Dive: Backend Architecture & Conventions

Based on a detailed analysis of `core/`, `backend/`, and `tests/`, the following conventions should be strictly followed.

-   **Supervisor as an Orchestrator (`core/agents/supervisor.py`):**
    -   The `Supervisor` class is the high-level entry point for complex, multi-step business processes (e.g., "run pricing for a catalog"). It does not contain business logic itself but rather orchestrates calls to other services and tools.
    -   **When to use:** For tasks that involve a sequence of operations like data collection, optimization, and publishing, the agent should look to the `Supervisor` for the established pattern.
    -   **How to modify:** When adding a new step to a workflow, first add it as a tool in the `tool_registry`, then integrate it into the `Supervisor`'s orchestration logic. Avoid adding raw business logic directly to the `Supervisor`.

-   **Tool-Based Architecture (`core/tool_registry.py`):**
    -   The backend heavily relies on a tool registry to expose discrete functionalities (e.g., `upsert_product`, `start_data_collection`). This is a form of the Command pattern and is central to the system's design.
    -   **When to use:** Any new, self-contained piece of business logic should be exposed as a tool and registered in the `tool_registry`.
    -   **Example:** To add a feature for "calculating shipping costs," the agent should create a `calculate_shipping_cost` function, register it as a tool, and then call it via `tool_registry.execute_tool("calculate_shipping_cost", ...)`.

-   **Dependency Injection in FastAPI (`backend/routers/`):**
    -   API endpoints use FastAPI's `Depends` system to manage dependencies like the current user (`get_current_user`) and database repositories (`get_repo`).
    -   **How to modify:** When creating a new endpoint that requires database access or authentication, the agent must add the appropriate `Depends` parameter to the function signature. It should never instantiate dependencies like `DataRepo` directly within an endpoint function.

-   **Testing with Mocks (`backend/tests/`):**
    -   Backend tests effectively use `unittest.mock.patch` to isolate components and mock external dependencies, particularly the `DataRepo`.
    -   **How to test:** When writing tests for a new API endpoint, the agent should follow the pattern in `test_catalog_api.py`:
        1.  Use `monkeypatch` to set environment variables.
        2.  Create a `TestClient`.
        3.  Use `patch("path.to.dependency")` to mock the repository or other services.
        4.  Configure the mock's return values or side effects.
        5.  Make the request using the `client`.
        6.  Assert the response and that the mock was called correctly.

---

### 11. Deep Dive: Frontend Architecture & Conventions

Analysis of the `frontend/` directory, especially `src/`, reveals a modern, well-structured React application.

-   **State Management with Zustand:**
    -   The application uses Zustand for global state management. State is organized into "stores" (e.g., `messageStore`, `threadStore`, `settingsStore`).
    -   **How to modify:** To add new global state, the agent should either add a new property to an existing store or, if the state is sufficiently different, create a new store file following the existing pattern. State should always be modified by calling the action functions defined in the store (e.g., `useMessagesActions().refresh()`).

-   **Component Structure:**
    -   Components are organized by feature (`chat/`, `settings/`) or purpose (`ui/`).
    -   **Styling:** Tailwind CSS is used exclusively for styling. The agent should not write custom CSS files. UI components from `components/ui/` (built on Radix UI) should be reused whenever possible.
    -   **Data Fetching:** While not explicitly seen in the `ChatPane`, the presence of TanStack React Query implies that API calls should be wrapped in custom hooks (e.g., `useProducts`) that use `useQuery` or `useMutation`. This handles caching, refetching, and loading/error states automatically.

-   **Custom Hooks for Logic (`hooks/`):**
    -   Complex logic and side effects are encapsulated in custom hooks (e.g., `useChatKeyboardShortcuts`).
    -   **How to modify:** When adding new complex client-side logic, especially logic that needs to be shared between components, the agent should create a new custom hook in the `hooks/` directory.

**Golden Rule for Frontend:** Data flows from API -> React Query hooks -> Zustand stores -> React components. The agent should always follow this pattern to ensure consistency and maintainability.

---

### 12. Event-Driven Agent Communication Architecture

The system uses a sophisticated pub-sub event bus for **loosely-coupled agent communication**. This architecture enables autonomous, reactive workflows.

**Core Event Bus (`core/agents/agent_sdk/bus_factory.py`):**
- **9 predefined event topics** defined in `core/agents/agent_sdk/protocol.py` (Topic enum):
  - `MARKET_TICK`: Real-time market data events
  - `PRICE_PROPOSAL`: Pricing suggestions from optimizer
  - `PRICE_UPDATE`: Confirmed price changes
  - `OPTIMIZATION_REQUEST`: Trigger for pricing workflows
  - `MARKET_FETCH_REQUEST`: Request for data collection
  - `MARKET_FETCH_ACK`: Acknowledgment of data collection
  - `MARKET_FETCH_DONE`: Completion of data collection
  - `ALERT`: System alerts and notifications
  - Additional topics for workflow orchestration

**Event Validation & Journaling (`core/events/`):**
- All events validated against Pydantic schemas in `core/events/schemas.py`
- **Automatic event journaling** to `data/events.jsonl` for audit trail and debugging
- Best-effort delivery pattern: publish never blocks, failures are logged

**Agent Communication Patterns:**

1. **Data Collector → Pricing Optimizer** (`core/agents/data_collector/collector.py:35-62`):
   ```python
   # DataCollector publishes typed MarketTick events
   tick = MarketTick(sku=..., our_price=..., competitor_price=...)
   await get_bus().publish(Topic.MARKET_TICK.value, tick)
   ```

2. **Pricing Optimizer → Governance Agent** (`core/agents/price_optimizer/agent.py:590-600`):
   ```python
   # PricingOptimizerAgent publishes proposals
   proposal = {
       "proposal_id": uuid.uuid4().hex,
       "product_id": sku,
       "previous_price": float(our_price),
       "proposed_price": float(new_price)
   }
   await bus.publish(Topic.PRICE_PROPOSAL.value, proposal)
   ```

3. **Governance Agent → System** (`core/agents/governance_execution_agent.py:226-231`):
   ```python
   # GovernanceExecutionAgent publishes after applying prices
   upd = {"proposal_id": ..., "product_id": ..., "final_price": ...}
   await get_bus().publish(Topic.PRICE_UPDATE.value, upd)
   ```

**How Agents Subscribe:**
```python
# Agent initialization pattern (see auto_applier.py:36-48)
async def start(self):
    async def on_proposal(pp: PriceProposal):
        self._handle_proposal_nonblocking(pp)
    
    get_bus().subscribe(Topic.PRICE_PROPOSAL.value, on_proposal)
```

**Agent Instructions:**
- When adding new agent workflows, **always use the event bus** for inter-agent communication
- Define new event topics in `protocol.py` if needed
- Use typed dataclasses for events (see `events_models.py`) to ensure schema validation
- Never block the event callback - offload heavy work to background threads (see `auto_applier.py:140-141`)
- Events are logged to `data/events.jsonl` automatically - use this for debugging

---

### 13. MCP (Model Context Protocol) Integration

The system implements an **MCP abstraction layer** for agent tools, enabling dual-mode operation: direct function calls OR MCP server communication.

**MCP Infrastructure:**

1. **Connection Pooling & Resilience** (`core/agents/agent_sdk/mcp_client.py`):
   - Automatic connection pooling per MCP server
   - Exponential backoff retry strategy (3 attempts with 0.5s, 1s, 2s delays)
   - Health checks and automatic reconnection
   - Timeout handling (30s default)

2. **Dual-Mode Toggle** (via `USE_MCP` env var in `.env`):
   - `USE_MCP=true`: Route tool calls through MCP servers (for distributed deployments)
   - `USE_MCP=false` or unset: Direct local function calls (for development/testing)

3. **Two MCP Servers:**
   - **Data Collector MCP** (`core/agents/data_collector/mcp_server.py`):
     - Tools: `fetch_market_data`, `get_recent_ticks`, `list_jobs`
   - **Price Optimizer MCP** (inferred from `agent.py:104-127`):
     - Tools: `get_product_info`, `get_market_intelligence`, `run_pricing_algorithm`, `validate_price`, `publish_price_proposal`

**MCP Auth Capabilities System:**
- Token validation for secure MCP communication
- Capabilities negotiation on connection
- Support for multi-tenant environments

**How to Use MCP in Agents:**
```python
# Agents use get_price_optimizer_client factory (see agent.py:112-114)
from core.agents.agent_sdk.mcp_client import get_price_optimizer_client

# Factory returns either MCP client OR local function facade
tools = get_price_optimizer_client(
    use_mcp=None,  # None = read from env
    app_db=str(app_db_path),
    market_db=str(market_db_path)
)

# Call tools uniformly regardless of MCP/local mode
result = await tools.get_product_info(sku="SKU-123")
```

**Agent Instructions:**
- When creating new agent tools, **always implement both MCP and local modes**
- Use `get_price_optimizer_client()` or similar factories, never hardcode MCP/local choice
- Handle connection failures gracefully - fallback to local mode if MCP unavailable
- Test both modes: `USE_MCP=true` for integration tests, `USE_MCP=false` for unit tests

---

### 14. LLM Tool Orchestration & Autonomous Decision Making

The system features **LLM-powered autonomous agents** with sophisticated tool orchestration for multi-step reasoning.

**LLM Client Architecture (`core/agents/llm_client.py`):**

1. **Multi-Provider Failover System** (`llm_client.py:85-94`):
   - Provider priority: OpenRouter → OpenAI → Gemini
   - Automatic rotation on failure
   - Per-provider retry with exponential backoff
   - Detailed error logging and activity traces

2. **Tool Calling Modes**:
   - **Streaming with tools** (`chat_with_tools_stream`, line 216-372):
     - Real-time streaming of text deltas AND tool calls
     - Yields: `{"type": "delta", "text": "..."}` or `{"type": "tool_call", "name": "...", "status": "start"/"end"}`
     - Multi-round tool execution (up to `max_rounds` iterations)
   - **Non-streaming with tools** (`chat_with_tools`, line 195-214):
     - Synchronous multi-round tool execution
     - Returns final text after all tool calls complete

3. **Usage Tracking & Observability**:
   - Token counts (input/output) captured per response
   - Cost calculation (USD) based on provider pricing
   - Activity logging with trace IDs for debugging
   - Last usage stored in `self.last_usage` for UI display

**Autonomous Agent Pattern - Pricing Optimizer (`core/agents/price_optimizer/agent.py`):**

**System Prompt Defines Workflow** (`agent.py:47-60`):
```
1. ALWAYS start by calling get_product_info()
2. Call get_market_intelligence() for competitive context
3. Analyze and select pricing algorithm
4. Call run_pricing_algorithm()
5. Call validate_price()
6. Call publish_price_proposal()
```

**LLM-Powered Algorithm Selection** (`agent.py:279-287`):
- Uses `LLMBrain.decide_tool()` to select best algorithm based on user request and market context
- Fallback to keyword heuristics if LLM unavailable
- Algorithms: `rule_based`, `ml_model`, `profit_maximization`

**Dual-Mode Optimization** (`agent.py:161-164`):
- **Autonomous Mode** (LLM available): Full multi-step reasoning with tool calls
- **Fallback Mode** (LLM unavailable): Deterministic heuristic workflow

**Chat Executor for Tool Execution** (`core/agents/chat_executor.py`):
- Synchronous tool execution with async support
- Automatic context propagation via `contextvars`
- Error handling and result serialization
- Supports both `fn(**args)` and `fn(args)` calling conventions

**Agent Instructions:**
- When adding LLM-powered agents, **define clear system prompts** with step-by-step workflows
- Always implement **fallback heuristics** for when LLM is unavailable
- Use `get_llm_client()` to get cached singleton client (avoids re-initialization)
- For streaming responses, use `chat_with_tools_stream()` to show live tool execution
- Wrap tool functions in async wrappers if calling from sync context (see `agent.py:189-214`)
- Use `trace_id` parameter for end-to-end debugging across tool calls

---

### 15. Streaming Architecture (Frontend ↔ Backend)

The system implements **Server-Sent Events (SSE)** for real-time streaming of LLM responses, tool calls, and agent activity to the frontend.

**Backend SSE Endpoint** (`backend/routers/messages.py` - inferred from usage):
- Route: `POST /api/threads/{thread_id}/messages/stream`
- Emits multiple event types over single connection

**SSE Event Types** (`frontend/src/lib/api/sseClient.ts:5-22`):
1. **`thinking`**: LLM is processing (shows "Thinking..." indicator)
2. **`agent`**: Active agent name (e.g., `{"name": "PriceOptimizer"}`)
3. **`tool_call`**: Tool execution status
   - Start: `{"name": "get_product_info", "status": "start"}`
   - End: `{"name": "get_product_info", "status": "end"}`
4. **`message`**: Text delta or final message
   - Delta: `{"delta": "Hello"}`
   - Final: `{"id": 123, "token_in": 50, "token_out": 100, "cost_usd": 0.002, ...}`
5. **`thread_renamed`**: Auto-generated thread title
6. **`done`**: Stream completion
7. **`error`**: Error details

**Frontend SSE Client** (`frontend/src/lib/api/sseClient.ts`):

**Streaming Flow**:
```
User sends message → messageStore.send() → streamMessage()
                  ↓
            POST /stream endpoint
                  ↓
         SSE connection established
                  ↓
     Event stream parsed (sseClient.ts:89-199)
                  ↓
   onUpdate() callback triggers state updates
                  ↓
    UI re-renders with live updates
```

**Watchdog Timer** (`sseClient.ts:73-87`):
- 25-second inactivity timeout
- Polls every 5 seconds
- Auto-aborts on timeout to prevent hanging

**State Updates During Streaming** (`messageStore.ts:143-182`):
- **Thinking state**: Shows "Thinking…" message (id: -3)
- **Text deltas**: Appended to live message (id: -2)
- **Agent tracking**: `liveActiveAgent`, `liveAgents[]` for UI badges
- **Tool tracking**: `liveTool: {name, status}` for UI indicators
- **Turn statistics**: Token counts, costs, model, provider for display

**Draft Thread Auto-Creation** (`messageStore.ts:108-127`):
- Draft threads have IDs like `draft_0`, `draft_1`
- On first message send, backend creates real thread
- Frontend updates URL and thread list automatically
- Prevents empty threads in database

**Error Handling**:
- 401 → triggers `triggerUnauthorized()` (redirects to login)
- Network errors → toast notification, state cleanup
- Timeout → toast + force stream close

**Agent Instructions:**
- When adding streaming endpoints, **always use SSE event format**: `event: <type>\ndata: <json>\n\n`
- Emit `thinking` event before long-running LLM calls
- Emit `agent` events when switching between agents (e.g., Supervisor → PriceOptimizer)
- Emit `tool_call` start/end events for each tool execution
- Always emit `done` event to close stream gracefully
- For errors, emit `error` event with `{"detail": "..."}` or `{"error": "..."}`
- Backend should flush after each SSE event to ensure immediate delivery
- Frontend stores handle state transitions automatically - just emit events

---

### 16. Governance & Autonomous Price Application

The system includes **two governance agents** for autonomous price application with business rules enforcement.

**Agent #1: AutoApplier** (`core/agents/auto_applier.py`):

**Guardrails System** (stored in `app/data.db` `settings` table):
- `auto_apply`: `"true"` or `"false"` (master toggle)
- `min_margin`: Minimum profit margin (default: 0.12 = 12%)
- `max_delta`: Maximum price change vs current price (default: 0.10 = 10%)

**Decision Logging** (`auto_applier.py:83-94`):
- Every proposal logged to `decision_log` table BEFORE any action
- Decision states: `AWAITING_MANUAL_APPROVAL`, `APPLIED_AUTO`
- Tracks: SKU, old price, new price, margin, algorithm, actor, timestamp

**Optimistic Concurrency Pattern** (`auto_applier.py:96-116`):
- Uses `pricing_list.optimized_price` as base for validation
- Exponential backoff retries (0.01s → 0.5s) on lock contention
- Atomic compare-and-swap: `UPDATE ... WHERE optimized_price = ?`
- Publishes `PRICE_UPDATE` event only after successful commit

**Background Processing** (`auto_applier.py:140-141`):
- Offloads database writes to daemon thread
- Prevents blocking event bus callback
- Handles async-to-sync bridge via `asyncio.run()` in thread

**Agent #2: GovernanceExecutionAgent** (`core/agents/governance_execution_agent.py`):

**Enhanced Decision States** (`governance_execution_agent.py:82-85`):
- `RECEIVED`: Proposal logged, not yet processed
- `APPROVED`: Manual approval (future feature)
- `REJECTED`: Guardrail violation
- `APPLIED_AUTO`: Successfully applied
- `APPLY_FAILED`: Database error during application
- `STALE`: Base price changed between proposal and application

**Idempotent Processing** (`governance_execution_agent.py:166-174`):
- `INSERT OR IGNORE` for proposal receipt
- State checks before transitions
- Prevents duplicate processing of same proposal

**Guardrail Enforcement** (`governance_execution_agent.py:185-202`):
- Validates delta percentage: `abs(proposed - base) / base <= max_delta`
- Rejects if threshold exceeded, logs reason
- Uses current `pricing_list.optimized_price` as base (not `previous_price`)

**WAL Mode for Concurrency** (`governance_execution_agent.py:162-163`):
- `PRAGMA journal_mode=WAL` enables concurrent readers during writes
- `PRAGMA busy_timeout=5000` prevents immediate lock failures

**Agent Instructions:**
- When modifying pricing workflows, **always go through governance agents** (never write to `pricing_list` directly)
- Add new guardrails by inserting into `settings` table with new keys
- Decision log is immutable audit trail - never update/delete entries
- Use optimistic concurrency for all price updates (compare-and-swap pattern)
- Publish `PRICE_UPDATE` events AFTER database commit, not before
- For manual approval workflows, subscribe to `PRICE_PROPOSAL` and set `auto_apply=false`

---

### 17. Market Data Collection with Request/Response Pattern

The **Data Collector Agent** uses an asynchronous request/response pattern for reliable market data ingestion.

**Three-Event Workflow** (`core/agents/data_collector/collector.py:91-200`):

1. **MARKET_FETCH_REQUEST** published by client:
   ```python
   {
       "request_id": "uuid",
       "sku": "SKU-123",
       "market": "DEFAULT",
       "sources": ["web_scraper", "mock"],
       "urls": ["https://example.com/product"],
       "depth": 5
   }
   ```

2. **MARKET_FETCH_ACK** published by Data Collector:
   - Status: `QUEUED` → `RUNNING` → `FAILED`
   - Includes `job_id` for tracking
   - Error details if applicable

3. **MARKET_FETCH_DONE** published on completion:
   ```python
   {
       "request_id": "uuid",
       "job_id": "uuid",
       "status": "DONE",
       "tick_count": 15
   }
   ```

**Job Tracking** (`collector.py:115-127`):
- Jobs stored in database with states: `QUEUED`, `RUNNING`, `DONE`, `FAILED`
- Tracks: SKU, market, sources, depth, created_at, completed_at
- Enables monitoring and retry logic

**Duplicate Request Prevention** (`collector.py:102-109`):
- Instance-level `_processed_requests` set
- Logs duplicate attempts, ignores silently
- Prevents double-processing from event bus replays

**Data Connectors**:
1. **Web Scraper** (`connectors/web_scraper.py`):
   - Parses competitor prices from provided URLs
   - Returns `{"status": "success", "price": 99.99}` or error
2. **Mock Connector** (`connectors/mock.py`):
   - Generates synthetic ticks for testing
   - Configurable: SKU, market, depth

**MARKET_TICK Publishing** (`collector.py:48-62`):
- After ingestion, publishes typed `MarketTick` dataclass
- Dual-publish: new bus (dataclass) + legacy bus (dict) for backward compat
- Downstream agents (e.g., AlertEngine) subscribe to `MARKET_TICK` for reactive workflows

**Agent Instructions:**
- To request market data, publish `MARKET_FETCH_REQUEST` with all required fields
- Always generate unique `request_id` (use `uuid.uuid4().hex`)
- Subscribe to `MARKET_FETCH_ACK` and `MARKET_FETCH_DONE` to track progress
- Handle `FAILED` status gracefully - log errors, optionally retry
- When adding new data sources, implement connector in `connectors/` directory
- Connectors must be async and return consistent schema: `{"status": "success", ...}`

---

### 18. Testing Strategies for AI Agents

Based on codebase patterns, the following testing strategies are recommended:

**Unit Testing AI Agents** (`backend/tests/test_*_api.py` patterns):

1. **Mock External Dependencies**:
   ```python
   # Mock DataRepo to isolate API logic
   with patch("path.to.DataRepo") as mock_repo:
       mock_repo.return_value.get_product.return_value = {...}
       response = client.post("/api/endpoint", json={...})
       assert response.status_code == 200
   ```

2. **Monkeypatch Environment Variables** (`backend/tests/test_chat_api.py` patterns):
   ```python
   monkeypatch.setenv("USE_MCP", "false")
   monkeypatch.setenv("OPENAI_API_KEY", "")
   # Ensures deterministic LLM availability for tests
   ```

3. **Smoke Tests for Integration** (`scripts/smoke_*.py` patterns):
   - Test full workflows end-to-end
   - Use real databases in test mode
   - Minimal assertions, focus on "does it crash?"

**LLM Testing Strategies**:

1. **LLM Unavailable Tests** (`tests/test_llm_integration.py` inferred):
   - Test fallback heuristics when LLM disabled
   - Verify agents work in degraded mode

2. **LLM Available Tests** (`tests/test_llm_comprehensive.py` inferred):
   - Test tool calling with real API (or mock)
   - Verify tool selection logic
   - Check streaming behavior

**Event-Driven Testing**:

1. **Publish-Subscribe Tests**:
   ```python
   # Test agent reacts to events
   bus = get_bus()
   received = []
   
   async def listener(payload):
       received.append(payload)
   
   bus.subscribe(Topic.PRICE_PROPOSAL.value, listener)
   await bus.publish(Topic.PRICE_PROPOSAL.value, {...})
   
   # Assert listener was called
   assert len(received) == 1
   ```

2. **Event Journaling Verification**:
   - Check `data/events.jsonl` for expected events
   - Parse JSON lines, assert on event payloads

**Agent Instructions:**
- For API endpoints, always mock `DataRepo` and external services
- Use `monkeypatch` to control environment (LLM keys, MCP toggles)
- Write smoke tests for new workflows (`scripts/smoke_<feature>.py`)
- Test both LLM-enabled and LLM-disabled modes
- Verify event publishing/subscription in integration tests
- Use `pytest -v` to run all tests, `pytest path/to/test.py::test_name` for single test

