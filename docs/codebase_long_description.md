# Dynamic Pricing AI — Long Description (Living Document)

This is a living technical narrative of the codebase. It is updated in rounds after inspecting modules, tools, and scripts. Each pass adds depth, clarifies contracts, and calls out inconsistencies or “junk code” to address.

Last updated: Pass 5 — Orchestrators, MCP lifecycle, config/logging

---

## Executive Summary

This repository implements a modular, agent-based dynamic pricing platform. It ingests market data via pluggable connectors, proposes optimized prices via a pricing agent, and detects noteworthy events via an alert engine. Services expose MCP tools, communicate through a lightweight in-process event bus, and persist state in SQLite databases. A small FastAPI backend provides auth endpoints for a frontend. Smoke scripts demonstrate end-to-end flows.

Key strengths:
- Clear agent boundaries with MCP tool surfaces.
- Lightweight, pragmatic event bus with schema checks and journaling.
- Simple, inspectable SQLite persistence with WAL mode.
- Useful scripts and smoke tests for local validation.

Key caveats/to-dos:
- Some input/output mismatches between docs and implementations.
- A few placeholder or legacy compatibility paths and prints in runtime code.
- Web scraping connector is illustrative, not production-safe.

---

## Architecture Overview

- Agents (core/agents/)
  - data_collector: Accepts collection requests, ingests ticks from connectors (mock, early web_scraper), computes basic features, exposes MCP tools for jobs, ticks, features, and catalog import.
  - price_optimizer: Builds context from app/data.db and data/market.db, applies a heuristic optimizer, journals workflow, and publishes bus price proposals. Exposes MCP tools to propose/explain/apply/cancel proposals.
  - alert_service: Loads rules, listens to market ticks and price proposals, correlates into incidents, and delivers to sinks (ui, slack, email, webhook).
  - agent_sdk: Event protocol, async bus, health tools, auth, activity logging, and MCP client/supervisor utilities.
  - pricing_optimizer_bus and user_interact: Integration helpers and interaction agent scaffolding.

- Backend (backend/main.py)
  - FastAPI service focused on auth: register, login, me, logout. Configures permissive localhost CORS for dev.

- Data & Events
  - app/data.db: product catalog, ingestion jobs, market ticks, price proposals.
  - app/alert.db: alert rules, incidents, deliveries, and settings.
  - data/market.db: sample read-only market dataset for the optimizer.
  - data/events.jsonl: event journal, best-effort writes of bus traffic and additional workflow breadcrumbs.

- Scripts (scripts/)
  - smoke_* flows, MCP server runners, data population utilities.

---

## Eventing: Topics, Validation, Journaling

- Topics (core/agents/agent_sdk/protocol.py)
  - market.tick
  - market.fetch.request | .ack | .done
  - price.proposal | price.update
  - alert.event
  - chat.prompt | chat.tool_call (reserved)

- Schema checks (core/events/schemas.py)
  - REQUIRED_KEYS enforced on publish when defined:
    - price.proposal: proposal_id, product_id, previous_price, proposed_price
    - price.update: proposal_id, product_id, final_price
    - market.fetch.request: request_id, sku, market, sources, horizon_minutes, depth
    - market.fetch.ack: request_id, job_id, status
    - market.fetch.done: request_id, job_id, status, tick_count

- Bus (core/agents/agent_sdk/bus_factory.py)
  - subscribe(topic, callback): allows sync or async callbacks.
  - publish(topic, payload): validates, journals, and dispatches; logs invalid payloads instead of raising.

- Journal (core/events/journal.py)
  - Best-effort append-only JSONL at data/events.jsonl with {ts, topic, payload}.

Note: The optimizer writes a journal-only “price.proposal” record with old_price/new_price — not bus-validated; intended for traceability.

### Example Bus Payloads

- price.proposal (bus-enforced):
```json
{
  "proposal_id": "37bb8d0f-7e6b-4a82-a2c7-1e7d8e7e7f72",
  "product_id": "iphone15",
  "previous_price": 999.0,
  "proposed_price": 949.0
}
```

