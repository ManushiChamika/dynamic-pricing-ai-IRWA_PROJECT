from fastapi import FastAPI, HTTPException, Response, Cookie, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional, List, Dict, Any
from core.chat_db import (
    init_chat_db,
    create_thread as db_create_thread,
    add_message as db_add_message,
    list_threads as db_list_threads,
    get_thread_messages as db_get_thread_messages,
    get_message as db_get_message,
    update_message as db_update_message,
    delete_message as db_delete_message,
    update_thread as db_update_thread,
    delete_thread as db_delete_thread,
    cleanup_empty_threads,
    SessionLocal,
    get_latest_summary as db_get_latest_summary,
    add_summary as db_add_summary,
)
from core.chat_db import Thread as ChatThread, Message as ChatMessage
from core.chat_db import Summary as ChatSummary
from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
from core.auth_db import init_db

from core.auth_service import (
    RegisterIn,
    register_user,
    authenticate,
    create_persistent_session,
    validate_session_token,
    revoke_session_token,
)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_chat_db()
    cleanup_empty_threads()
    yield

app = FastAPI(title="FluxPricer Auth + Chat API", lifespan=lifespan)
 
# CORS for local React dev on any localhost/127.0.0.1 port
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static chat UI if present
BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"
if UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(UI_DIR)), name="ui")

@app.get("/", response_class=HTMLResponse)
def root_index():
    try:
        return HTMLResponse((UI_DIR / "index.html").read_text(encoding="utf-8"))
    except Exception:
        return HTMLResponse("<h1>FluxPricer API</h1><p>Open /ui for the chat UI.</p>")

# Eager DB initialization for test environments where startup may not run
try:
    init_db()
    init_chat_db()
except Exception:
    pass



# ---------- Utility: LLM cost + metadata helpers ----------

def _default_price_map() -> Dict[str, Dict[str, float]]:
    # Per-1K token prices in USD for a few common models (override via LLM_PRICE_MAP)
    return {
        "openai:gpt-4o-mini": {"in": 0.005, "out": 0.015},
        "openai:gpt-4o": {"in": 0.01, "out": 0.03},
        "gemini:gemini-2.0-flash": {"in": 0.0005, "out": 0.0015},
        "openrouter:deepseek/deepseek-r1-0528:free": {"in": 0.0, "out": 0.0},
        "openrouter:z-ai/glm-4.5-air:free": {"in": 0.0, "out": 0.0},
    }


def _load_price_map() -> Dict[str, Dict[str, float]]:
    import os, json
    raw = os.getenv("LLM_PRICE_MAP")
    if not raw:
        return _default_price_map()
    try:
        data = json.loads(raw)
        out: Dict[str, Dict[str, float]] = {}
        for k, v in (data.items() if isinstance(data, dict) else []):
            if isinstance(v, dict) and "in" in v and "out" in v:
                out[str(k)] = {"in": float(v["in"]), "out": float(v["out"])}
        return out or _default_price_map()
    except Exception:
        return _default_price_map()


def _compute_cost_usd(provider: Optional[str], model: Optional[str], token_in: Optional[int], token_out: Optional[int]) -> Optional[str]:
    try:
        if not provider or not model or token_in is None or token_out is None:
            return None
        key = f"{provider}:{model}"
        pm = _load_price_map()
        price = pm.get(key) or pm.get(model)  # allow model-only keys
        if not price:
            return None
        cin = (token_in or 0) / 1000.0 * float(price.get("in", 0.0))
        cout = (token_out or 0) / 1000.0 * float(price.get("out", 0.0))
        return f"{cin + cout:.4f}"
    except Exception:
        return None


def _derive_agents_from_tools(tools_used: Optional[List[str]]) -> List[str]:
    if not tools_used:
        return []
    mapping = {
        "run_pricing_workflow": "PricingOptimizerAgent",
        "optimize_price": "PricingOptimizerAgent",
        "scan_for_alerts": "AlertNotificationAgent",
        "collect_market_data": "DataCollectionAgent",
        "request_market_fetch": "MarketCollector",
    }
    agents: List[str] = []
    for t in tools_used:
        name = mapping.get(t)
        if name and name not in agents:
            agents.append(name)
    return agents


