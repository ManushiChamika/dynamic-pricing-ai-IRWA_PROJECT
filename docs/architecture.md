# Architecture Overview

This project is composed of a Streamlit UI, modular agents, and lightweight persistence. It favors simple local setup with SQLite, while structuring components to scale to message buses and external services.

## Components

- UI (Streamlit): `app/` with pages in `app/pages`. Boots the Alert Service and renders activity, rules, and settings.
- Pricing Optimizer Agent: `core/agents/pricing_optimizer.py` implementing `PricingOptimizerAgent` (LLM Brain) and simple algorithms.
- Price Optimizer Heuristic: `core/agents/price_optimizer/optimizer.py` for feature-based pricing with guardrails.
- Data Collector: `core/agents/data_collector/` providing connectors, a repo, and an async collection service (MCP interface in `mcp_server.py`).
- Alert Service: `core/agents/alert_service/` with rules, detectors, sinks, and a small async engine and repo.
- Agent SDK: `core/agents/agent_sdk/` with an in-process event bus, protocol, and event models that decouple agents.

## Architecture Diagram

```mermaid
graph TD
  subgraph UI[Streamlit UI]
    PAGES[Pages: Home/Login/Profile/Settings]
    UI -->|reads/writes| DATA_DB[(app/data.db)]
    UI --> BUS
  end

  subgraph Agents
    OPT[Pricing Optimizer]\ncore/agents/pricing_optimizer.py
    COL[Data Collector]\nconnectors + mcp_server
    ALERT[Alert Service]\nrules + detectors + sinks
    SDK[Agent SDK]\nevent bus + models
  end

  UI --> OPT
  OPT -->|publish PriceProposal| BUS[(In-Process Bus)]
  ALERT --> BUS
  COL --> DATA_DB
  OPT --> DEMO_DB[(market.db)]
  BUS --> UI
```

## Agent Roles & Communication Flow

- Roles:
  - Pricing Optimizer: selects tools/algorithms (LLM-first, deterministic fallback), computes prices, publishes `PriceProposal`.
  - Data Collector: ingests market ticks via connectors; optional MCP tool for scraping competitor prices.
  - Alert Service: evaluates rules/detectors, sends notifications via sinks (email/slack/ui/webhook).
  - UI: entry point, visualizes activity, manages settings, and can trigger runs.
- Protocols:
  - In-Process Bus: Pub/Sub of `PriceProposal` and incidents via `agent_sdk.bus_factory` and `agent_sdk.protocol.Topic`.
  - MCP: `core/agents/data_collector/mcp_server.py` exposes scraping/tool endpoints callable by the optimizer or CLI.
  - API (internal): Alert service exposes lightweight methods consumed by UI pages.

## Data Flows

- Market ticks collected into `app/data.db` via the Data Collector.
- Pricing Optimizer consumes records from `market.db` (demo DB) and augments with scraper data if selected.
- A `PriceProposal` event is published to the bus; proposals are persisted into `app/data.db` and summarized to `market.db/pricing_list` for simple demo visibility.
- UI pages query the Alert Service API, display activity logs, incidents, and rules.

## Communication

- In-Process Bus: `agent_sdk.bus_factory` exposes a singleton bus for Pub/Sub of `PriceProposal` and other events using `agent_sdk.protocol.Topic` values.
- MCP (Model Context Protocol): Collector and other services expose thin MCP servers to be callable from LLM tools or CLIs. This supports local tools with clear schema and isolation.

## Persistence

- `auth.db` (SQLite): users and session tokens via SQLAlchemy models in `core/auth_db.py`.
- `app/data.db` (SQLite): `market_ticks`, `product_catalog`, `ingestion_jobs`, `price_proposals` handled by `DataRepo`.
- `market.db` (SQLite, demo): `market_data`, `pricing_list` used by optimizer demos and scripts.

## Deployment Notes

- Local-first. Replace in-process bus with an external queue (e.g., Redis, NATS) if scaling beyond one process.
- Replace SQLite with Postgres for multi-writer concurrency. The repo structure cleanly isolates DB access in small repos.
- LLM usage is optional; all flows degrade gracefully without keys.

## Security Considerations

- Never commit real credentials. Use `.env` locally.
- Authentication DB is local SQLite for demos; in production switch to a managed DB and harden secrets, password hashing, and token lifetimes.
- The scraper is optional and should be used in compliance with target sites' robots and terms.

