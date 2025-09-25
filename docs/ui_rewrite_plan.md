# Dynamic Pricing AI — Greenfield UI Rewrite Plan

This document defines a complete plan to rebuild the user interface from first principles, guided by the existing backend domain (alerts engine, pricing optimizer, bus events, user interaction agent), while deliberately ignoring the current UI implementation. Backend logic and data contracts must not change; the UI will consume and orchestrate what already exists, adding only a thin client layer where necessary.

---

## 1. Scope and Goals

- Goal: Deliver a cohesive, production-grade UI for dynamic pricing operations: monitoring health and activity, managing incidents and rules, exploring markets, reviewing/applying price proposals, and collaborating via an AI assistant.
- Non-goals:
  - Modify core backend logic/algorithms.
  - Redesign data models or service responsibilities.
  - Add new external dependencies to core services. A thin UI client adapter in the UI layer is allowed if it only calls existing modules.
- Constraints:
  - Respect current backend domain and callable APIs (Python modules in `core.agents.*`).
  - Prefer read/write flows exposed by: alerts service (`list_incidents`, `ack_incident`, `resolve_incident`, `list_rules`, `create_rule`, `get_settings`, `save_settings`), activity log, pricing optimizer events, and existing user interaction agent.

---

## 2. Guiding Principles

- Domain-first: UI vocabulary matches backend entities and events.
- Observable by default: show what’s happening now (activity feed, optimizer stages, incidents).
- Clear, safe actions: destructive actions gated, with previews and diffs.
- Fast and legible: predictable navigation, clear information hierarchy, keyboard support, and dark/light themes.
- Progressive delivery: ship incrementally in feature slices with robust mocks.

---

## 3. Domain Primer (from backend)

- Alerts & Incidents (`core/agents/alert_service`)
  - Entities: `RuleSpec`, `RuleRecord`, `Alert`, `Incident`, channel settings, severity (info/warn/crit), status (OPEN/ACKED/RESOLVED).
  - APIs (async):
    - `list_incidents(status?)`
    - `ack_incident(id)`
    - `resolve_incident(id)`
    - `list_rules()` / `create_rule(spec)`
    - `get_settings()` / `save_settings(d)` (UI redacts secrets)
- Pricing Optimizer Bus (`core/agents/pricing_optimizer_bus/bus_events.py`)
  - Stages: `processing`, `checking_database`, `data_stale`, `updating_database`, `calculating_price`, `updating_pricing_list`, `notifying_alert_agent`, `done`, `error`.
- Market and Proposals (schemas)
  - `MarketTick(sku, our_price, competitor_price?, demand_index, ts)`
  - `PriceProposal(sku, proposed_price, margin, ts)`
- User Interaction Agent
  - Chat-like assistant used for explanations, commands and knowledge handoff.
- Activity Log (`core/agents/agent_sdk/activity_log`)
  - Recent high-level actions with status and optional details.

---

## 4. Users and Jobs-to-be-Done

- Pricing Ops Analyst
  - Monitor optimizer runs and outcomes, review proposals, apply/revert safely.
  - Investigate anomalies through incidents, acknowledge and resolve.
- Pricing Manager
  - Define and tune alerting rules and notification channels.
  - Track KPIs and trends; approve strategic price changes.
- Engineer/Operator
  - Observe system activity, health, and integration issues.
  - Triage errors and verify rule engine runtime status.

---

## 5. Information Architecture

- Global Shell
  - App bar: environment badge, user menu (profile, logout), global search.
  - Left navigation:
    - Dashboard
    - Market Explorer
    - Price Proposals
    - Alerts & Incidents
    - Rules
    - Jobs
    - Activity
    - Assistant
    - Settings

---

## 6. Screens and Core Flows

### 6.1 Dashboard
- Purpose: One-glance operational health + key KPIs.
- Content:
  - KPI tiles: total sales, average price, units sold (sourced or mocked where needed).
  - Optimizer Run Summary: latest runs with stage progress (map to bus events), duration, errors.
  - Incident snapshot: counts by status/severity; top critical items.
  - Trend charts: demand over time, price vs demand scatter.
  - Live Activity strip: most recent actions from activity log.
- Actions:
  - Click-through to detail views (runs, proposals, incidents).
- Acceptance:
  - Updates on new activity within <3s using periodic poll or background loop.

