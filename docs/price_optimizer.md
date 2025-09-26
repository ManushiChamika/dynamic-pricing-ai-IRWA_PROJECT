# Price Optimizer

This document explains how the Pricing Optimizer works, including its tool/algorithm selection, data flow, and publish/persist behavior.

## Overview

The optimizer is implemented in `core/agents/pricing_optimizer.py` with a unified agent `PricingOptimizerAgent` (alias of `LLMBrain`). It orchestrates:
- Data freshness checks against `market.db` (tables `market_data`, `pricing_list`).
- Optional scraping via the Data Collector Web Scraper tool.
- Tool selection (LLM-first, heuristic fallback) to choose pricing algorithm.
- Price computation using one of the built-in algorithms.
- Hybrid publication of a `PriceProposal` to the in-process event bus, plus background persistence to `app/data.db` for UI features.
- Update of `pricing_list` in `market.db` for demo scripts.

## Tool Selection (LLM Brain)

- The agent builds a prompt listing available tools with short descriptions.
- If a provider key is available (`OPENROUTER_API_KEY` preferred, else `OPENAI_API_KEY`) and the `openai` SDK is installed, it calls chat completions to select the most appropriate tool and arguments.
- If no LLM is available, the agent applies deterministic rules:
  - If the user request contains a URL and the `fetch_competitor_price` tool is available, select that tool.
  - If the request mentions “profit” or “maximize”, select `profit_maximization`.
  - Otherwise select `rule_based`.

The agent performs two selections:
1) Optional pre-step for `fetch_competitor_price` to augment records.
2) Pricing algorithm choice from `{rule_based, ml_model, profit_maximization}`.

## Algorithms

Given a list of records `(price, update_time)` from `market_data`:
- `rule_based`: average competitor price minus 2%.
- `ml_model`: placeholder that returns the average competitor price (stub for future ML model).
- `profit_maximization`: average competitor price with +10% markup.

Separately, `core/agents/price_optimizer/optimizer.py` contains a small heuristic function operating on structured features with margin guardrails; this is used by other parts of the system and the UI but is not the primary flow in `PricingOptimizerAgent`.

## Data Flow

- Input data source: `market.db` at repo root (demo DB), table `market_data(product_name, price, features, update_time)`.
- Output targets:
  - `pricing_list` table in `market.db` is updated with `(product_name, optimized_price, last_update, reason)`.
  - A `PriceProposal` event is published asynchronously to the agent bus for other services (e.g., AutoApplier, UI activity feed).
  - A copy of the proposal is also persisted asynchronously into `app/data.db` table `price_proposals` to support UI timelines.

## Scraper Integration (Optional)

If `core.agents.data_collector.connectors.web_scraper.fetch_competitor_price` is importable, the agent may select it when the request contains a URL or when the LLM chooses it. The result augments the records and is also inserted into `market_data` with `features='scraped'` when possible.

## Running Once (Demo)

- Prepare demo DB: `python core/create_market_db.py` and `python scripts/insert_mock_market_data.py`.
- Run one-shot workflow: `python scripts/run_pricing_agent_once.py`.
  - Writes `app/pricing_agent_run.json` with the agent result.
  - Writes `app/pricing_agent_dbrows.json` containing rows from `pricing_list`.

## Configuration

- Provider keys are loaded from environment or `.env`.
- Preferred provider: OpenRouter (`OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL`). Default model `z-ai/glm-4.5-air:free` when available.
- OpenAI fallback: `OPENAI_API_KEY`, `OPENAI_MODEL`.
- Without keys or `openai` SDK, the optimizer uses deterministic selection and still functions.

## Error Handling & Transparency

- The agent logs major workflow steps to an activity log (best-effort) for UI transparency when `core.agents.agent_sdk.activity_log` is available.
- Scraper errors or LLM errors are caught and logged; the agent falls back to deterministic selection and continues where possible.

## Evaluation (Demo)

- Setup: insert mock data, then run `python scripts/run_pricing_agent_once.py`.
- Metrics (illustrative):
  - Latency per run: ~0.4–1.2s without LLM; ~1.5–4s with LLM (network-bound).
  - Deterministic fallback accuracy: when compared to mean competitor price benchmark on mock data, heuristic remains within ±5–12% depending on selected algorithm.
- Artifacts: JSON output written to `app/` and `pricing_list` table updated in `market.db`.

## Notes

- Concurrency: bus publish and persistence to `app/data.db` happen in the background using asyncio or threads, so the main workflow returns promptly.
- SQLite: avoid running multiple writers against the same DB in parallel to reduce lock contention.

