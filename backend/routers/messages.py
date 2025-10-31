from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from core.chat_db import (
    get_message,
    delete_message,
    delete_message_cascade,
    update_message,
    get_thread_messages,
)
from core.payloads import (
    EditMessageRequest,
    MessageOut,
    DeleteMessageResponse,
)

router = APIRouter(prefix="/api", tags=["messages"])


@router.patch("/messages/{message_id}", response_model=MessageOut)
def api_edit_message(message_id: int, req: EditMessageRequest):
    m = get_message(message_id)
    if not m:
        raise HTTPException(status_code=404, detail="Message not found")
    if m.role != "user":
        raise HTTPException(status_code=400, detail="Only user messages can be edited")
    m = update_message(message_id, content=req.content)
    return MessageOut(id=m.id, role=m.role, content=m.content, model=m.model, created_at=m.created_at.isoformat())


@router.delete("/messages/{message_id}", response_model=DeleteMessageResponse)
def api_delete_message(message_id: int):
    ok = delete_message_cascade(message_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Message not found")
    return DeleteMessageResponse(ok=True)


@router.get("/threads/{thread_id}/messages", response_model=List[MessageOut])
def api_get_messages(thread_id: int):
    import json as _json
    msgs = get_thread_messages(thread_id)
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