### 6.2 Market Explorer
- Purpose: Explore SKUs with current prices, competitor prices, demand signals.
- Content:
  - Data grid: SKU, our_price, competitor_price, demand_index, last updated.
  - Filters: search SKU, ranges, outliers, demand buckets.
  - SKU detail: mini time-series, related incidents, recent proposals.
- Actions:
  - Queue a manual proposal (form) for specific SKU (write to proposal store if available; otherwise mock now, wire later).
- Acceptance:
  - Default table loads <1.5s for 10k rows with virtualization.

### 6.3 Price Proposals
- Purpose: Review, approve, apply/revert proposals.
- Content:
  - Proposals table: SKU, proposed_price, margin, source (manual/optimizer), created_at, status.
  - Diff panel: current vs proposed; expected margin/volume impact; confidence.
  - Batch operations: approve N, apply N.
- Actions:
  - Approve, Apply, Revert with confirmation.
  - Export CSV of selected items.
- Acceptance:
  - Any apply/revert shows a precise audit trail and result notification.

### 6.4 Alerts & Incidents
- Purpose: Triage and resolve operational signals.
- Content:
  - Incident list with filters by status, severity, rule, SKU.
  - Incident detail: timeline, alert payload, group key, related rules and SKUs.
- Actions:
  - Ack/Resolve via `ack_incident`/`resolve_incident`.
  - Link out to Market Explorer and Proposals for the SKU.
- Acceptance:
  - State transitions reflected immediately and persisted.

### 6.5 Rules
- Purpose: Manage `RuleSpec` definitions and rule lifecycle.
- Content:
  - Rules list: id, source (MARKET_TICK | PRICE_PROPOSAL), severity, enabled.
  - Rule editor:
    - Choose source.
    - Either boolean `where` expression or named `detector` with `params`.
    - Optional: `field`, `hold_for`, `dedupe`, `group_by`, `notify` (channels + throttle + email/webhook args), `enabled`.
- Actions:
  - Create Rule: validates `where XOR detector` invariant; persists via `create_rule`.
  - Toggle enable/disable.
- Acceptance:
  - List reflects backend `list_rules()` verbatim; create persists and triggers `reload_rules()` internally.

### 6.6 Jobs
- Purpose: Run operational jobs ad-hoc and inspect recent runs.
- Content:
  - Job catalog (read-only mapping to existing scripts/entrypoints); recent runs with status.
- Actions:
  - Trigger a job with arguments (if supported) — optional if only via CLI today; can be simulated initially.
- Acceptance:
  - If direct calls are not available via modules, present read-only status first; upgrade later without UI redesign.

### 6.7 Activity
- Purpose: High-level internal actions feed.
- Content:
  - Reverse-chronological list: ts, agent, action, status, message, details JSON.
  - Filters: status, agent, text search.
- Acceptance:
  - Shows last 50–200 events; details lazy-rendered to keep UI fast.

### 6.8 Assistant
- Purpose: Conversational help, explanations, and shortcuts.
- Content:
  - Chat threads with titles, last message preview, pin/archive.
  - Message view: bubbles; pasteable code/JSON; copy-to-clipboard.
  - Context chips: links to incidents, rules, SKUs, proposals.
- Actions:
  - Ask question; store Q/A in current thread; persist threads per user.
  - Optional quick actions: "Generate alert rule from this incident", yielding pre-filled editor.
- Acceptance:
  - Streaming response display or single-shot with spinner; errors are friendly and retryable.

### 6.9 Settings
- Purpose: Configure channels for alerts; user profile.
- Content:
  - Alerts Channels Settings: via `get_settings()`/`save_settings(d)`; redact secrets.
  - Personal profile: name, email (read-only or editable based on current auth source).
- Acceptance:
  - Saving feedback with clear success/error; password fields masked.

---

## 7. Architecture (UI Layer Only)

- Technology: Python Streamlit (keeps integration with existing Python modules; zero backend changes). If a SPA is adopted later, the page/component structure and data contracts remain valid.
- Structure:
  - `app/ui/` (new folder) — domain-first UI modules and building blocks.
    - `components/` reusable UI widgets (tables, forms, charts, toasts, modals, timelines).
    - `views/` screen-level containers (Dashboard, Market, Proposals, Incidents, Rules, Jobs, Activity, Assistant, Settings, Auth).
    - `services/` thin adapters to backend modules (alerts, optimizer runs, proposals, activity, auth). No business logic.
    - `state/` view models and session coordination (Streamlit `session_state` wrappers).
    - `theme/` tokens, color schemes, spacing, typography.
  - Pages use `views/*` and compose `components/*` with service calls.