# ---------- Context assembly + summarization helpers ----------

def _env_int(name: str, default: int) -> int:
    try:
        import os
        return int(os.getenv(name, str(default)) or default)
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        import os
        return float(os.getenv(name, str(default)) or default)
    except Exception:
        return default


def _assemble_memory(thread_id: int) -> List[Dict[str, str]]:
    """Build memory with summary + recent tail to control context size."""
    msgs = db_get_thread_messages(thread_id)
    mem: List[Dict[str, str]] = []

    # Environment-tunable caps
    # Use a high default for pre-summary history to approximate full context
    max_msgs = _env_int("UI_HISTORY_MAX_MSGS", 200)
    tail_after_summary = _env_int("UI_HISTORY_TAIL_AFTER_SUMMARY", 12)

    # Try to include latest summary first
    latest = db_get_latest_summary(thread_id)
    cutoff_id = 0
    if latest and latest.content:
        mem.append({
            "role": "system",
            "content": f"Conversation summary up to message {latest.upto_message_id}:\n" + str(latest.content)
        })
        cutoff_id = int(latest.upto_message_id or 0)

    # Add tail messages after cutoff, capped by count
    tail: List[ChatMessage] = [m for m in msgs if m.id > cutoff_id and m.role in ("system", "user", "assistant")]
    # If no summary or very short, allow up to max_msgs, otherwise use smaller tail
    cap = max_msgs if cutoff_id == 0 else tail_after_summary
    for m in tail[-cap:]:
        mem.append({"role": m.role, "content": m.content})

    # If still empty (no messages), fall back to full tiny history
    if not mem:
        for m in msgs[-max_msgs:]:
            if m.role in ("system", "user", "assistant"):
                mem.append({"role": m.role, "content": m.content})

    return mem


def _should_summarize(thread_id: int, upto_message_id: int, token_in: Optional[int], token_out: Optional[int]) -> bool:
    import random
    msgs = db_get_thread_messages(thread_id)
    latest = db_get_latest_summary(thread_id)
    since = [m for m in msgs if m.id <= upto_message_id and (latest is None or m.id > int(latest.upto_message_id))]

    # Env knobs
    min_msgs = _env_int("UI_SUMMARIZE_AFTER_MSGS", 12)
    long_thread = _env_int("UI_LONG_THREAD_MSGS", 20)
    prob = _env_float("UI_SUMMARIZE_PROB", 0.25)
    token_trigger = _env_int("UI_SUMMARIZE_TOKEN_TRIGGER", 2000)

    if len(since) >= min_msgs:
        return True
    if (token_in or 0) + (token_out or 0) >= token_trigger:
        return True
    if len(msgs) >= long_thread and random.random() < prob:
        return True
    return False


def _generate_summary(thread_id: int, upto_message_id: int) -> Optional[str]:
    """Best-effort: summarize messages since the last summary up to given id."""
    try:
        from core.agents.llm_client import get_llm_client
    except Exception:
        get_llm_client = None  # type: ignore[assignment]

    msgs = db_get_thread_messages(thread_id)
    latest = db_get_latest_summary(thread_id)
    start_id = int(latest.upto_message_id) if latest else 0
    segment = [m for m in msgs if m.id > start_id and m.id <= upto_message_id]
    if len(segment) < 4:  # too few to bother
        return None

    # Build a compact transcript
    lines: List[str] = []
    for m in segment[-50:]:  # cap transcript length
        role = m.role
        text = m.content.replace("\n", " ")
        if len(text) > 400:
            text = text[:400] + "..."
        lines.append(f"{role}: {text}")
    transcript = "\n".join(lines)

    # If no LLM available, skip silently
    if get_llm_client is None:
        return None
    try:
        import os as _os
        summary_model = _os.getenv("SUMMARIZER_MODEL")
        llm = get_llm_client(model=summary_model) if summary_model else get_llm_client()
        if not llm.is_available():
            return None
        system = (
            "You are a helpful assistant creating a rolling, concise conversation summary. "
            "Write 5-8 bullet points capturing key decisions, requests, tool results, and context. "
            "Keep it factual and under 180 words."
        )
        prompt = (
            "Summarize the following chat segment to help future turns continue without full history.\n\n" + transcript
        )
        content = llm.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ], max_tokens=220, temperature=0.2)
        return content
    except Exception:
        return None


