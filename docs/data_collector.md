# Data Collector — Developer Notes

Purpose:
- Ingest market ticks (our_price, competitor_price, demand_index).
- Persist ticks to app/data.db (aiosqlite).
- Expose MCP tools (fetch_market_features, ingest_tick) and publish MARKET_TICK events.

Key files:
- core/agents/data_collector/repo.py
- core/agents/data_collector/collector.py
- core/agents/data_collector/connectors/mock.py
- scripts/ingest_demo.py

DB:
- Use app/data.db for market ticks (do NOT commit DB file).
- Add DATA_DB path to local .env in each worktree.

I/O contract:
- MarketTick: { sku, our_price, competitor_price?, demand_index, ts, source }
- fetch_market_features(sku, market, time_window) => { snapshot_id, as_of, features, provenance }
