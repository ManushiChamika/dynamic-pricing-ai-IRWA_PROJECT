# Responsible AI

This project includes features and practices that support responsible AI usage in pricing.

## Transparency

- Activity Log: significant optimizer actions are recorded via `agent_sdk.activity_log` (when available) and displayed in the UI. Scraper availability is logged explicitly.
- Deterministic Fallbacks: when LLMs or tools are unavailable, the system falls back to simple, documented heuristics with clear rationale fields.

## Guardrails

- Margin floors: heuristic optimizer (`core/agents/price_optimizer/optimizer.py`) enforces a configurable minimum margin when cost is known.
- Bounds: recommended prices are clamped within provided min/max bounds.
- Optional thresholds: alerting service supports configurable thresholds that can generate incidents for undercut and demand spikes.

## Fairness and Non-Discrimination

- Inputs used are market tick data and cost/price fields; no protected attributes are used by the algorithms.
- If ML models are introduced, document features and perform bias checks.

## Privacy & Data Handling

- Local SQLite by default; no customer PII is persisted in demo flows.
- Do not log secrets. Use `.env` and never commit real keys.

## Security

- Passwords hashed with Argon2 in `core/auth_db.py` (see `core/auth_service.py`).
- Prefer moving to managed DBs and secret stores for production.

## Explainability

- Each `PriceProposal` includes a `reason` string documenting tool/algorithm selection and key inputs (e.g., mean competitor price, markup, bounds).
- When LLM is used, the prompt and decision summary can be retained in the activity log for audit (configurable).

## Human-in-the-Loop

- The system publishes `PriceProposal` events and persists proposals for review. Auto-apply should be opt-in and configurable, with audit logs retained.

## Compliance Checklist (Quick)

- Data minimization: Only pricing-relevant features are collected.
- User consent: Not applicable in the demo; in production ensure consent/ToS for scraping and data use.
- Auditability: Activity log and `price_proposals` table enable traceability.
- Safety: Rate-limit scraping, respect robots, and fail closed when policies are violated.