- market.fetch.request:
```json
{
  "request_id": "d3a7b1e0-1c2d-4a5b-9f8e-123456789abc",
  "sku": "iphone15",
  "market": "DEFAULT",
  "sources": ["web_scraper"],
  "horizon_minutes": 60,
  "depth": 1
}
```

- market.fetch.ack / market.fetch.done:
```json
{
  "request_id": "d3a7b1e0-1c2d-4a5b-9f8e-123456789abc",
  "job_id": "J-2025-09-29-001",
  "status": "RUNNING"
}
```
```json
{
  "request_id": "d3a7b1e0-1c2d-4a5b-9f8e-123456789abc",
  "job_id": "J-2025-09-29-001",
  "status": "DONE",
  "tick_count": 5
}
```

## Authentication

- Token: `capability_token` required by protected tools; verified by `core/agents/agent_sdk/auth.py::verify_capability`.
- Scopes: defaults per service via `DEFAULT_SCOPES` (e.g., data_collector: read, write, collect, import; price_optimizer: read, write, propose, apply, explain; admin has all including admin).
- Creation: use `create_token(scopes)` or `get_service_token(service_name)` in code; admin metrics require `admin` scope.
- Formats: legacy `iat:scopes.signature` and v2 `iat:exp:scopes.signature` supported; expiry enforced with small skew tolerance.
- Decorator: services may also use `require_scope("scope")` for per-tool enforcement.

## MCP Tool Examples

### Data Collector

- fetch_market_features (actual shape)
```json
{
  "ok": true,
  "sku": "iphone15",
  "market": "DEFAULT",
  "time_window": "P7D",
  "snapshot_id": "snap:iphone15:DEFAULT:2025-09-29T12:34:56Z",
  "as_of": "2025-09-29T12:34:56Z",
  "features": {
    "our_price": 999.0,
    "competitor_price": 949.0,
    "demand_index": 1.0,
    "price_gap_pct": 0.05
  },
  "provenance": ["market_ticks"],
  "count": 3
}
```

- start_collection (success)
```json
{
  "ok": true,
  "job_id": "J-2025-09-29-001",
  "sku": "iphone15",
  "market": "DEFAULT",
  "connector": "mock",
  "depth": 3
}
```
- start_collection (unsupported connector)
```json
{
  "ok": false,
  "error": "unsupported_connector",
  "supported_connectors": ["mock"]
}
```

- list_sources
```json
{
  "ok": true,
  "sources": [
    {"name": "mock", "type": "mock", "status": "active", "description": "Mock data generator for testing", "last_check": "2025-09-29T12:34:56Z"},
    {"name": "web_scraper", "type": "web_scraper", "status": "inactive", "description": "Web scraping data connector", "last_check": "2025-09-29T12:34:56Z"}
  ],
  "count": 2
}
```

- get_job_status
```json
{
  "ok": true,
  "job": {
    "id": "J-2025-09-29-001",
    "sku": "iphone15",
    "market": "DEFAULT",
    "connector": "mock",
    "depth": 3,
    "status": "RUNNING",
    "error": null,
    "created_at": "2025-09-29T12:34:56Z",
    "started_at": "2025-09-29T12:35:00Z",
    "finished_at": null
  },
  "job_id": "J-2025-09-29-001"
}
```

- Error shapes
```json
{"ok": false, "error": "auth_error", "message": "missing or invalid capability"}
{"ok": false, "error": "validation_error", "details": [{"loc": ["sku"], "msg": "field required", "type": "value_error.missing"}]}
{"ok": false, "error": "internal_error", "message": "..."}
```

### Price Optimizer