- Data Flow:
  - View triggers service call (async via background loop if needed).
  - Service invokes existing backend API (e.g., `core.agents.alert_service.api.*`).
  - Response normalized to ViewModel; UI renders.
  - Mutations update backend via service; UI invalidates cached data.

- Real-time/Background:
  - Background thread + asyncio event loop (pattern already used for alerts) centralised in `services/runtime.py`.
  - Polling for activity feed and incidents at 2–5s intervals, or push if/when event bus is expose-able without backend changes.

- Error Handling:
  - Central error boundary component: shows toast + inline details; classifies retryable vs permanent.
  - Network/service timeouts with sensible defaults (e.g., 10s).

- Security:
  - Reuse existing `auth_service`/`auth_db` for login/session gate.
  - Authorize actions client-side by role flags in session (if available from current auth), otherwise conservatively show only allowed controls.

---

## 8. Services (UI Adapters) — Contracts

These are thin wrappers living under `app/ui/services/`. They should only adapt inputs/outputs to friendly shapes.

- AlertsService
  - `list_incidents(status: Optional[str]) -> list[IncidentVM]`
  - `ack_incident(id: str) -> AckResult`
  - `resolve_incident(id: str) -> ResolveResult`
  - `list_rules() -> list[RuleSpec]`
  - `create_rule(spec: RuleSpec) -> CreateRuleResult`
  - `get_settings() -> ChannelSettingsVM`
  - `save_settings(d: ChannelSettingsVM) -> bool`

- ActivityService
  - `recent(limit: int = 100) -> list[ActivityItem]`

- OptimizerService
  - `recent_runs(limit: int = 20) -> list[RunVM]` (derive from bus events if accessible; otherwise mock until available)
  - `run_details(id: str) -> RunDetailVM`

- ProposalsService
  - `list() -> list[ProposalVM]` (load from repository or generate from optimizer output if available; else mock structure)
  - `approve(ids: list[str]) -> Result`
  - `apply(ids: list[str]) -> Result`
  - `revert(ids: list[str]) -> Result`

- MarketService
  - `list_skus(filters) -> list[SkuVM]` (maps to `MarketTick`-like data if available; else mock)
  - `sku_detail(sku: str) -> SkuDetailVM`

- AssistantService
  - `send(user_text: str, thread_id: str) -> AssistantMessage`
  - `list_threads() / create_thread() / rename_thread() / delete_thread()` persisted in per-user store (JSON or DB as currently used).

Notes:
- Where the backend does not expose a read endpoint yet, we start with deterministic mocks in the service layer so UI can be built and tested without backend changes.

---

## 9. Component System and Design

- Foundations
  - Color tokens: semantic (bg, card, accent, text-muted, critical, warning, info).
  - Type scale: h1–h6, body, code; consistent spacing grid.
  - Dark/Light modes toggle with persisted preference.

- Key Components
  - `KpiTile` with delta and trend sparkline.
  - `DataTable` with virtualization, column definitions, faceted filters.
  - `Form` primitives: input, select, checkbox, chips, syntax editor for rule `where` expressions.
  - `Timeline` for optimizer stages and incident events.
  - `DiffCard` for proposal diff (current vs proposed).
  - `Toast`/`InlineAlert` for feedback.
  - `JsonViewer` for payloads.

- Accessibility
  - WCAG AA contrast, proper roles and labels, focus states, keyboard nav for tables and dialogs.

---

## 10. State, Caching, and Performance

- Use a simple in-memory cache keyed by service + params within the Streamlit session to avoid redundant calls in a single render cycle.
- Debounce search inputs (300–500ms), virtualize large tables, and progressively render heavy sections (skeletons first).
- Keep background polling lightweight and cancel stale requests.

---

## 11. Observability & UX Diagnostics

- Activity Feed integrated across the app (inline context on pages).
- Client-side timing (fetch, render) logged to an internal console pane in dev mode.
- Error events include correlation id surfaced to the user.

---

## 12. Testing Strategy

- Unit: service adapters (pure functions), formatters, validators.
- Interaction: view actions (ack, resolve, save settings) with local mocks.
- Visual: screenshot diff testing on key screens (golden images) for critical layouts.
- Accessibility: automated axe checks on major pages (dev-only helper).

---

## 13. Delivery Plan (Phased)

- Phase 0 — Foundations (1 week)
  - Project structure under `app/ui/*`, theme tokens, shell and navigation, runtime loop helper, service adapter scaffolds with mocks.

