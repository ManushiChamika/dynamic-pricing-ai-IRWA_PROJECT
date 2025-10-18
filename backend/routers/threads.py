from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from core.chat_db import (
    create_thread,
    delete_thread,
    get_thread_messages,
    list_threads,
    update_thread,
    add_message,
    SessionLocal,
    Thread as ChatThread,
    Summary as ChatSummary,
)
from core.payloads import (
    CreateThreadRequest,
    ThreadOut,
    UpdateThreadRequest,
    ThreadExport,
    ThreadImportRequest,
)
from core.auth_service import validate_session_token

router = APIRouter(prefix="/api/threads", tags=["threads"])


@router.post("", response_model=ThreadOut)
def api_create_thread(req: CreateThreadRequest, token: Optional[str] = None):
    owner_id = None
    if token:
        sess = validate_session_token(token)
        if sess:
            owner_id = sess["user_id"]
    t = create_thread(title=req.title, owner_id=owner_id)
    return ThreadOut(id=t.id, title=t.title, created_at=t.created_at.isoformat())


@router.get("", response_model=List[ThreadOut])
def api_list_threads(token: Optional[str] = None):
    owner_id = None
    if token:
        sess = validate_session_token(token)
        if sess:
            owner_id = sess["user_id"]
    rows = list_threads(owner_id=owner_id)
    return [ThreadOut(id=t.id, title=t.title, created_at=t.created_at.isoformat()) for t in rows]


@router.patch("/{thread_id}", response_model=ThreadOut)
def api_update_thread(thread_id: int, req: UpdateThreadRequest):
    if req.title is None or (req.title or "").strip() == "":
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    t = update_thread(thread_id, title=req.title.strip())
    if not t:
        raise HTTPException(status_code=404, detail="Thread not found")
    return ThreadOut(id=t.id, title=t.title, created_at=t.created_at.isoformat())


@router.delete("/{thread_id}")
def api_delete_thread(thread_id: int):
    ok = delete_thread(thread_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"ok": True}


@router.get("/{thread_id}/export", response_model=ThreadExport)
def api_export_thread(thread_id: int):
    msgs = get_thread_messages(thread_id)
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


@router.post("/import", response_model=ThreadOut)
def api_import_thread(req: ThreadImportRequest):
    t = create_thread(title=req.title, owner_id=req.owner_id)
    id_map: Dict[int, int] = {}
    import json as _json
    for msg in req.messages:
        agents = _json.dumps(msg.agents) if msg.agents is not None else None
        tools = _json.dumps(msg.tools) if msg.tools is not None else None
        metadata = _json.dumps(msg.metadata) if msg.metadata is not None else None
        parent_id = id_map.get(int(msg.parent_id)) if msg.parent_id is not None and int(msg.parent_id) in id_map else None
        m = add_message(
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
        if msg.id is not None:
            id_map[int(msg.id)] = m.id
    return ThreadOut(id=t.id, title=t.title, created_at=t.created_at.isoformat())


@router.get("/{thread_id}/summaries")
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
