# Dynamic Pricing AI — Codebase Deep Overview (Living Document)

This document provides a progressively refined, long-form description of the repository. After each inspection pass, new sections and details are appended or revised. Treat this as a living guide to the architecture, components, and workflows.

Last updated: Pass 3 — topics, payload contracts, DB schemas, workflows, MCP tools

---

## What This Repository Is

A modular, agent-based dynamic pricing platform that:
- Ingests market data via pluggable connectors
- Computes pricing proposals with an optimization agent (LLM-assisted)
- Enforces governance and policy constraints
- Publishes alerts and integrates with downstream UIs
- Exposes an authentication API for a frontend (FluxPricer Auth API)
- Includes smoke scripts for quick end-to-end validation

The system embraces the Model Context Protocol (MCP) with separate agent services, an event/bus layer, and supporting evaluation/observability utilities.

## High-Level Architecture

- Agents (under `core/agents/`):
  - `data_collector`: Connectors (e.g., `mock`, `web_scraper`) and a collection service exposing MCP tools to ingest and feature-engineer market data.
  - `price_optimizer`: Pricing optimization agent orchestrating LLM and rules/constraints to propose optimized prices.
  - `alert_service`: Detects interesting market conditions and publishes alerts to sinks (UI, webhook, email, Slack).
  - `user_interact`: User-facing agent layer for interaction tasks.
  - `agent_sdk`: Internal toolkit with protocol definitions, event models, a bus factory, health tools, and MCP client/supervisor utilities.
  - `pricing_optimizer_bus`: Event bus integration and UI integration helpers for the pricing flow.

- Backend API (under `backend/`):
  - `main.py`: FastAPI service focused on authentication and session management. Enables local dev CORS for any `localhost` port.

- Data & Events:
  - Application DB `app/data.db` stores product catalog, ingestion jobs, price proposals, and ingested market ticks.
  - Sample dataset `data/market.db` is read-only input for the optimizer (e.g., `pricing_list`, `market_data`).
  - Event journal/schemas live under `core/events/*` and write JSONL to `data/events.jsonl`.

- Evaluation & Observability:
  - `evaluation/`: Metrics, performance monitoring, and an evaluation engine for offline/online quality checks.
  - `core/observability/logging.py`: Project-wide logging setup based on `structlog`.

- Scripts (`scripts/`):
  - Smoke tests and orchestrators to run MCP servers, agents, and simple end-to-end flows.

## Technology Stack

- Language: Python 3.8+
- API & Web: FastAPI, Uvicorn
- Data: SQLite (`aiosqlite`), Pandas, PyArrow
- AI/LLM: OpenAI-compatible clients via `openai` SDK; provider fallback through OpenRouter, OpenAI, and Gemini (configured via `.env`)
- Async & IO: `aiohttp`, `aiosmtplib`
- Validation & Models: Pydantic v2
- Security: Argon2 for password hashing, email-validator, TOTP (`pyotp`)
- Observability: `structlog`
- Protocol: MCP (Model Context Protocol)

See `requirements.txt` for the full list.

## LLM Provider Configuration

The app supports OpenAI-compatible providers in order of priority:
1) OpenRouter (`OPENROUTER_API_KEY`, optional `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL`)
2) OpenAI (`OPENAI_API_KEY`, optional `OPENAI_MODEL`)
3) Gemini via OpenAI compatibility (`GEMINI_API_KEY`, optional `GEMINI_MODEL`, `GEMINI_BASE_URL`)

Add keys to `.env` and restart. The UI falls back if higher-priority providers are unavailable.

## Entry Points and Useful Scripts

- Auth API: `backend/main.py`
  - Endpoints: `/api/register`, `/api/login`, `/api/me`, `/api/logout`
  - Initializes the auth DB on startup.

- Smoke E2E: `scripts/smoke_end_to_end.py`
  - Imports a demo product, starts a mock data collection job, captures alerts, fetches features, and asserts a minimal pass condition.

- One-off Optimizer Run: `scripts/run_pricing_agent_once.py`
  - Runs the pricing optimizer agent against a sample product (`iphone15`), writes results to `app/pricing_agent_run.json`, and dumps DB rows to `app/pricing_agent_dbrows.json`.

- MCP Servers & Runners: `scripts/run_*_mcp.py`, `scripts/poc_supervisor.py`
  - Launch individual MCP agent servers and a simple supervisor for local experimentation.

## Repository Layout (selected)

- `backend/`: FastAPI auth service
- `core/agents/`: Agent implementations and SDK
  - `data_collector/`, `price_optimizer/`, `alert_service/`, `user_interact/`, `agent_sdk/`, `pricing_optimizer_bus/`
- `core/events/`: Event journal and schemas
- `evaluation/`: Metrics and performance monitoring
- `core/observability/`: Logging setup
- `scripts/`: Smoke tests and agent/server runners
- `data/`: SQLite DB and event log storage
- `docs/`: Design docs and this overview

---

## Event Bus and Contracts

- Bus: `core/agents/agent_sdk/bus_factory.py` exposes a lightweight async in-process bus with `subscribe(topic, callback)` and `publish(topic, payload)`.
  - Validates payloads via `core/events/schemas.py::validate_payload` when `REQUIRED_KEYS` exist.
  - Best-effort journaling to `data/events.jsonl` via `core/events/journal.py::write_event`.

- Topics (`core/agents/agent_sdk/protocol.py::Topic`):
  - `market.tick`
  - `market.fetch.request`
  - `market.fetch.ack`
  - `market.fetch.done`
  - `price.proposal`
  - `price.update`
  - `alert.event`
  - `chat.prompt`, `chat.tool_call` (reserved)