# ---------- Auth & Session Models ----------

class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str | None = None  # maps to full_name for now


class LoginRequest(BaseModel):
    email: str
    password: str


class LogoutRequest(BaseModel):
    token: str | None = None


# ---------- Chat Models ----------

class CreateThreadRequest(BaseModel):
    title: Optional[str] = None


class UpdateThreadRequest(BaseModel):
    title: Optional[str] = None


class PostMessageRequest(BaseModel):
    user_name: str
    content: str
    # Optional: allow client to pass parent_id for branching in future
    parent_id: Optional[int] = None


class ThreadOut(BaseModel):
    id: int
    title: str
    created_at: str


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    model: Optional[str] = None
    token_in: Optional[int] = None
    token_out: Optional[int] = None
    cost_usd: Optional[str] = None
    api_calls: Optional[int] = None
    agents: Optional[Dict[str, Any]] = None
    tools: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str


class EditMessageRequest(BaseModel):
    content: str
    branch: bool = True  # if true, create a new assistant reply branch


class DeleteMessageResponse(BaseModel):
    ok: bool


class ThreadExport(BaseModel):
    thread: Dict[str, Any]
    messages: List[Dict[str, Any]]


class ThreadImportMessage(BaseModel):
    id: Optional[int] = None  # original id from export for parent mapping
    role: str
    content: str
    model: Optional[str] = None
    token_in: Optional[int] = None
    token_out: Optional[int] = None
    cost_usd: Optional[str] = None
    agents: Optional[Dict[str, Any]] = None
    tools: Optional[Dict[str, Any]] = None
    api_calls: Optional[int] = None
    parent_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ThreadImportRequest(BaseModel):
    title: Optional[str] = None
    owner_id: Optional[int] = None
    messages: List[ThreadImportMessage] = []


# ---------- Optional auth gating ----------

def _require_login_enabled() -> bool:
    try:
        import os
        return (os.getenv("UI_REQUIRE_LOGIN", "0").lower() in {"1","true","yes","on"})
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

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class ChatAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not _require_login_enabled():
            return await call_next(request)
        path = request.url.path or ""
        # Allow auth and settings endpoints without token
        if path.startswith("/api/login") or path.startswith("/api/register") or path.startswith("/api/me") or path.startswith("/api/settings"):
            return await call_next(request)
        # Protect chat threads/messages endpoints
        if path.startswith("/api/threads") or path.startswith("/api/messages"):
            token = _extract_token_from_request(request)
            sess = validate_session_token(token) if token else None
            if not sess:
                return JSONResponse({"error": "Authentication required"}, status_code=401)
        return await call_next(request)

# Register middleware
app.add_middleware(ChatAuthMiddleware)

# ---------- Settings (in-memory, token-based) ----------

class Settings(BaseModel):
    show_model_tag: bool = True
    show_timestamps: bool = False
    show_metadata_panel: bool = False
    show_thinking: bool = False
    theme: str = "dark"  # dark | light
    streaming: str = "sse"  # sse | ws
    mode: str = "user"  # user | developer


SETTINGS_STORE: Dict[int, Dict[str, Any]] = {}


def _default_settings() -> Dict[str, Any]:
    import os
    dev = (os.getenv("DEV_MODE", "0").lower() in {"1", "true", "yes", "on"})
    return {
        "show_model_tag": True,
        "show_timestamps": bool(dev),
        "show_metadata_panel": bool(dev),
        "show_thinking": bool(dev),
        "theme": "dark",
        "streaming": "sse",
        "mode": "user",
    }


