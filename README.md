# FluxPricer AI (Dynamic Pricing)

FluxPricer AI is a modular dynamic-pricing project with a Streamlit UI, a lightweight data collector, a pricing optimizer agent with LLM-assisted tool selection (OpenRouter/OpenAI), and an alerting service. It uses local SQLite for simple persistence so you can run end-to-end demos without external infra.

## Quick Start

- Python 3.11+ recommended.
- Create and activate a virtual environment.
- Install dependencies: `pip install -r requirements.txt`
- Copy `.env.example` to `.env` and set your API keys (OpenRouter preferred). The app works without LLM keys using deterministic fallbacks; LLM features will be disabled.
- Launch the Streamlit app: `streamlit run app/streamlit_app.py` or run `run_app.ps1` on Windows.

## Environment

- `.env` at repo root supports:
  - `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL`
  - `OPENAI_API_KEY`, `OPENAI_MODEL`
  - `DEBUG_LLM=1` to enable verbose LLM client logs
  - `SOUND_NOTIFICATIONS=0|1` optional UI setting

The UI loads `.env` via `python-dotenv`. The pricing/LLM code also implements a tiny internal loader, so LLM falls back gracefully if `python-dotenv` is absent.

## Run the App

- Windows: `\.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py` or double-click `run_app.ps1` after creating `.venv`.
- Cross-platform: `streamlit run app/streamlit_app.py` from an activated venv.

First load starts the Alert Service in the background; the sidebar shows the app entry. Pages live under `app/pages`.

## Data & Storage

- Authentication DB: `auth.db` at repo root, created via `core/auth_db.py`.
- Market/Optimizer DB (demo): `market.db` at repo root, used by scripts and pricing optimizer to store `market_data` and `pricing_list`.
- UI/Collector DB: `app/data.db` used by the data collector for `market_ticks`, `product_catalog`, `ingestion_jobs`, and `price_proposals`.

You can initialize the demo market DB:
- `python core/create_market_db.py`
- Insert sample ticks: `python scripts/insert_mock_market_data.py`

## LLM Usage

- Preferred: OpenRouter (`OPENROUTER_API_KEY`). Default model in `.env.example` is `z-ai/glm-4.5-air:free` when available.
- Fallback: OpenAI (`OPENAI_API_KEY`).
- No key: deterministic heuristic/tool selection and optimizer still work; scraping and LLM-based selection are disabled.

The Streamlit app uses `app/llm_client.py` which auto-detects provider and models. The optimizer’s `LLMBrain` selects tools and pricing algorithms; if no key is present, it uses transparent rules.

## Demos & Scripts

- Insert mock data then run one-shot optimizer:
  - `python scripts/insert_mock_market_data.py` (writes to `market.db`)
  - `python scripts/run_pricing_agent_once.py` (writes JSON outputs to `app/` and updates `pricing_list` in `market.db`)
- End-to-end smoke of collector + alerts:
  - `python scripts/smoke_end_to_end.py` (uses `app/data.db` internally)
- Data collector smoke (features path only):
  - `python scripts/smoke_data_collector.py`
- Auto Applier long-running demo:
  - `python scripts/run_auto_applier.py`

Note: `scripts/smoke_price_optimizer.py` is present as a placeholder and currently empty.

## Commercialization (Pitch)

- Problem: SMBs struggle to keep prices competitive across channels with limited data science resources.
- Solution: Plug-and-play pricing co-pilot with responsible guardrails, optional LLM reasoning, and transparent proposals.
- Target Users: DTC shops (Shopify/WooCommerce), marketplace sellers, and SMB retailers.
- Pricing Model: Tiered SaaS (Starter, Growth, Pro) with usage-based add-ons for data connectors and alerts.
- Differentiation: Local-first setup, graceful degradation without LLM, explicit explainability, and event-driven extensibility (MCP/tools).

## Progress Demo Checklist

- Install deps and initialize DBs.
- Run `python scripts/run_pricing_agent_once.py` and open the generated JSON in `app/`.
- Show `pricing_list` in `market.db` updated for a product (e.g., `iphone15`).
- Launch UI and navigate through Home → Alerts → Settings to show components working.
- Optional: Enable `DEBUG_LLM=1` to show reasoning path and tool selection in logs.

## Evaluation (How We Measure)

- Functional: `scripts/run_pricing_agent_once.py` updates `pricing_list`, emits proposal events, and writes JSON artifacts.
- Latency: ~0.4–1.2s (no LLM); ~1.5–4s (with LLM) on typical dev hardware.
- Quality: Compare recommended price to mean competitor price on mock data; aim within ±10% unless margin floors bind.
- Reliability: Deterministic fallback path ensures results without network/LLM.

## Viva Prep (What to Explain)

- System Architecture: Components, data flows, and scaling plan (see `docs/architecture.md`).
- Agent Roles & Communication: In-process bus, MCP endpoints, and how the optimizer selects tools.
- Responsible AI: Guardrails, transparency of `reason`, and audit logs (see `docs/responsible_ai.md`).
- Commercialization: Who pays, pricing tiers, and rollout plan.
- Demos: Run the one-shot script and show `pricing_list` updates; walk through UI pages.

## Troubleshooting

- Missing `openai` or `python-dotenv`: install from `requirements.txt`.
- LLM errors or unavailability: features fall back to deterministic selection; check `DEBUG_LLM=1` for logs.
- Windows path issues: prefer venv absolute path in `run_app.ps1`.
- SQLite locks: if running multiple scripts concurrently, avoid writing to the same DB files simultaneously.

## Repository Structure (high-level)

- `app/` Streamlit app + session and LLM client
- `core/agents/` Agents: pricing optimizer, data collector, alert service, agent SDK
- `scripts/` Smoke tests and runnable demos
- `docs/` Design and optimizer details

For deeper design and algorithm details, see `docs/architecture.md` and `docs/price_optimizer.md`.

## Contributors

- Add your team members here for grading visibility (Name, Student ID, role).
