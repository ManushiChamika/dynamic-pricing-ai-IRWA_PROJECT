# Comprehensive Migration Plan: Library Modernization Initiative

## Guiding Principles
- Prefer mature, well-documented libraries over custom code
- Introduce **anti-corruption layers** (thin wrappers) to isolate external APIs
- Migrate **incrementally**: old and new systems coexist until validated
- Maintain **backward compatibility endpoints** until consumer parity achieved
- Instrument early: observability added before risky changes
- Every migration has: prerequisites, steps, acceptance criteria, rollback procedure
- Avoid big-bang rewrites; ensure each phase yields production value
- Preserve existing business logic semantics (pricing governance, agent workflows)

## High-Level Phases & Timeline (Estimated 8–10 Weeks)
| Phase | Weeks | Focus | Key Deliverables |
|-------|-------|-------|------------------|
| 1 | 1–2 | Foundation | pydantic-settings config, initial Zustand store, RHF+Zod on login form |
| 2 | 3–5 | Critical Services | fastapi-users auth (parallel), Blinker event bus, react-eventsource SSE, initial OpenTelemetry traces |
| 3 | 6–8 | Developer Velocity | LangChain LLM wrapper, FastCRUD repositories/endpoints, TanStack Query + Axios, TS type generation (@hey-api/openapi-ts) |
| 4 | 9–10 | Production Readiness | Async test harness (httpx), Vitest setup, full observability dashboards, deprecation of legacy layers |

## Dependency Graph (Simplified)
- Config precedes everything (env + settings used globally)
- Zustand auth store needed before SSE + TanStack Query
- fastapi-users must be in place before deprecating legacy auth endpoints
- Blinker bus must exist before OpenTelemetry cross-component tracing
- LangChain wrapper depends on config + observability, not on CRUD
- FastCRUD depends on stable auth + settings
- Type generation depends on stabilized OpenAPI spec (post-auth changes)

---
## 1. Configuration Migration (core/config.py → pydantic-settings)
### Goal
Replace ad-hoc `os.getenv` logic with `BaseSettings` for type-safe, centralized config.
### Prerequisites
- Install `pydantic-settings` (matching current Pydantic major version)
### Steps
1. Create `core/settings.py` with `AppSettings(BaseSettings)` enumerating all current env vars (scan usages).
2. Support `.env` loading via `SettingsConfigDict(env_file=".env", extra="allow")`.
3. Replace direct `os.getenv` calls with `get_settings().VARIABLE` accessor.
4. Add cached singleton `@lru_cache` accessor.
5. Update tests to monkeypatch settings via `settings._settings.model_copy(update={...})` or environment variable context.
### Acceptance Criteria
- All imports of legacy Config removed.
- Running app uses only `AppSettings` for env.
- No failing tests related to missing environment values.
### Rollback
- Revert to previous `core/config.py` and restore original imports.

---
## 2. Global Frontend State (Zustand)
### Goal
Introduce predictable global state (auth/session) replacing ad-hoc state patterns.
### Prerequisites
- Install `zustand`
### Steps
1. Create `src/store/authStore.ts` with token, user, and `setAuth`, `logout` actions.
2. Integrate into existing login flow after form migration (Section 3).
3. Replace any prop-drilling for auth with store selectors.
### Acceptance Criteria
- Auth token readable via store for SSE and Axios interceptors.
- No residual custom global state for auth.
### Rollback
- Revert new store file and reinstate prior state management logic.

---
## 3. Frontend Forms (React Hook Form + Zod)
### Goal
Reduce manual form logic, centralize validation.
### Prerequisites
- Install `react-hook-form`, `zod`, `@hookform/resolvers`
### Steps
1. Migrate login form: create `LoginSchema` (email + password), integrate `useForm` with `zodResolver`.
2. Add error display using Tailwind components.
3. Migrate registration and catalog/product forms iteratively.
4. Remove obsolete local validation utilities.
### Acceptance Criteria
- All forms use RHF + Zod.
- Manual onChange validation removed.
### Rollback
- Restore previous component versions from VCS.

---
## 4. Authentication (fastapi-users) – Parallel Rollout
### Goal
Replace custom Argon2 session system with `fastapi-users` while preserving session (non-JWT) semantics.
### Prerequisites
- Backup `data/auth.db`.
- Install: `fastapi-users`, `pwdlib[argon2]` (or ensure Argon2 hashing support), `sqlalchemy` compatible versions.
### Steps
1. Create new user model extending `SQLAlchemyBaseUserTable` with existing columns; add migration for any required extras.
2. Implement `get_user_db` adapter pointing to existing session.
3. Choose `CookieTransport` (session semantics) & `AuthenticationBackend` with database strategy.
4. Mount new auth router at `/api/v2/auth` alongside legacy.
5. Write migration script to validate legacy password hashes (argon2 verify).
6. Update frontend to use new endpoints selectively (feature flag `USE_V2_AUTH`).
7. After validation (≥95% successful logins), deprecate legacy endpoints and remove old code.
### Acceptance Criteria
- Users can authenticate via `/api/v2/auth/login`.
- Session cookie issued and recognized across protected routes.
- No password hash mismatches (audit log).
### Rollback
- Switch feature flag off; retain legacy endpoints; remove new router imports.