- propose_price (intended shape)
```json
{
  "ok": true,
  "proposal": {
    "proposal_id": "f5a2f6f1-7e98-4d86-9a8d-5f0b3a1c2d4e",
    "sku": "iphone15",
    "current_price": 999.0,
    "proposed_price": 979.0,
    "expected_margin": 0.2,
    "confidence": 0.6,
    "reasoning": "Competitor undercut → reduce slightly; Margin floor enforced",
    "expires_at": "2025-09-30T12:34:56Z",
    "inputs": {
      "competitor_price": 949.0,
      "demand_index": 1.1,
      "cost": 700.0,
      "min_price": 900.0,
      "max_price": 1100.0,
      "min_margin": 0.12
    }
  }
}
```
Note: The underlying optimizer returns keys `recommended_price` and `rationale`. The MCP wrapper currently looks for `price` and `reasoning`, so `proposed_price` may fall back to `our_price`. Harmonize by mapping `recommended_price → proposed_price` and `rationale → reasoning`, and pass through `confidence`.

- explain_proposal
```json
{
  "ok": true,
  "explanation": {
    "proposal_id": "f5a2f6f1-7e98-4d86-9a8d-5f0b3a1c2d4e",
    "reasoning": "Price optimization considers market conditions, competitor pricing, and demand patterns",
    "factors": [
      {"name": "competitor_price", "weight": 0.3, "description": "Impact of competitor pricing on our positioning"},
      {"name": "demand_index", "weight": 0.25, "description": "Customer demand signal for price sensitivity"},
      {"name": "cost_margin", "weight": 0.25, "description": "Minimum margin requirements based on cost structure"},
      {"name": "market_position", "weight": 0.2, "description": "Our competitive position in the market segment"}
    ],
    "algorithm": "Multi-factor optimization with constraint satisfaction",
    "generated_at": "2025-09-29T12:34:56Z"
  }
}
```

- apply_proposal / cancel_proposal
```json
{"ok": true, "result": {"proposal_id": "...", "status": "applied", "applied_at": "..."}}
{"ok": true, "result": {"proposal_id": "...", "status": "cancelled", "cancelled_at": "..."}}
```

- Error shapes
```json
{"ok": false, "error": "auth_error", "message": "missing or invalid capability"}
{"ok": false, "error": "validation_error", "details": [{"loc": ["our_price"], "msg": "ensure this value is greater than 0", "type": "value_error.number.not_gt"}]}
{"ok": false, "error": "optimization_error", "message": "..."}
```

---

## Datastores and Schemas

- app/data.db (core/agents/data_collector/repo.py)
  - market_ticks(id, sku, market, our_price, competitor_price, demand_index, ts, source, ingested_at)
  - product_catalog(sku PK, title, currency, current_price, cost, stock, updated_at)
  - ingestion_jobs(id PK, sku, market, connector, depth, status, error, created_at, started_at, finished_at)
  - price_proposals(id PK, sku, proposed_price, current_price, margin, algorithm, ts)

- app/alert.db (core/agents/alert_service/repo.py)
  - rules(id PK, version, spec_json, enabled)
  - incidents(id PK, rule_id, sku, status, first_seen, last_seen, severity, title, group_key, fingerprint UNIQUE)
  - deliveries(id PK, incident_id, channel, ts, status, response_json)
  - settings(key PK, value) — includes channel settings under key "channels".

- data/market.db (read-only)
  - price_optimizer uses pricing_list(optimized_price) by product_name, fallback to AVG(price) from market_data.

Note: DB path inconsistency — runtime uses `DATA_DB` env or defaults to `app/data.db`, while repo has `data/market.db` for samples. Consolidate paths via config to avoid confusion.

---

## Agents in Detail

### Data Collector (core/agents/data_collector)
- Subscribes to market.fetch.request and drives connectors; publishes market.fetch.ack and market.fetch.done, and emits market.tick events.
- Implements duplicate request suppression by request_id at runtime.
- ingest_tick() normalizes payload and inserts into market_ticks, then publishes a typed MarketTick on the bus.
- Supports a mock connector; web_scraper is illustrative and relies on requests + BeautifulSoup to extract a price.
- Repository includes feature extraction (latest snapshot + simple gap), product upsert with ON CONFLICT, and job state transitions.