- Phase 1 — Alerts & Incidents (1–2 weeks)
  - Incidents list/detail with ack/resolve wired to `alert_service.api`.
  - Channel settings read/write page.

- Phase 2 — Rules (1–2 weeks)
  - Rules list, create/edit with schema validation of `RuleSpec` (where XOR detector).

- Phase 3 — Activity & Dashboard (1–2 weeks)
  - Activity feed with filters; dashboard KPIs and trends; optimizer stage timeline (mock then wire).

- Phase 4 — Market Explorer (1–2 weeks)
  - Virtualized table, filters, SKU detail; propose manual price form (mock action).

- Phase 5 — Proposals (2 weeks)
  - Proposals list, diff view, approve/apply/revert actions (mock then wire to existing flows/CLIs if callable without changing core).

- Phase 6 — Assistant & Polish (1–2 weeks)
  - Threaded chat with per-user persistence; contextual links; theming + accessibility polish; documentation.

- Phase 7 — Hardening (ongoing)
  - Performance tuning, a11y passes, error simulations, edge cases.

Milestones are additive and can ship independently behind a flag or alternate route.

---

## 14. Cutover & Migration

- Run new UI side-by-side under `/new` route in Streamlit while legacy remains at root.
- Dogfood with Ops team for at least 1–2 weeks; instrument feedback.
- Gate switch: promote `/new` to default once feature parity reached for Alerts/Rules (critical operations).
- Keep legacy as fallback for one release cycle.

---

## 15. Risks & Mitigations

- Missing read APIs for some domains (e.g., proposals):
  - Mitigate with UI mocks; keep adapters thin so wiring later doesn’t ripple.
- Real-time expectations vs available signals:
  - Use periodic polling; if bus push is needed, plan a follow-up iteration (not part of this rewrite scope).
- Streamlit layout constraints for very dense tables:
  - Use optimized components and pagination/virtualization; if needed, offload heavy grids to a custom component.

---

## 16. Acceptance Criteria (V1)

- Alerts & Incidents: End-to-end ack/resolve and settings save with no backend changes.
- Rules: Create valid `RuleSpec`, list shows parity with backend, hot-reload triggered.
- Dashboard: Shows optimizer stage timeline (mock allowed) and live activity; KPIs present.
- Assistant: Threaded chat persisted per user; messages survive reload.
- Performance: <2s initial page load; <300ms average navigation.
- Accessibility: keyboard navigable, labeled controls, color contrast AA.

---

## 17. Appendix A — Example Service Adapters (Python)

```python
# app/ui/services/alerts.py
from core.agents.alert_service import api as alerts

async def list_incidents(status: str | None = None):
    return await alerts.list_incidents(status)

async def ack_incident(incident_id: str):
    return await alerts.ack_incident(incident_id)

async def resolve_incident(incident_id: str):
    return await alerts.resolve_incident(incident_id)

async def list_rules():
    return await alerts.list_rules()

async def create_rule(spec: dict):
    return await alerts.create_rule(spec)

async def get_settings():
    return await alerts.get_settings()

async def save_settings(d: dict):
    return await alerts.save_settings(d)
```

```python
# app/ui/services/activity.py
from core.agents.agent_sdk.activity_log import activity_log

def recent(limit: int = 100):
    return activity_log.recent(limit)
```

---

## 18. Appendix B — Wireframe Notes (Textual)

- Dashboard
  - [KPIs][Optimizer Runs][Incidents Summary]
  - [Price vs Demand Chart] [Demand Trend]
  - [Live Activity strip]

- Incidents List
  - Filters top bar; table with severity badge; action buttons (Ack/Resolve) right-aligned.

- Rule Editor
  - Source selector; tabs: "Where" | "Detector" (mutually exclusive). JSON preview panel on the right.

- Proposals
  - Master-detail: table at left, DiffCard at right; batch select above table.

- Assistant
  - Left: threads list with preview; Right: conversation; bottom input with send.

---

## 19. Appendix C — Glossary

- Incident: Aggregated manifestation of alerts from rules over grouped keys.
- RuleSpec: Declarative rule describing source, condition/detector, and notify behavior.
- Proposal: Suggested price change with margin and metadata.
- Activity: High-level log produced by agents during operations.

---

## 20. Next Steps

- Approve this plan and the phased delivery.
- Create `app/ui/` scaffolding and start Phase 0 foundations.
- Identify any missing read endpoints; confirm mock strategies.