def _get_user_settings(token: Optional[str]) -> Dict[str, Any]:
    user_id: Optional[int] = None
    if token:
        sess = validate_session_token(token)
        user_id = int(sess["user_id"]) if sess else None
    if user_id is not None and user_id in SETTINGS_STORE:
        return SETTINGS_STORE[user_id]
    return _default_settings()





@app.post("/api/register")
def api_register(req: RegisterRequest):
    try:
        register_user(RegisterIn(email=req.email, full_name=req.username, password=req.password))
        # Create a session on successful registration
        user = authenticate(req.email, req.password)
        token, expires_at = create_persistent_session(user_id=user["user_id"])
        return {"ok": True, "token": token, "user": user, "expires_at": expires_at.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/login")
def api_login(req: LoginRequest):
    try:
        user = authenticate(req.email, req.password)
        token, expires_at = create_persistent_session(user_id=user["user_id"])
        return {"ok": True, "token": token, "user": user, "expires_at": expires_at.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/me")
def api_me(token: str):
    sess = validate_session_token(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"ok": True, "user": sess}


@app.post("/api/logout")
def api_logout(req: LogoutRequest, response: Response, fp_session: str | None = Cookie(default=None)):
    token = req.token or fp_session
    if not token:
        raise HTTPException(status_code=400, detail="No session token provided")
    revoke_session_token(token)
    response.delete_cookie("fp_session", path="/")
    return {"ok": True}


# ---------- Settings Endpoints ----------

@app.get("/api/settings")
def api_get_settings(token: Optional[str] = None):
    return {"ok": True, "settings": _get_user_settings(token)}


class UpdateSettingsRequest(BaseModel):
    token: Optional[str] = None
    settings: Dict[str, Any]


@app.put("/api/settings")
def api_update_settings(req: UpdateSettingsRequest):
    sess = validate_session_token(req.token) if req.token else None
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    uid = int(sess["user_id"])  # type: ignore[index]
    # Merge with defaults, then override with provided
    cur = SETTINGS_STORE.get(uid, _default_settings())
    # Only allow keys that exist in defaults
    allowed = _default_settings().keys()
    cur.update({k: v for k, v in req.settings.items() if k in allowed})
    SETTINGS_STORE[uid] = cur
    return {"ok": True, "settings": cur}


# ---------- Chat Endpoints ----------

@app.post("/api/threads", response_model=ThreadOut)
def api_create_thread(req: CreateThreadRequest, token: Optional[str] = None):
    owner_id = None
    if token:
        sess = validate_session_token(token)
        if sess:
            owner_id = sess["user_id"]
    t = db_create_thread(title=req.title, owner_id=owner_id)
    return ThreadOut(id=t.id, title=t.title, created_at=t.created_at.isoformat())


@app.patch("/api/messages/{message_id}", response_model=MessageOut)
def api_edit_message(message_id: int, req: EditMessageRequest):
    m = db_get_message(message_id)
    if not m:
        raise HTTPException(status_code=404, detail="Message not found")
    if m.role != "user":
        raise HTTPException(status_code=400, detail="Only user messages can be edited")
    # Update content
    m = db_update_message(message_id, content=req.content)
    # When branching, the next assistant message should be regenerated by client calling POST /messages
    return MessageOut(id=m.id, role=m.role, content=m.content, model=m.model, created_at=m.created_at.isoformat())


@app.delete("/api/messages/{message_id}", response_model=DeleteMessageResponse)
def api_delete_message(message_id: int):
    ok = db_delete_message(message_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Message not found")
    return DeleteMessageResponse(ok=True)


@app.get("/api/threads/{thread_id}/export", response_model=ThreadExport)
def api_export_thread(thread_id: int):
    msgs = db_get_thread_messages(thread_id)
    # Load thread record for metadata
    thread_info: Dict[str, Any] = {"id": thread_id}
    try:
        with SessionLocal() as db:
            t = db.get(ChatThread, thread_id)
            if t:
                thread_info = {
                    "id": t.id,
                    "title": t.title,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
    except Exception:
        pass
    # Build portable messages
    out_msgs: List[Dict[str, Any]] = []
    for m in msgs:
        item: Dict[str, Any] = {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "model": m.model,
            "token_in": m.token_in,
            "token_out": m.token_out,
            "cost_usd": m.cost_usd,
            "api_calls": m.api_calls,
            "parent_id": m.parent_id,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        # parse json fields if present
        try:
            if m.agents:
                item["agents"] = __import__("json").loads(m.agents)
        except Exception:
            item["agents"] = None
        try:
            if m.tools:
                item["tools"] = __import__("json").loads(m.tools)
        except Exception:
            item["tools"] = None
        try:
            if m.meta:
                item["metadata"] = __import__("json").loads(m.meta)
        except Exception:
            item["metadata"] = None
        out_msgs.append(item)
    return ThreadExport(thread=thread_info, messages=out_msgs)


@app.post("/api/threads/import", response_model=ThreadOut)
def api_import_thread(req: ThreadImportRequest):
    # Create new thread
    t = db_create_thread(title=req.title, owner_id=req.owner_id)
    # Insert messages preserving parent ordering (assumes input either ordered or parent_id references prior)
    id_map: Dict[int, int] = {}
    import json as _json
    for msg in req.messages:
        agents = _json.dumps(msg.agents) if msg.agents is not None else None
        tools = _json.dumps(msg.tools) if msg.tools is not None else None
        metadata = _json.dumps(msg.metadata) if msg.metadata is not None else None
        parent_id = id_map.get(int(msg.parent_id)) if msg.parent_id is not None and int(msg.parent_id) in id_map else None
        m = db_add_message(
            thread_id=t.id,
            role=msg.role,
            content=msg.content,
            model=msg.model,
            token_in=msg.token_in,
            token_out=msg.token_out,
            cost_usd=msg.cost_usd,
            agents=agents,
            tools=tools,
            api_calls=msg.api_calls,
            parent_id=parent_id,
            meta=metadata,
        )
        # Map original id (if provided) to new id for subsequent parent references
        if msg.id is not None:
            id_map[int(msg.id)] = m.id
    return ThreadOut(id=t.id, title=t.title, created_at=t.created_at.isoformat())


@app.get("/api/threads", response_model=List[ThreadOut])
def api_list_threads(token: Optional[str] = None):
    owner_id = None
    if token:
        sess = validate_session_token(token)
        if sess:
            owner_id = sess["user_id"]
    rows = db_list_threads(owner_id=owner_id)
    return [ThreadOut(id=t.id, title=t.title, created_at=t.created_at.isoformat()) for t in rows]


@app.patch("/api/threads/{thread_id}", response_model=ThreadOut)
def api_update_thread(thread_id: int, req: UpdateThreadRequest):
    if req.title is None or (req.title or "").strip() == "":
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    t = db_update_thread(thread_id, title=req.title.strip())
    if not t:
        raise HTTPException(status_code=404, detail="Thread not found")
    return ThreadOut(id=t.id, title=t.title, created_at=t.created_at.isoformat())


@app.delete("/api/threads/{thread_id}")
def api_delete_thread(thread_id: int):
    ok = db_delete_thread(thread_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"ok": True}


@app.get("/api/threads/{thread_id}/messages", response_model=List[MessageOut])
def api_get_messages(thread_id: int):
    import json as _json
    msgs = db_get_thread_messages(thread_id)
    out: List[MessageOut] = []
    for m in msgs:
        meta = None
        agents = None
        tools = None
        try:
            meta = _json.loads(m.meta) if getattr(m, "meta", None) else None
        except Exception:
            meta = None
        try:
            agents = _json.loads(m.agents) if m.agents else None
        except Exception:
            agents = None
        try:
            tools = _json.loads(m.tools) if m.tools else None
        except Exception:
            tools = None
        out.append(MessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            model=m.model,
            token_in=m.token_in,
            token_out=m.token_out,
            cost_usd=m.cost_usd,
            api_calls=m.api_calls,
            agents=agents,
            tools=tools,
            metadata=meta,
            created_at=m.created_at.isoformat()
        ))
    return out


@app.get("/api/threads/{thread_id}/summaries")
def api_list_summaries(thread_id: int):
    rows: List[Dict[str, Any]] = []
    try:
        with SessionLocal() as db:
            q = (
                db.query(ChatSummary)
                .filter(ChatSummary.thread_id == thread_id)
                .order_by(ChatSummary.upto_message_id.asc())
                .all()
            )
            for s in q:
                rows.append({
                    "id": s.id,
                    "upto_message_id": s.upto_message_id,
                    "content": s.content,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                })
    except Exception:
        rows = []
    return {"ok": True, "summaries": rows}


@app.post("/api/threads/{thread_id}/messages", response_model=MessageOut)
def api_post_message(thread_id: int, req: PostMessageRequest, token: Optional[str] = None):
    import json as _json
    # Resolve settings and mode
    settings = _get_user_settings(token)
    mode = str(settings.get("mode", "user") or "user")

    # Store user message
    um = db_add_message(thread_id=thread_id, role="user", content=req.content, parent_id=req.parent_id)
    # Build UI agent memory from thread (summary-aware)
    uia = UserInteractionAgent(user_name=req.user_name, mode=mode)
    for item in _assemble_memory(thread_id):
        uia.add_to_memory(item["role"], item["content"])
    
    # Collect response by consuming the stream
    full_parts: List[str] = []
    activated_agents: set = set()
    try:
        for delta in uia.stream_response(req.content):
            if isinstance(delta, str) and delta:
                full_parts.append(delta)
            elif isinstance(delta, dict):
                et = delta.get("type")
                if et == "agent":
                    agent_name = delta.get("name")
                    if agent_name:
                        activated_agents.add(agent_name)
    except Exception:
        pass
    
    answer = "".join(full_parts).strip()
    
    # Persist assistant with metadata if available
    model = getattr(uia, "last_model", None)
    usage = getattr(uia, "last_usage", {}) if hasattr(uia, "last_usage") else {}
    token_in = usage.get("prompt_tokens") if isinstance(usage, dict) else None
    token_out = usage.get("completion_tokens") if isinstance(usage, dict) else None
    tools_used = usage.get("tools_used") if isinstance(usage, dict) else None
    provider = getattr(uia, "last_provider", None)
    metadata: Dict[str, Any] | None = None
    try:
        metadata = {"provider": provider, "tools_used": tools_used}
    except Exception:
        metadata = None

    # Derived metadata for UI/exports
    agents_list = list(activated_agents) if activated_agents else []
    tools_obj = {"used": (tools_used or []), "count": len(tools_used or [])}
    agents_obj = {"activated": agents_list, "count": len(agents_list)}
    api_calls = (1 if model else 0) + len(tools_obj["used"])  # model call + tool calls
    cost_usd = _compute_cost_usd(provider, model, token_in, token_out)

    # Also propagate agents/tools metadata to the originating user message
    try:
        db_update_message(
            um.id,
            agents=_json.dumps(agents_obj, ensure_ascii=False) if agents_obj else None,
            tools=_json.dumps(tools_obj, ensure_ascii=False) if tools_obj else None,
            meta=(None if metadata is None else _json.dumps(metadata, ensure_ascii=False)),
        )
    except Exception:
        pass

    am = db_add_message(
        thread_id=thread_id,
        role="assistant",
        content=answer,
        model=model,
        token_in=token_in,
        token_out=token_out,
        cost_usd=cost_usd,
        agents=_json.dumps(agents_obj, ensure_ascii=False) if agents_obj else None,
        tools=_json.dumps(tools_obj, ensure_ascii=False) if tools_obj else None,
        api_calls=api_calls,
        parent_id=um.id,
        meta=(None if metadata is None else _json.dumps(metadata, ensure_ascii=False)),
    )

    # Best-effort: create/update rolling summary when appropriate
    try:
        if _should_summarize(thread_id, am.id, token_in, token_out):
            summary = _generate_summary(thread_id, am.id)
            if summary:
                db_add_summary(thread_id=thread_id, upto_message_id=am.id, content=summary)
    except Exception:
        pass

    # Prepare parsed fields for response
    agents_parsed = agents_obj
    tools_parsed = tools_obj
    return MessageOut(
        id=am.id,
        role=am.role,
        content=am.content,
        model=am.model,
        token_in=am.token_in,
        token_out=am.token_out,
        cost_usd=am.cost_usd,
        api_calls=am.api_calls,
        agents=agents_parsed,
        tools=tools_parsed,
        metadata=metadata,
        created_at=am.created_at.isoformat(),
    )


@app.post("/api/threads/{thread_id}/messages/stream")
def api_post_message_stream(thread_id: int, req: PostMessageRequest, token: Optional[str] = None):
    import json as _json

    def _get_show_thinking() -> bool:
        try:
            settings = _get_user_settings(token)
            return bool(settings.get("show_thinking", False))
        except Exception:
            return False

    def _get_mode() -> str:
        try:
            settings = _get_user_settings(token)
            return str(settings.get("mode", "user") or "user")
        except Exception:
            return "user"

    def _iter():
        # Early event to open the stream
        try:
            if _get_show_thinking():
                yield "event: thinking\n" + "data: " + _json.dumps({"status": "started"}) + "\n\n"
            else:
                yield "event: ping\n" + "data: {}\n\n"
        except Exception:
            yield "event: ping\n" + "data: {}\n\n"

        # Process the message and forward true token streaming
        try:
            # Store user message first
            um = db_add_message(thread_id=thread_id, role="user", content=req.content, parent_id=req.parent_id)

            # Prepare UI agent and assemble memory (includes summary + recent tail)
            uia = UserInteractionAgent(user_name=req.user_name, mode=_get_mode())
            for item in _assemble_memory(thread_id):
                uia.add_to_memory(item["role"], item["content"])

            # Create a placeholder assistant message to obtain an id for deltas
            am = db_add_message(
                thread_id=thread_id,
                role="assistant",
                content="",
                parent_id=um.id,
            )

            # Stream tokens from the LLM and forward as SSE deltas
            full_parts: List[str] = []
            activated_agents: set = set()
            try:
                for delta in uia.stream_response(req.content):
                    try:
                        # Back-compat: plain text chunks
                        if isinstance(delta, str) and delta:
                            full_parts.append(delta)
                            yield "event: message\n" + "data: " + _json.dumps({"id": am.id, "delta": delta}, ensure_ascii=False) + "\n\n"
                            continue

                        # Structured events from UIA/LLM tool streaming
                        if isinstance(delta, dict):
                            et = delta.get("type")
                            if et == "delta":
                                text = delta.get("text") or ""
                                if text:
                                    full_parts.append(text)
                                    yield "event: message\n" + "data: " + _json.dumps({"id": am.id, "delta": text}, ensure_ascii=False) + "\n\n"
                            elif et == "agent":
                                # Forward agent activation for UI badges and collect for database
                                agent_name = delta.get("name")
                                if agent_name:
                                    activated_agents.add(agent_name)
                                payload = {"name": agent_name}
                                yield "event: agent\n" + "data: " + _json.dumps(payload, ensure_ascii=False) + "\n\n"
                            elif et == "tool_call":
                                # Forward tool call lifecycle events
                                payload = {"name": delta.get("name"), "status": delta.get("status")}
                                yield "event: tool_call\n" + "data: " + _json.dumps(payload, ensure_ascii=False) + "\n\n"
                            # Unknown structured events are ignored for now
                    except Exception:
                        # Ignore malformed streaming payloads while keeping the stream alive
                        continue
            except Exception:
                # streaming failed mid-way; proceed to finalize with what we have
                pass

            # Finalize content and collect metadata
            full_text = ("".join(full_parts)).strip()
            model = getattr(uia, "last_model", None)
            usage = getattr(uia, "last_usage", {}) if hasattr(uia, "last_usage") else {}
            token_in = usage.get("prompt_tokens") if isinstance(usage, dict) else None
            token_out = usage.get("completion_tokens") if isinstance(usage, dict) else None
            tools_used = usage.get("tools_used") if isinstance(usage, dict) else None
            provider = getattr(uia, "last_provider", None)
            metadata: Dict[str, Any] | None = None
            try:
                metadata = {"provider": provider, "tools_used": tools_used}
            except Exception:
                metadata = None

            agents_list = list(activated_agents) if activated_agents else []
            tools_obj = {"used": (tools_used or []), "count": len(tools_used or [])}
            agents_obj = {"activated": agents_list, "count": len(agents_list)}
            api_calls = (1 if model else 0) + len(tools_obj["used"])
            cost_usd = _compute_cost_usd(provider, model, token_in, token_out)

            # Update the originating user message to include agents/tools metadata
            try:
                db_update_message(
                    um.id,
                    agents=_json.dumps(agents_obj, ensure_ascii=False) if agents_obj else None,
                    tools=_json.dumps(tools_obj, ensure_ascii=False) if tools_obj else None,
                    meta=(None if metadata is None else _json.dumps(metadata, ensure_ascii=False)),
                )
            except Exception:
                pass

            # Update the placeholder message with final content and metadata
            am = db_update_message(
                am.id,
                content=full_text,
                model=model,
                token_in=token_in,
                token_out=token_out,
                cost_usd=cost_usd,
                agents=_json.dumps(agents_obj, ensure_ascii=False) if agents_obj else None,
                tools=_json.dumps(tools_obj, ensure_ascii=False) if tools_obj else None,
                api_calls=api_calls,
                meta=(None if metadata is None else _json.dumps(metadata, ensure_ascii=False)),
            )

            # Best-effort summarization
            try:
                if _should_summarize(thread_id, am.id, token_in, token_out):
                    summary = _generate_summary(thread_id, am.id)
                    if summary:
                        db_add_summary(thread_id=thread_id, upto_message_id=am.id, content=summary)
            except Exception:
                pass

            # Emit final message payload (backwards compatible)
            payload = {
                "id": am.id,
                "role": am.role,
                "content": am.content,
                "model": am.model,
                "token_in": am.token_in,
                "token_out": am.token_out,
                "cost_usd": am.cost_usd,
                "api_calls": am.api_calls,
                "agents": agents_obj,
                "tools": tools_obj,
                "metadata": metadata,
                "created_at": am.created_at.isoformat(),
            }
            yield "event: message\n" + "data: " + _json.dumps(payload, ensure_ascii=False) + "\n\n"
            yield "event: done\n" + "data: {}\n\n"
        except Exception as e:
            err = {"error": str(e)}
            yield "event: error\n" + "data: " + _json.dumps(err, ensure_ascii=False) + "\n\n"

    return StreamingResponse(_iter(), media_type="text/event-stream")


# ---------- Price Feed (SSE) ----------

@app.get("/api/prices/stream")
async def api_prices_stream(sku: Optional[str] = None):
    import asyncio
    import json
    import random
    import time
    import sqlite3

    if sku:
        symbols = [sku]
    else:
        conn = sqlite3.connect('data/market.db')
        cursor = conn.cursor()
        cursor.execute('SELECT product_name FROM market_data LIMIT 50')
        symbols = [row[0] for row in cursor.fetchall()]
        conn.close()
        if not symbols:
            symbols = ["SKU-1", "SKU-2", "SKU-3"]
    
    bases = {s: 100.0 + random.random() * 10.0 for s in symbols}

    async def _aiter():
        # Initial ping to open stream quickly
        yield "event: ping\n" + "data: {}\n\n"
        while True:
            try:
                sym = random.choice(symbols)
                # simple bounded random walk
                drift = random.uniform(-1.2, 1.2)
                price = max(1.0, bases[sym] + drift)
                bases[sym] = price
                payload = {
                    "sku": sym,
                    "price": round(price, 2),
                    "ts": int(time.time() * 1000),
                }
                yield "event: price\n" + "data: " + json.dumps(payload, ensure_ascii=False) + "\n\n"
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                err = {"error": str(e)}
                yield "event: error\n" + "data: " + json.dumps(err, ensure_ascii=False) + "\n\n"
                await asyncio.sleep(1.0)

    return StreamingResponse(_aiter(), media_type="text/event-stream")