MCP Tools (mcp_server.py):
- start_collection(sku, market="DEFAULT", connector="mock", depth=1, capability_token) → {ok, job_id, sku, market, connector, depth} | {ok:false, error}
- get_job_status(job_id, capability_token) → {ok, job, job_id} | {ok:false, error}
- fetch_market_features(sku, market, time_window="P7D", freshness_sla_minutes=60, capability_token) → {ok, features, sku, market, time_window}
- ingest_tick(d, capability_token) → {ok}
- import_product_catalog(rows, capability_token) → {ok, count, processed, total_input} | error
- list_sources(capability_token) → {ok, sources[], count}
- Health/auth: ping_health, version_info, health_check, auth_metrics

### Price Optimizer (core/agents/price_optimizer)
- Agent builds context from app/data.db and data/market.db, catalogs product, looks up competitor price, and runs heuristic optimize() with margin floor and competitor undercut logic.
- Journals price.workflow breadcrumbs and, if bus available, publishes a bus-compliant price.proposal payload.

MCP Tools (mcp_server.py):
- propose_price(sku, our_price, competitor_price?, demand_index?, cost?, min_price?, max_price?, min_margin=0.12, capability_token) → {ok, proposal{...}}
- explain_proposal(proposal_id, capability_token) → {ok, explanation{...}}
- apply_proposal(proposal_id, capability_token) → {ok, result{status:"applied"}}
- cancel_proposal(proposal_id, capability_token) → {ok, result{status:"cancelled"}}
- Legacy helper: optimize_price(payload, capability_token) → redirects to propose_price
- Health/auth: ping_health, version_info, health_check, auth_metrics

### Alert Service (core/agents/alert_service)
- Loads enabled rules, subscribes to MARKET_TICK and PRICE_PROPOSAL, evaluates rules and detectors, correlates by fingerprint into incidents, and delivers via configured sinks (ui, slack, email, webhook). Throttle windows supported.

MCP Tools (mcp_server.py):
- list_alerts(status?, rule_id?, limit=100, capability_token) → {ok, alerts[], count} | {ok:false, error}
- create_alert(spec, capability_token) → {ok, id} | {ok:false, validation_error|auth_error|internal_error}
- ack_alert(alert_id, capability_token) → {ok} | error
- resolve_alert(alert_id, capability_token) → {ok} | error
- subscribe_alerts(rule_id?, severity?, callback_url?, capability_token) → {ok, subscription_id, message} | error
- Legacy: create_rule(spec), list_rules(), list_incidents(status?), ack_incident(id), resolve_incident(id)
- Health/auth: ping_health, version_info, health_check, auth_metrics (requires admin)

Example: create_alert
```json
{
  "ok": true,
  "id": "pp_spike"
}
```

Example: list_alerts
```json
{
  "ok": true,
  "alerts": [
    {
      "id": "inc_1727600000000",
      "rule_id": "pp_spike",
      "sku": "iphone15",
      "status": "OPEN",
      "first_seen": "2025-09-29T12:34:56.000000+00:00",
      "last_seen": "2025-09-29T12:35:10.000000+00:00",
      "severity": "warn",
      "title": "pp_spike on iphone15"
    }
  ],
  "count": 1
}
```

Example: ack_alert / resolve_alert
```json
{"ok": true}
```

Example: subscribe_alerts
```json
{
  "ok": true,
  "subscription_id": "sub_123456789",
  "message": "Subscription created successfully"
}
```

RuleSpec shape (schemas.py):
```json
{
  "id": "pp_spike",
  "source": "PRICE_PROPOSAL",
  "where": "proposed_price < current_price * 0.95",
  "severity": "warn",
  "dedupe": "sku",
  "group_by": [],
  "notify": {"channels": ["ui"], "throttle": "15m"},
  "enabled": true
}
```

Detector-based rule example (detectors.py + rules.py):
```json
{
  "id": "demand_outlier",
  "source": "MARKET_TICK",
  "detector": "ewma_zscore",
  "field": "demand_index",
  "params": {"alpha": 0.3, "z": 3.0},
  "hold_for": "5m",
  "severity": "crit",
  "notify": {"channels": ["ui", "slack"], "throttle": "30m"},
  "enabled": true
}
```