- Required keys (`core/events/schemas.py::REQUIRED_KEYS`):
  - `price.proposal`: `proposal_id`, `product_id`, `previous_price`, `proposed_price`
  - `price.update`: `proposal_id`, `product_id`, `final_price`
  - `market.fetch.request`: `request_id`, `sku`, `market`, `sources`, `horizon_minutes`, `depth`
  - `market.fetch.ack`: `request_id`, `job_id`, `status`
  - `market.fetch.done`: `request_id`, `job_id`, `status`, `tick_count`

- Note on journaling vs. bus validation:
  - The optimizer writes additional journal records (e.g., `price.workflow`, and a journal-only `price.proposal` shape with `old_price/new_price`) directly via `journal.write_event`. These records are for traceability and do not pass bus validation. The bus-enforced `price.proposal` payload is emitted separately by the Pricing Optimizer agent with the required keys.

## Databases and Schemas

- Application DB `app/data.db` (see `core/agents/data_collector/repo.py`):
  - `market_ticks`: `(id, sku, market, our_price, competitor_price, demand_index, ts, source, ingested_at)`; index on `(sku, market, ts)`.
  - `product_catalog`: `(sku PRIMARY KEY, title, currency, current_price, cost, stock, updated_at)`.
  - `ingestion_jobs`: `(id PRIMARY KEY, sku, market, connector, depth, status, error, created_at, started_at, finished_at)`.
  - `price_proposals`: `(id PRIMARY KEY, sku, proposed_price, current_price, margin, algorithm, ts)`.

- Alert DB `app/alert.db` (see `core/agents/alert_service/repo.py`):
  - `rules(id, version, spec_json, enabled)`
  - `incidents(id, rule_id, sku, status, first_seen, last_seen, severity, title, group_key, fingerprint UNIQUE)`
  - `deliveries(id, incident_id, channel, ts, status, response_json)`
  - `settings(key PRIMARY KEY, value)` — includes persisted channel overrides under key `channels`.

- Sample Market DB `data/market.db` (read-only by `price_optimizer/agent.py`):
  - Reads from `pricing_list(optimized_price)` by `product_name`, falling back to `AVG(price)` from `market_data` by `product_name`.

## Agent Workflows

- Data Collector (`core/agents/data_collector/collector.py`):
  - Subscribes to `market.fetch.request`; on request:
    - Creates an `ingestion_jobs` row and publishes `market.fetch.ack` (QUEUED → RUNNING).
    - Processes sources (supports `web_scraper` if URLs provided; otherwise `mock` streaming via MCP server path), ingests ticks into `market_ticks`, and publishes typed `market.tick` events.
    - Marks job DONE and publishes `market.fetch.done` with `tick_count`; on error, marks FAILED and publishes an ACK with `status=FAILED` and `error`.

- Price Optimizer (`core/agents/price_optimizer/agent.py`, `optimizer.py`):
  - Builds context from `app/data.db` (catalog) and `data/market.db` (competitor price lookups).
  - Runs heuristic optimizer to compute `recommended_price`; journals `price.workflow` records.
  - Publishes bus `price.proposal` with required keys: `proposal_id`, `product_id` (SKU), `previous_price`, `proposed_price`.

- Alert Engine (`core/agents/alert_service/engine.py`):
  - Loads active rules from `app/alert.db` and subscribes to `market.tick` and `price.proposal`.
  - Evaluates rules (boolean expressions or detectors), correlates into `incidents` with throttling, and delivers via configured sinks (`ui`, `slack`, `email`, `webhook`).

## MCP Tool Surfaces

- Data Collector Service (`core/agents/data_collector/mcp_server.py`):
  - `start_collection(sku, market="DEFAULT", connector="mock", depth=1, capability_token) -> {ok, job_id, sku, market, connector, depth}`
  - `get_job_status(job_id, capability_token) -> {ok, job}|{ok: false, error}`
  - `fetch_market_features(sku, market="DEFAULT", time_window="P7D", freshness_sla_minutes=60, capability_token) -> {ok, features, sku, market, time_window}`
  - `ingest_tick(d, capability_token) -> {ok}`
  - `import_product_catalog(rows, capability_token) -> {ok, count, processed, total_input}|{ok: false, error}`
  - `list_sources(capability_token) -> {ok, sources[], count}`
  - Health/auth: `ping_health`, `version_info`, `health_check`, `auth_metrics`.

- Price Optimizer Service (`core/agents/price_optimizer/mcp_server.py`):
  - `propose_price(sku, our_price, competitor_price?, demand_index?, cost?, min_price?, max_price?, min_margin=0.12, capability_token) -> {ok, proposal{...}}|error`
  - `explain_proposal(proposal_id, capability_token) -> {ok, explanation{...}}`
  - `apply_proposal(proposal_id, capability_token) -> {ok, result{status: "applied"}}`
  - `cancel_proposal(proposal_id, capability_token) -> {ok, result{status: "cancelled"}}`
  - Legacy: `optimize_price(payload, capability_token)` redirects to `propose_price`.
  - Health/auth: `ping_health`, `version_info`, `health_check`, `auth_metrics`.

---

## Backlog and Follow-ups

- Path hygiene: ensure imports consistently use `core/observability/logging` (bus currently guards missing logger gracefully).
- Schema note: journal-only `price.proposal` records in `optimizer.py` differ from bus `price.proposal` schema; documented above.
- Documentation alignment: reconcile `docs/mcp_tool_contracts.md` examples with actual tool signatures and outputs observed in code (e.g., `start_collection` output shape and supported connectors).
