from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from core.chat_db import (
    add_message,
    update_message,
    get_thread_messages,
)
from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
from core.payloads import PostMessageRequest, MessageOut


router = APIRouter(prefix="/api/threads", tags=["streaming"])


def _get_user_settings(token: Optional[str]) -> Dict[str, Any]:
    from core.auth_service import validate_session_token
    if not token:
        return {}
    sess = validate_session_token(token)
    if not sess:
        return {}
    from backend.routers.settings import get_user_settings
    return get_user_settings(token)


def _assemble_memory(thread_id: int) -> List[Dict[str, str]]:
    from backend.routers.utils import assemble_memory
    return assemble_memory(thread_id)


def _compute_cost_usd(provider: Optional[str], model: Optional[str], token_in: Optional[int], token_out: Optional[int]) -> Optional[str]:
    from backend.routers.utils import compute_cost_usd
    return compute_cost_usd(provider, model, token_in, token_out)


def _should_summarize(thread_id: int, upto_message_id: int, token_in: Optional[int], token_out: Optional[int]) -> bool:
    from backend.routers.utils import should_summarize
    return should_summarize(thread_id, upto_message_id, token_in, token_out)


def _generate_summary(thread_id: int, upto_message_id: int) -> Optional[str]:
    from backend.routers.utils import generate_summary
    return generate_summary(thread_id, upto_message_id)


def db_add_summary(thread_id: int, upto_message_id: int, content: str):
    from core.chat_db import add_summary as _add_summary
    return _add_summary(thread_id, upto_message_id, content)


def _should_auto_rename_thread(thread_id: int) -> bool:
    from backend.routers.utils import should_auto_rename_thread
    return should_auto_rename_thread(thread_id)


def _generate_thread_title(thread_id: int) -> Optional[str]:
    from backend.routers.utils import generate_thread_title
    return generate_thread_title(thread_id)


def _update_thread_title(thread_id: int, title: str) -> bool:
    from core.chat_db import update_thread
    try:
        result = update_thread(thread_id, title=title)
        return result is not None
    except Exception:
        return False


@router.post("/{thread_id}/messages", response_model=MessageOut)
def api_post_message(thread_id: int, req: PostMessageRequest, token: Optional[str] = None):
    import json as _json
    settings = _get_user_settings(token)
    mode = str(settings.get("mode", "user") or "user")

    um = add_message(thread_id=thread_id, role="user", content=req.content, parent_id=req.parent_id)
    uia = UserInteractionAgent(user_name=req.user_name, mode=mode)
    for item in _assemble_memory(thread_id):
        uia.add_to_memory(item["role"], item["content"])
    
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

    try:
        update_message(
            um.id,
            agents=_json.dumps(agents_obj, ensure_ascii=False) if agents_obj else None,
            tools=_json.dumps(tools_obj, ensure_ascii=False) if tools_obj else None,
            meta=(None if metadata is None else _json.dumps(metadata, ensure_ascii=False)),
        )
    except Exception:
        pass

    am = add_message(
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

            try:
                if _should_summarize(thread_id, am.id, token_in, token_out):
                    summary = _generate_summary(thread_id, am.id)
                    if summary:
                        db_add_summary(thread_id=thread_id, upto_message_id=am.id, content=summary)
            except Exception:
                pass

            try:
                if _should_auto_rename_thread(thread_id):
                    new_title = _generate_thread_title(thread_id)
                    if new_title:
                        _update_thread_title(thread_id, new_title)
                        yield "event: thread_renamed\n" + "data: " + _json.dumps({"thread_id": thread_id, "title": new_title}, ensure_ascii=False) + "\n\n"
            except Exception:
                pass

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


@router.post("/{thread_id}/messages/stream")
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
        try:
            if _get_show_thinking():
                yield "event: thinking\n" + "data: " + _json.dumps({"status": "started"}) + "\n\n"
            else:
                yield "event: ping\n" + "data: {}\n\n"
        except Exception:
            yield "event: ping\n" + "data: {}\n\n"

        try:
            um = add_message(thread_id=thread_id, role="user", content=req.content, parent_id=req.parent_id)

            uia = UserInteractionAgent(user_name=req.user_name, mode=_get_mode())
            for item in _assemble_memory(thread_id):
                uia.add_to_memory(item["role"], item["content"])

            am = add_message(
                thread_id=thread_id,
                role="assistant",
                content="",
                parent_id=um.id,
            )

            full_parts: List[str] = []
            activated_agents: set = set()
            try:
                for delta in uia.stream_response(req.content):
                    try:
                        if isinstance(delta, str) and delta:
                            full_parts.append(delta)
                            yield "event: message\n" + "data: " + _json.dumps({"id": am.id, "delta": delta}, ensure_ascii=False) + "\n\n"
                            continue

                        if isinstance(delta, dict):
                            et = delta.get("type")
                            if et == "delta":
                                text = delta.get("text") or ""
                                if text:
                                    full_parts.append(text)
                                    yield "event: message\n" + "data: " + _json.dumps({"id": am.id, "delta": text}, ensure_ascii=False) + "\n\n"
                            elif et == "agent":
                                agent_name = delta.get("name")
                                if agent_name:
                                    activated_agents.add(agent_name)
                                payload = {"name": agent_name}
                                yield "event: agent\n" + "data: " + _json.dumps(payload, ensure_ascii=False) + "\n\n"
                            elif et == "tool_call":
                                payload = {"name": delta.get("name"), "status": delta.get("status")}
                                yield "event: tool_call\n" + "data: " + _json.dumps(payload, ensure_ascii=False) + "\n\n"
                    except Exception:
                        continue
            except Exception:
                pass

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

            try:
                update_message(
                    um.id,
                    agents=_json.dumps(agents_obj, ensure_ascii=False) if agents_obj else None,
                    tools=_json.dumps(tools_obj, ensure_ascii=False) if tools_obj else None,
                    meta=(None if metadata is None else _json.dumps(metadata, ensure_ascii=False)),
                )
            except Exception:
                pass

            am = update_message(
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

            try:
                if _should_summarize(thread_id, am.id, token_in, token_out):
                    summary = _generate_summary(thread_id, am.id)
                    if summary:
                        db_add_summary(thread_id=thread_id, upto_message_id=am.id, content=summary)
            except Exception:
                pass

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