---
## 5. Event Bus (Blinker) → Future Redis Option
### Goal
Ensure reliable in-process pub-sub with error isolation; prepare for eventual distributed messaging.
### Prerequisites
- Install `blinker`.
### Steps
1. Introduce `core/events/signals.py` defining `signal("market_tick")` etc.
2. Replace custom bus publish calls with `signals.market_tick.send(payload=...)` style through wrapper.
3. Wrap async handlers: signal receiver schedules `asyncio.create_task(handler(payload))`.
4. Retain logging to `data/events.jsonl` via centralized receiver decorator.
5. Provide abstraction `EventBus` with Blinker backend; later add Redis backend implementing same interface.
### Acceptance Criteria
- All topics routed through new abstraction.
- Errors in a handler do not crash publisher; errors logged.
### Rollback
- Revert to previous `core/bus.py` and receiver registrations.

---
## 6. SSE Client (react-eventsource)
### Goal
Shrink custom 206 LOC SSE client; support auth headers properly.
### Prerequisites
- Install `react-eventsource`.
### Steps
1. Create hook `useChatStream(threadId)` using `<EventSource />` component or provided hook.
2. Inject headers from Zustand (`Authorization: Bearer <token>` if required or appropriate cookie strategy).
3. Map server events to internal types; remove buffering logic if library handles it.
4. Delete legacy `sseClient.ts` after parity validation.
### Acceptance Criteria
- All 7 event types received correctly.
- Reconnection works under simulated network drop.
### Rollback
- Reintroduce legacy client file and revert usages.

---
## 7. LLM Orchestration (LangChain Wrapper)
### Goal
Replace custom 428 LOC `llm_client.py` with thin abstraction over LangChain while maintaining failover, tool calling, streaming, cost tracking.
### Prerequisites
- Install: `langchain`, `langchain-core`, provider packages (`langchain-openai`, `langchain-community`, `google-generativeai`, optional `langchain-anthropic`), `tiktoken` (token counting), any OpenRouter integration (custom via API wrapper if not native).
- Define provider API keys in new settings.
### Steps
1. Create `core/llm/langchain_client.py` containing class `LangChainLLMClient`.
2. Implement model registry: ordered list of `(model_id, provider_type)` for failover.
3. Tool calling: Use `ChatOpenAI.bind_functions` or generic function tool pattern; wrap existing tool schema.
4. Streaming: Utilize `callback_manager` with custom handler forwarding deltas to SSE pipeline.
5. Cost tracking: For each call, collect token usage via LangChain usage metadata; map to cost table.
6. Failover strategy: On exception/timeouts, iterate to next provider (expose metrics).
7. Provide compatibility shim exposing original methods: `chat_with_tools_stream(...)`, `simple_completion(...)`.
8. Write tests comparing outputs of old client vs new for a fixed prompt (non-deterministic parts mocked).
9. Deprecate and eventually remove legacy file after parity.
### Acceptance Criteria
- All existing agent workflows operate unchanged through wrapper.
- Streaming events preserved (thinking, message delta, done).
- Tool calling yields identical tool invocation structure.
- Token/cost metrics recorded.
### Rollback
- Switch DI to legacy client; retain both implementations.

---
## 8. Database CRUD (FastCRUD / CRUDBase)
### Goal
Eliminate repetitive CRUD code while preserving custom behaviors (optimistic locking, decision logging).
### Prerequisites
- Install chosen CRUD library (`fastcrud` or similar).
### Steps
1. Introduce base repository wrapping library generics.
2. Migrate least critical module first (chat) to validate pattern.
3. Add extension methods for bespoke operations (e.g., compare-and-swap with version field).
4. Replace direct session operations in routers with repository methods.
5. Document repository interface in `docs/`.
### Acceptance Criteria
- CRUD endpoints rely on repository abstraction.
- Optimistic locking tests pass.
### Rollback
- Restore original repository code; keep DB schema unchanged.

---
## 9. Server State (TanStack Query + Axios)
### Goal
Standardize API calls, caching, and mutations; remove manual fetch wrappers.
### Prerequisites
- Install: `axios`, `@tanstack/react-query`, `@tanstack/react-query-devtools`.
### Steps
1. Create configured Axios instance with interceptor injecting auth token from Zustand.
2. Add React Query `QueryClient` provider at root.
3. Migrate one read hook (e.g., useCatalog) and one mutation hook (create product) to validate patterns.
4. Introduce optimistic update pattern for price proposals if applicable.
5. Remove legacy fetch wrappers after migration.
### Acceptance Criteria
- Network calls centralized in Axios instance.
- Cache invalidation patterns implemented for CRUD operations.
### Rollback
- Revert to previous fetch utilities and remove provider changes.

