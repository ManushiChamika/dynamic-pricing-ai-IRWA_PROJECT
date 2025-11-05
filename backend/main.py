import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from core.chat_db import init_chat_db, cleanup_empty_threads
from core.auth_db import init_db
from core.auth_service import validate_session_token
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.routers import auth, settings, threads, messages, streaming, prices, catalog, alerts, debug, collector, responsible_ai

from core.agents.alert_service import api as alert_api
from core.agents.price_optimizer.agent import PricingOptimizerAgent
from core.agents.data_collector.agent import DataCollectorAgent
from core.agents.data_collector.repo import DataRepo
from core.agents.data_collector.collector import DataCollector


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_chat_db()
    cleanup_empty_threads()
    
    if os.environ.get("EXPORT_OPENAPI_ONLY", "0") in {"1", "true", "yes", "on"}:
        yield
        return
    try:
        pricing_optimizer = PricingOptimizerAgent()
    except Exception:
        pricing_optimizer = None
    
    try:
        from core.config import resolve_app_db
        db_path = resolve_app_db()
        data_collector_repo = DataRepo(db_path)
        await data_collector_repo.init()
        reactive_collector = DataCollector(data_collector_repo)
        app.state.reactive_collector = reactive_collector
        data_collector = DataCollectorAgent(
            repo=data_collector_repo,
            check_interval_seconds=180
        )
    except Exception:
        data_collector = None
    
    await alert_api.start()
    if pricing_optimizer is not None:
        await pricing_optimizer.start()
    if data_collector is not None:
        await data_collector.start()
    
    yield


app = FastAPI(title="FluxPricer Auth + Chat API", lifespan=lifespan)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


@app.get("/", response_class=HTMLResponse)
def root_index():
    try:
        return HTMLResponse((FRONTEND_DIST / "index.html").read_text(encoding="utf-8"))
    except Exception:
        return HTMLResponse("<h1>FluxPricer API</h1><p>Frontend not built. Run: cd frontend && npm run build</p>")


try:
    init_db()
    init_chat_db()
except Exception:
    pass


# Capture the original host environment value for UI_REQUIRE_LOGIN so pytest can override it
_ORIG_UI_REQUIRE_LOGIN = os.environ.get("UI_REQUIRE_LOGIN")


def _require_login_enabled() -> bool:
    try:
        if os.getenv("PYTEST_CURRENT_TEST") is not None:
            return os.environ.get("UI_REQUIRE_LOGIN", "").lower() in {"1", "true", "yes", "on"}

        if _ORIG_UI_REQUIRE_LOGIN is not None:
            try:
                return _ORIG_UI_REQUIRE_LOGIN.lower() in {"1", "true", "yes", "on"}
            except Exception:
                return False

        return False
    except Exception:
        return False



def _extract_token_from_request(request: Request) -> str | None:
    try:
        token = request.query_params.get("token")
        if token:
            return token
        auth = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            return auth.split(" ", 1)[1].strip()
        cookie = request.cookies.get("fp_session")
        if cookie:
            return cookie
    except Exception:
        pass
    return None


class ChatAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not _require_login_enabled():
            return await call_next(request)
        path = request.url.path or ""
        if path.startswith("/api/login") or path.startswith("/api/register") or path.startswith("/api/me") or path.startswith("/api/settings"):
            return await call_next(request)
        if path.startswith("/api/threads") or path.startswith("/api/messages"):
            token = _extract_token_from_request(request)
            try:
                sess = validate_session_token(token) if token else None
            except Exception as e:
                print(f"Token validation error: {e}")
                sess = None
            if not sess:
                return JSONResponse({"error": "Authentication required"}, status_code=401)
        return await call_next(request)


app.add_middleware(ChatAuthMiddleware)

app.include_router(auth.router)
app.include_router(settings.router)
app.include_router(threads.router)
app.include_router(messages.router)
app.include_router(streaming.router)
app.include_router(prices.router)
app.include_router(catalog.router)
app.include_router(alerts.router)
app.include_router(debug.router)
app.include_router(collector.router)
app.include_router(responsible_ai.router)