Engine flow (engine.py):
- Subscribes to `market.tick` and `price.proposal`.
- On bus event: for each matching rule (by `source`), evaluate either `where` expression or `detector` result.
- If fired, build Alert with `severity` from rule, correlate via fingerprint (`{rule_id}:{sku}`) to Incident, then deliver to configured sinks.
- Throttle: if `notify.throttle` is set and an incident with same fingerprint fired recently, skip creating/updating (touch `last_seen`).

Sinks:
- ui: publishes incident dict to `alert.event` on the bus.
- slack: posts formatted text to webhook URL (retries, records delivery)
- email: SMTP send with STARTTLS if available (retries, records delivery)
- webhook: POST minimal JSON payload (retries, records delivery)

Error shapes (MCP layer):
```json
{"ok": false, "error": "auth_error", "message": "missing or invalid capability"}
{"ok": false, "error": "validation_error", "details": [{"loc": ["status"], "msg": "string does not match regex", "type": "value_error.str.regex"}]}
{"ok": false, "error": "internal_error", "message": "..."}
```

---

## Backend API (backend/main.py)
- FastAPI app providing authentication endpoints used by the frontend UI:
  - POST /api/register, /api/login
  - GET /api/me
  - POST /api/logout
- Initializes auth DB at startup and enables localhost CORS.

---

## Observability and Evaluation
- Logging (core/observability/logging.py) integrates structlog-style structured logs.
- Evaluation (evaluation/) includes metrics, evaluation_engine.py, and performance_monitor.py for offline/online assessments.

---

## Scripts and Smoke Tests (selected)
- scripts/smoke_end_to_end.py: end-to-end sanity flow importing a product, starting collection, checking alerts, and feature pulls.
- scripts/run_*_mcp.py: run individual MCP servers for data_collector and price_optimizer.
- scripts/poc_supervisor.py: simple MCP supervisor for local experimentation.
- Data population and CLI validation helpers are under scripts/.
- tests under scripts/ prefixed with test_* provide functional checks around pricing operations and agent CLIs.

---

## Notable Inconsistencies and Potential “Junk Code”

Alert Service specific:
- Severity taxonomy mismatch:
  - Schemas use `info|warn|crit` (schemas.py: Severity).
  - subscribe_alerts validates `low|medium|high|critical`.
  - Recommendation: Standardize on `info|warn|crit` across tools and docs; if UI needs mapping, translate UI levels to schema levels at the edge.
- Auth method inconsistency:
  - alerts mcp_server uses `verify_capability_legacy` raising PermissionError; other agents use `verify_capability` returning structured AuthError.
  - Recommendation: Switch to `verify_capability` and/or use `require_scope` decorator for uniform responses and metrics.
- Event schema looseness:
  - `alert.event` has no REQUIRED_KEYS; ui sink publishes raw dicts from incidents; engine publishes SimpleNamespace for ready-notice.
  - Recommendation: Introduce a minimal REQUIRED_KEYS for `alert.event` (e.g., id, rule_id, sku, severity, title, ts) to improve tooling reliability.
- Mixed payload typing:
  - engine converts payloads with best-effort dict extraction; sinks then re-coerce to dicts.
  - Recommendation: Normalize to pydantic models at boundaries and `.model_dump()` before bus publish.
- Channel config source:
  - sinks merge env/secrets with DB overrides; UI path not fully documented.
  - Recommendation: Document `settings` table key `channels` and fields; add a tool to get/set these settings.
- Missing retry helper:
  - sinks import `..util.retry.retry`, but `core/agents/alert_service/util/retry.py` is absent in the repo snapshot.
  - Recommendation: add a small async retry utility or inline simple retry loops in sinks.


These are areas that look inconsistent, placeholder-y, or in need of cleanup.

