from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

# Backend services
from core.db import init_db
from core.auth_service import (
    authenticate,
    create_persistent_session,
    validate_session_token,
    revoke_session_token,
    get_profile,
    register_user,
)
from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
from core.agents.analytics import insights as analytics
from core.agents.alert_service import api as alert_api

# ---------- App setup ----------
app = FastAPI(title="IRWA Dynamic Pricing API", version="0.1")

# Allow local dev frontend
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Resolve project root and DB paths
ROOT = Path(__file__).resolve().parents[1]
DATA_DB = str(ROOT / "app" / "data.db")

# In-memory per-session chat agents (simple demo storage)
_agent_by_token: Dict[str, UserInteractionAgent] = {}


# ---------- Models ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ChatIn(BaseModel):
    message: str


class ChatOut(BaseModel):
    reply: str


# ---------- Dependencies ----------

def get_token_from_auth_header(request: Request) -> str:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    return auth.split(" ", 1)[1].strip()


def current_session(request: Request) -> Dict[str, Any]:
    token = get_token_from_auth_header(request)
    sess = validate_session_token(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return sess


# ---------- Startup ----------
@app.on_event("startup")
async def _startup() -> None:
    # Ensure relational DB tables exist for auth/session
    init_db()
    # Initialize alert engine singletons (idempotent)
    # try:
    #     await alert_api.start()
    # except Exception:
    #     # Keep API available even if alerts can't start
    #     pass


# ---------- Auth ----------
@app.post("/api/auth/register")
def http_register(payload: RegisterIn):
    res = register_user(payload.model_dump())
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail=res.get("error") or "Registration failed")
    return {"ok": True}


@app.post("/api/auth/login")
def http_login(payload: LoginIn):
    user = authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token, expires = create_persistent_session(user_id=user["user_id"], days=7)
    return {"token": token, "expires": expires.isoformat()}


@app.get("/api/auth/me")
def http_me(sess: Dict[str, Any] = Depends(current_session)):
    prof = get_profile(sess["user_id"]) or {}
    return {"user": prof}


@app.post("/api/auth/logout")
def http_logout(sess: Dict[str, Any] = Depends(current_session)):
    ok = revoke_session_token(sess["token"]) if "token" in sess else False
    # Best-effort: also drop any agent memory for this token
    try:
        token = sess.get("token")
        if token and token in _agent_by_token:
            del _agent_by_token[token]
    except Exception:
        pass
    return {"ok": bool(ok)}


# ---------- Chat ----------
@app.post("/api/chat", response_model=ChatOut)
def http_chat(payload: ChatIn, sess: Dict[str, Any] = Depends(current_session)):
    token = sess.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Invalid session")

    agent = _agent_by_token.get(token)
    if agent is None:
        # Use email as user_name for a friendlier context
        prof = get_profile(sess["user_id"]) or {}
        user_name = prof.get("email") or f"user-{sess['user_id']}"
        agent = UserInteractionAgent(user_name=user_name)
        _agent_by_token[token] = agent

    try:
        reply = agent.get_response(payload.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ChatOut(reply=reply)


# ---------- Analytics ----------
@app.get("/api/analytics/trending")
async def http_trending(days: int = 7, limit: int = 5, ascending: bool = False):
    try:
        rows = await analytics.top_trending_by_volume(DATA_DB, days=days, limit=limit, ascending=ascending)
        return {"items": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/movers")
async def http_movers(days: int = 7, limit: int = 5):
    try:
        rows = await analytics.top_price_movers(DATA_DB, days=days, limit=limit)
        return {"items": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/pressure")
async def http_pressure(days: int = 7, limit: int = 5):
    try:
        rows = await analytics.highest_competitor_pressure(DATA_DB, days=days, limit=limit)
        return {"items": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/latest")
async def http_latest(sku: str, market: str = "DEFAULT"):
    try:
        row = await analytics.latest_price_for(DATA_DB, sku=sku, market=market)
        return {"item": row}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/stats")
async def http_stats(sku: str, days: int = 7, market: str = "DEFAULT"):
    try:
        row = await analytics.stats_for_period(DATA_DB, sku=sku, days=days, market=market)
        return {"item": row}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Health ----------
@app.get("/api/health")
def http_health():
    return {"ok": True}


# Friendly error handler to keep JSON surface neat
@app.exception_handler(HTTPException)
async def http_exc_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