---
## 10. Type Safety (@hey-api/openapi-ts)
### Goal
Auto-generate TypeScript types and hooks from FastAPI `openapi.json`.
### Prerequisites
- Install dev dependency: `@hey-api/openapi-ts`.
### Steps
1. Add script `npm run generate:api` invoking CLI with flags for React Query hook generation (`--useQuery`).
2. Commit generated types to `frontend/src/api/generated/` (avoid editing manually).
3. Refactor manual types/usages to generated equivalents.
4. Add CI check: run generation and fail if diff found.
### Acceptance Criteria
- No manually maintained endpoint types remain.
- Hooks in use align with generated code.
### Rollback
- Remove generated folder; restore manual type files.

---
## 11. Backend Testing (httpx.AsyncClient + pytest-asyncio)
### Goal
Proper async test execution eliminating hidden concurrency issues.
### Prerequisites
- Install: `httpx`, `pytest-asyncio`.
### Steps
1. Add `@pytest.fixture(scope="session")` event loop in `conftest.py`.
2. Provide `async_client` fixture wrapping FastAPI app via `httpx.AsyncClient(app=app, base_url="http://test")`.
3. Convert streaming tests to async style.
4. Replace deprecated sync client usages.
### Acceptance Criteria
- All tests pass under `pytest -k` subsets and full run.
- No `RuntimeWarning: coroutine was never awaited` occurrences.
### Rollback
- Reinstate previous sync fixtures.

---
## 12. Frontend Testing (Vitest + RTL)
### Goal
Consistent component, hook, and interaction testing.
### Prerequisites
- Install: `vitest`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`, optional `msw`.
### Steps
1. Create `vitest.setup.ts` registering jest-dom and MSW handlers (if used).
2. Add test examples for form + SSE hook.
3. Integrate into CI pipeline (`npm run test`).
4. Remove obsolete test runner configs if any.
### Acceptance Criteria
- Coverage for migrated forms and hooks.
- Tests run in < N seconds threshold.
### Rollback
- Revert to previous test configuration.

---
## 13. Observability (OpenTelemetry + Prometheus + Grafana)
### Goal
End-to-end tracing and metrics for agents, API, LLM calls.
### Prerequisites
- Install: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp`, `opentelemetry-instrumentation-fastapi`, `prometheus-client`.
- Provision OTLP collector and Grafana dashboards (external infra).
### Steps
1. Initialize tracer provider early in app startup (before routers).
2. Instrument FastAPI with middleware for request spans.
3. Wrap event bus send/receive in spans (e.g., `event.publish`, `event.handle`).
4. Instrument LangChain wrapper: span around each provider attempt; add attributes `model`, `tokens_prompt`, `tokens_completion`, `latency_ms`.
5. Expose Prometheus metrics endpoint (`/metrics`).
6. Create Grafana dashboards: API latency, LLM cost/tokens, event throughput.
### Acceptance Criteria
- Traces show full path: HTTP → Agent → LLM → SSE.
- Metrics populated and visible in Grafana.
### Rollback
- Disable tracer initialization; remove middleware (keep logging fallback).

---
## 14. Type Generation + Endpoint CRUD Consolidation (FastCRUD + @hey-api synergy)
### Goal
Combine generated backend CRUD with generated frontend hooks to minimize boilerplate.
### Steps
1. After FastCRUD endpoint stabilization, regenerate `openapi.json`.
2. Run `generate:api` script; update affected hooks automatically.
3. Replace any manual mutation logic with generated hook usage.
### Acceptance Criteria
- Manual endpoint code significantly reduced (≥50%).
- Generated hooks functional in key views.
### Rollback
- Retain previous manual endpoints; skip regeneration diff enforcement.

---
## Risk Matrix Summary
| Component | Risk Level | Primary Risk | Mitigation |
|-----------|------------|--------------|------------|
| fastapi-users | High | Data migration errors | Parallel rollout + backup + staged verification |
| LangChain wrapper | Medium | Performance regression | Failover metrics + load tests + keep legacy client |
| Event Bus change | Medium | Missed async tasks | Wrapper scheduling + error logging + tests |
| FastCRUD | Medium | Loss of custom logic | Extension methods + focused tests |
| SSE client | Low | Header auth failures | Token validation tests + fallback toggle |
| Config migration | Low | Missing env variables | Diff checklist + fallback defaults |
| Observability | Medium | Overhead | Sampling + performance benchmarks |

