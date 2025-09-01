# Branch: feat/data-collector-mvp

## Purpose
Deliver the minimum viable Data Collector flow so Alerts work end-to-end without changing existing consumers. This branch focuses on: typed MARKET_TICK events, a small runner that ingests ticks, additive persistence (catalog + jobs), and MCP tools to import a catalog, start a collection, and query job status.

## Scope (minimal, additive)
- Wire DataCollector to publish core.models.MarketTick on core.protocol.Topic.MARKET_TICK via core.bus.bus.
- Add additive tables to DataRepo: product_catalog, ingestion_jobs, price_proposals (keep market_ticks as-is).
- Implement MCP tools: import_product_catalog, start_collection, get_job_status.
- Update the lightweight market collector runner to ingest mock ticks and publish events.
- Add a tiny smoke test script to exercise the tools.

## Constraints
- Python 3.11+, async/await, aiosqlite. No new external dependencies. DB changes are additive only.
- Small, focused patches. Keep existing AlertNotifier behavior unchanged.

## Acceptance (summary)
1) MARKET_TICK events are typed (MarketTick) and visible on Topic.MARKET_TICK.
2) DataRepo initializes new tables and helper functions without breaking changes.
3) MCP tools: start_collection returns job_id and transitions QUEUED → RUNNING → DONE/FAILED.
4) Smoke script runs and prints DONE plus a small snapshot.

## Notes
See the TL;DR plan in the task for step-by-step prompts (audit → wiring → runner → repo → tools → smoke → docs/commits).