1) Price Optimizer MCP output vs optimizer result
- File: core/agents/price_optimizer/mcp_server.py (propose_price)
- Uses res.get("price"), res.get("margin"), res.get("reasoning"). But optimizer.optimize returns keys: recommended_price, confidence, rationale, constraints_evaluation.
- Effect: proposed_price may fall back to our_price; expected_margin defaults to min_margin; reasoning falls back to a generic string; confidence may not come from the optimizer.
- Recommendation: Align keys or adapt the wrapper to map optimize() → MCP schema consistently.

2) Data Collector connectors list vs enforcement
- File: core/agents/data_collector/mcp_server.py
- StartCollectionRequest allows connector pattern ^(mock|web_scraper|api)$, but implementation explicitly supports only "mock" and returns {error:"unsupported_connector"} for others.
- Recommendation: Either implement connector modes, or narrow the validation enum/pattern and update docs accordingly.

3) Dual-publish to a legacy bus in DataCollector
- File: core/agents/data_collector/collector.py
- Attempts to import legacy get_bus/Topic from core.agents.agent_sdk (module-level) and dual-publish payloads.
- This is defensive, but may be leftover from a migration. If the legacy bus is not in use, consider removing for simplicity.

4) Print statements in runtime paths
- Files: data_collector/collector.py, data_collector/mcp_server.py
- Various print() diagnostics in async flows (job start/end, errors). Good for dev, but should likely move to structured logging for production paths.

5) Journal topic name collision risk
- File: core/agents/price_optimizer/optimizer.py
- Writes a journal record under "price.proposal" with old_price/new_price fields that do not match the bus-enforced schema. While the bus only validates on publish() and journal.write_event() is separate, using the same topic string in the journal could confuse tooling.
- Recommendation: Use a distinct journal-only topic like "price.proposal.journal" to avoid ambiguity.

6) Web scraper connector as illustrative code
- File: core/agents/data_collector/connectors/web_scraper.py
- Uses requests + BeautifulSoup to parse pages with heuristic CSS selectors. Not async, no robots.txt handling, and selectors are example-only. Clearly educational; document as non-production and keep disabled by default.

7) Health/MCP fallbacks
- Files: price_optimizer/mcp_server.py, data_collector/mcp_server.py
- Each contains a fallback or guard for FastMCP absence. This is acceptable, but ensure serve() paths produce clear runtime errors and docs note MCP dependency.

8) DB path inconsistency
- Files: core/agents/data_collector/repo.py and repository layout
- Default DB is `app/data.db`; meanwhile repo includes `data/market.db` samples and scripts expecting `data/`. Consolidate via config to avoid confusion between `app/` and `data/` roots.

---

## Roadmap Suggestions

- Align MCP contract docs with actual tool signatures and outputs.
- Normalize optimizer result keys and MCP response fields (map recommended_price → proposed_price, rationale → reasoning, include constraints and confidence consistently).
- Replace prints with structured logs; apply consistent logger imports.
- Tighten Data Collector connector validation to reflect what is actually supported, or implement web_scraper/api in the background job runner.
- Consider separating journal-only topics from bus topics by naming convention.
- Extend tests to cover MCP tool contracts and event payload validation on the bus.

---

## How To Run (high level)

- Set up environment variables for LLM providers as needed; see .env.example and README.
- Start the auth backend: python backend/main.py (or via uvicorn if configured).
- Run MCP servers: scripts/run_data_collector_mcp.py and scripts/run_price_optimizer_mcp.py.
- Execute smoke: scripts/smoke_end_to_end.py to validate ingestion → optimization → alerts.

---

---

## Bus Internals (Pass 4)