---
## Environment & Dependency Changes (Initial Batch)
### Backend (pyproject/requirements)
Add (or verify):
- pydantic-settings
- fastapi-users
- pwdlib[argon2]
- blinker
- langchain, langchain-core, langchain-openai, langchain-community, google-generativeai, tiktoken
- fastcrud (or chosen CRUD lib)
- httpx
- pytest-asyncio
- opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp, opentelemetry-instrumentation-fastapi
- prometheus-client

### Frontend (package.json)
Add dev & prod deps:
- zustand
- react-hook-form
- zod
- @hookform/resolvers
- axios
- @tanstack/react-query, @tanstack/react-query-devtools
- react-eventsource
- @hey-api/openapi-ts (dev)
- vitest, @testing-library/react, @testing-library/user-event, @testing-library/jest-dom, msw (dev)

---
## Anti-Corruption Layer Patterns
| Area | Wrapper | Purpose |
|------|---------|---------|
| LLM | `LangChainLLMClient` | Preserve old API (stream & tools) |
| Event Bus | `EventBus` | Hide Blinker/Redis specifics |
| Repositories | `BaseRepo` | Centralize CRUD + custom methods |
| Config | `get_settings()` | Hide library-specific configuration retrieval |
| SSE | `useChatStream()` | Abstract underlying implementation |

Guideline: All new external libraries used only within wrappers; application code imports wrappers.

---
## Rollback Strategy (General Pattern)
1. Keep legacy implementation in place during initial deployment.
2. Route small traffic percentage (manual testing or feature flag) to new path.
3. Monitor logs, metrics, and traces for anomalies.
4. If issues arise, toggle flag off; capture diagnostics before reverting code.
5. Roll forward with fix—avoid oscillating repeatedly.

---
## Acceptance Test Blueprint (Representative Examples)
| Migration | Test Focus |
|-----------|------------|
| Config | All critical settings accessible; default fallback works |
| Auth | Legacy + new login success; session cookie present; permission checks intact |
| Event Bus | Subscriber error isolation; event logged; async task executes |
| LLM | Streaming events ordering; tool invocation schema; failover path executed on forced error |
| CRUD Repo | Optimistic lock conflict triggers retry or error; transaction rollbacks function |
| SSE Client | Reconnect after forced network drop; auth header attached |
| React Forms | Validation messages appear; form resets succeed; performance (no re-render storm) |
| Query Layer | Cache invalidation after mutation; parallel queries deduped |
| Type Generation | Generated types match schema; compile passes with no manual types |
| Observability | Trace spans assembled correctly; metrics counters increment |

---
## Operational Checklist Per Migration
- Branch policy: (No branches per repo policy) commit locally with clear messages.
- Pre-migration: list files to touch; verify tests covering them.
- Post-migration: run targeted tests; inspect logs; capture performance baseline.
- Documentation: update related `docs/` file; link to migration plan section.

---
## Weekly Work Breakdown (Indicative)
Week 1: Config migration, login form (RHF+Zod), create auth Zustand store
Week 2: Remaining critical forms, initial QueryClient + Axios setup
Week 3: fastapi-users parallel endpoints, password hash verification scripts
Week 4: Blinker event bus integration + SSE client migration + initial traces
Week 5: Deprecate legacy auth gradually; expand tracing + metrics
Week 6: LangChain wrapper + parity tests; begin FastCRUD for chat
Week 7: FastCRUD for market/auth; TanStack Query full adoption; remove old fetch code
Week 8: Type generation integration + CI check; refine LLM cost tracking
Week 9: Async test harness conversion; Vitest suite + SSE/form tests
Week 10: Observability dashboards finalization; remove deprecated legacy components

---
## Tracking & Metrics
- LOC delta per migration (record pre/post in commit messages)
- Mean latency for LLM calls per provider
- Event bus delivery success vs handler errors
- Auth success/failure ratio between v1 and v2 during parallel phase
- Cache hit ratio (TanStack Query devtools metrics)
- Form validation error frequency (optional analytics)
- Trace completeness percentage (presence of all expected spans)

---
## Final Decommissioning Checklist
- Remove legacy `llm_client.py` after 2 weeks stable metrics
- Remove legacy auth endpoints after 100% traffic on v2 for 1 week
- Delete custom SSE client after no reconnect issues reported
- Archive deprecated CRUD helper files
- Update README and architecture docs to reflect new stack

---
## Next Immediate Actions
1. Implement `AppSettings` (pydantic-settings)
2. Scaffold LangChain wrapper interface (empty methods calling pass) for incremental fill
3. Create login form migration using RHF + Zod
4. Add Zustand auth store

---
This plan provides a structured, incremental pathway to modernize the codebase while honoring reliability and rollback safety. Proceed with Phase 1 tasks and instrument changes early to maximize observability and control.
