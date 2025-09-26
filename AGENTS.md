AGENTS.md

- Build: `py -3.11 -m pip install -r requirements.txt`; frontend `cd frontend && npm install && npm run build`.
- Dev servers: backend `py -3.11 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000`; frontend `cd frontend && npm run dev` (see `run_both.bat` / `start_servers.ps1`).
- Tests (Python): repo uses ad-hoc smoke scripts under `scripts/`. Run a single check via `py -3.11 scripts/test_auto_apply.py`, `py -3.11 scripts/test_price_proposal_publish.py`, or `py -3.11 scripts/smoke_end_to_end.py`. UI import checks: `py -3.11 test_ui_integration.py`.
- Tests (JS): none defined; run Vite build as basic check: `cd frontend && npm run build`.
- Lint/format (Python): no configured linters. Follow PEP8 with 100-char lines; use type hints (PEP484/PEP561). Prefer `pathlib`, f-strings, and context managers; keep functions small and pure.
- Lint/format (TS/JS): `cd frontend && npm run lint` (ESLint 9). Typecheck via `npm run -w . tsc -b` or `npm run build`.
- Imports (Python): standard lib, then third-party, then local; absolute imports (e.g., `from core.agents...`), no wildcard imports. Group and alphabetize within groups.
- Naming: snake_case for variables/functions, PascalCase for classes, SCREAMING_SNAKE_CASE for constants; files and modules snake_case.
- Errors: raise specific exceptions; validate inputs early; never silence exceptions—log or return structured error dicts consistent with existing API patterns. For user-facing FastAPI, return `HTTPException` with clear messages; avoid leaking internals.
- Concurrency: prefer `async` APIs where existing modules are async (e.g., collectors). Use `asyncio.create_task` with cancellation and timeouts; do not block event loop with CPU or blocking I/O.
- Data access: use SQLite connections via context managers; ensure tables exist as in scripts; avoid SQL injection (use parameterized queries).
- Config/env: load via `python-dotenv`; see `.env.example`. Do not hardcode secrets; access `core.config` for LLM keys and URLs.
- Frontend style: use React 19 + Vite; keep components functional; co-locate styles; follow ESLint rules. Use `App.css`/Tailwind utilities consistently; avoid inline styles where possible.
- API design: FastAPI under `api/main.py`; define pydantic models; return typed responses; maintain consistent routes and error schemas.
- Commits/PRs: small, focused changes; descriptive messages; accompanying updates to scripts/docs as needed.
- Cursor/Copilot rules: none found (`.cursor/` or `.github/copilot-instructions.md` absent). If added later, follow them and update this file.
- Single-test tip: these scripts return exit codes; run one directly (above) or wrap with `pytest -q path::test_name` if pytest is introduced later.