- Implementation: `core/agents/agent_sdk/bus_factory.py` defines a lightweight `_AsyncBus` with `subscribe(topic, callback)` and `publish(topic, message)` methods. Callbacks can be sync or async; `publish` awaits coroutines.
- Validation: On publish, the bus calls `core/events/schemas.validate_payload(topic, payload)`. If required keys are missing, it logs a warning (when logger available) and drops the event instead of raising.
- Journaling: Every published event attempts a best-effort append to `data/events.jsonl` via `core/events/journal.write_event(topic, payload)` and never raises.
- Logging: Uses `core.observability.logging.get_logger("bus")` if available. Sink errors are logged as `bus_sink_error` but do not interrupt other subscribers.
- Singleton: `get_bus()` returns a module-level `_AsyncBus` singleton.
- Topics: Enumerated in `core/agents/agent_sdk/protocol.py::Topic`. Note that `alert.event` is defined but currently has no REQUIRED_KEYS, which makes downstream tooling fragile.

Practical guidance:
- Prefer publishing well-typed dicts that match `REQUIRED_KEYS` in `core/events/schemas.py`. Extend `REQUIRED_KEYS` as contracts stabilize.
- Treat journaling as telemetry; use distinct “journal-only” topics for payloads that differ from bus contracts.

## SDK Utilities (Pass 4)

- auth.py: Token creation/verification with legacy and v2 formats; `require_scope` decorator for MCP tools; simple in-memory metrics; default scopes for services; `verify_capability_legacy` provided for backward compatibility (alerts service still uses it in places; unify to `verify_capability`/`require_scope`).
- activity_log.py: Thread-safe in-memory ring buffer of activities with `generate_trace_id`, `should_trace` (env `TRACE_STEPS`), `safe_redact` for truncation and secret masking, and `recent()` exposure for UI/debug.
- health_tools.py: `ping`, `version`, and `health(service_name, check_dependencies=True)` helpers. Dependency checks currently import `.repo` from the SDK, which doesn’t exist. Recommendation: move dependency checks into each service’s MCP layer (or inject check functions) rather than SDK.

## Pricing Optimizer UI Bus (Pass 4)

- Modules: `core/agents/pricing_optimizer_bus/`
  - `bus_iface.py`: tiny in-process pub/sub (sync callbacks only) with a singleton `bus`.
  - `bus_events.py`: ad-hoc event name strings for UI status.
  - `pricing_ui_integration.py`: Streamlit-based helper wiring the PricingOptimizerAgent to the UI via the ad-hoc bus, using background threads and `st.session_state`.
- Notes: This is demo-oriented and duplicates the core bus. Recommendation: consolidate on `agent_sdk` bus with proper topics (e.g., `price.workflow`, `price.status`) or clearly mark this as demo-only and keep out of core paths.

## User Interaction Agent (Pass 4)

- File: `core/agents/user_interact/user_interaction_agent.py`
- Purpose: Provide a chat-style interface that can call into pricing, data collection, and alert agents; optionally uses an LLM client when available.
- Capabilities:
  - Memory of messages; journaling of `chat.prompt` events; activity logging when `TRACE_STEPS=1`.
  - Tools exposed to the LLM: `execute_sql` (read-only, capped), `list_inventory`, `list_market_prices`, `list_proposals`, `optimize_price` (calls core optimizer), `run_pricing_workflow` (calls PricingOptimizerAgent end-to-end), `request_market_fetch` (publishes `market.fetch.request` and listens for ACK/DONE), `scan_for_alerts`, `collect_market_data`.
  - Safe SQLite access via `file:...?...mode=ro` and table existence checks; result truncation and redaction utilities.
- Caveats:
  - Mixes sync/async via threads; uses timeouts and best-effort error handling.
  - Direct DB reads bypass MCP in some flows (appropriate for demos, not production boundaries).
  - UI-specific features (sound beeps, Streamlit in other modules) should remain optional and not in core service code paths.

## Additional Inconsistencies (Pass 4)

- Health tools repo import: `agent_sdk/health_tools.py` imports `.repo` (DataRepo/Repo) that do not exist in the SDK. Move dependency checks into each service’s MCP layer or pass callables into the SDK.
- Duplicate bus: `pricing_optimizer_bus` implements a separate bus for UI updates. Prefer the unified `agent_sdk` bus or clearly isolate as demo-only.
- Alert event schema: Add minimal `REQUIRED_KEYS` for `alert.event` (id, rule_id, sku, severity, title, ts) to improve interoperability.
- Auth consistency: Replace uses of `verify_capability_legacy` in alert MCP with `require_scope`/`verify_capability` for consistent error shapes and metrics.
- Journal vs bus topic names: Avoid writing non-conforming payloads under bus-enforced topic names; use distinct journal-only names (e.g., `price.proposal.journal`).

---

## Orchestrators (Pass 5)

- AlertNotificationAgent: simple demo scanner over SQLite that emits in-memory alert summaries. Uses low/medium/high severities and never touches the bus. Treat as UI helper; not part of the core alert_service path.
- DataCollectionAgent: demo agent that reads product catalog, generates mock competitor observations, and stores to data/market.db. Provides summaries for UI; complements, but does not replace, the production data_collector MCP server.
- AutoApplier: subscribes to price.proposal and applies governance guardrails from app/data.db settings. Logs decisions to decision_log, updates market.pricing_list, then publishes price.update. Payload currently misaligned with REQUIRED_KEYS; see Contradictions.
- GovernanceExecutionAgent: alternate, more schema-driven implementation of auto-apply. Uses PriceProposalPayload/PriceUpdatePayload and conforms to price.update REQUIRED_KEYS. Likely intended successor to AutoApplier; choose one path.
- Supervisor: end-to-end POC orchestrator for import → collect via MCP/local → optimize → persist → publish proposal. Publishes PriceProposal dataclass directly to bus (will be dropped); convert to dict per bus schema.

## MCP Client & Supervisor (Pass 5)

- mcp_client.DataCollectorTools: facade that toggles MCP via USE_MCP. The MCP path uses a connection pool with TTL, timeouts, retries, and jittered backoff. Falls back to local in-process functions if MCP not available.
- mcp_supervisor.MCPSupervisor: manages external MCP servers as subprocesses with start/stop/restart and a periodic health monitor. Publishes mcp.service.* and mcp.supervisor.* events to the bus; these topics are not registered in protocol/schemas and are effectively journal-only today.
- Lifecycle: start_all runs services in parallel and emits a roll-up started event; stop_all cancels health checks, terminates processes with timeout/kill fallback, shuts down MCP client pools, and emits stopped event.

## Config & Logging (Pass 5)

- core/config.py: centralizes env parsing with validation. Generates a dev auth secret when absent to keep local flows working; in production, require MCP_AUTH_SECRET ≥ 32 chars. Supports BUS_BACKEND=redis, but no Redis bus implementation exists; document as placeholder and keep default inproc. Exposes setup_logging and helper checks.
- core/observability/logging.py: structured logging with structlog when available; adds correlation_id and optional agent name via contextvars. Provide new_correlation_id for request/workflow scoping.

## Contradictions and Fix List (Pass 5)

- Dataclass on bus: alert_notifier and supervisor publish dataclass instances; bus expects dicts. Action: publish dicts (asdict) matching schemas.
- price.update mismatch (AutoApplier): publishes sku/new_price/actor/proposal_id/action. REQUIRED_KEYS are proposal_id/product_id/final_price. Action: align to schema or write to journal-only topic (price.update.journal) and let GovernanceExecutionAgent own bus-compliant updates.
- GovernanceExecutionAgent import: imports core.payloads, which exists at repo root, not core/. Verify import path is resolvable in runtime. Action: keep as-is or move file under core/ for clarity.
- Supervisor bus var: uses await bus.publish(...) but no bus is defined. Action: import get_bus() and call get_bus().publish(...), and publish dict payloads.
- Severity taxonomy drift: AlertNotificationAgent uses low/medium/high while alert_service uses info/warn/crit. Action: map demo severities to canonical at edges.
- Unregistered topics: mcp.service.* and mcp.supervisor.* not in protocol/schemas. Action: either register in protocol.Topic and add minimal REQUIRED_KEYS or mark as journal-only in docs.
- Redis config vs implementation: BUS_BACKEND=redis is validated but unsupported. Action: document as future work; default remains inproc.

---

End of Pass 5.

