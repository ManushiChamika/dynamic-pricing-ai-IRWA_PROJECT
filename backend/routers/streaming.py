from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from core.chat_db import (
    add_message,
    update_message,
    get_thread_messages,
    get_message,
)
from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
from core.payloads import PostMessageRequest, MessageOut
import logging

logger = logging.getLogger(__name__)


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


def _safe_add_summary(thread_id: int, upto_message_id: int, content: str) -> bool:
    from backend.routers.utils import safe_add_summary
    return safe_add_summary(thread_id, upto_message_id, content)


def _should_auto_rename_thread(thread_id: int) -> bool:
    from backend.routers.utils import should_auto_rename_thread
    return should_auto_rename_thread(thread_id)


def _generate_thread_title(thread_id: int) -> Optional[str]:
    from backend.routers.utils import generate_thread_title
    return generate_thread_title(thread_id)


def _update_thread_title(thread_id: int, new_title: str):
    from core.chat_db import update_thread
    return update_thread(thread_id, title=new_title)


def _summarize_tool_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, Dict[str, int]] = {}
    for e in events:
        n = e.get("name")
        s = e.get("status")
        if not n:
            continue
        if n not in counts:
            counts[n] = {"start": 0, "end": 0}
        if s == "start":
            counts[n]["start"] += 1
        if s == "end":
            counts[n]["end"] += 1
    completed = [k for k, v in counts.items() if v.get("end", 0) >= v.get("start", 0) and v.get("end", 0) > 0]
    incomplete = [k for k, v in counts.items() if v.get("start", 0) > v.get("end", 0)]
    return {"events": events, "completed": completed, "incomplete": incomplete}


def _apply_output_gate(text: str, tools_used: Optional[List[str]]) -> (str, Optional[Dict[str, Any]]):
    t = text or ""
    lu = tools_used or []
    lower = t.lower()
    trigger = False
    phrases = ["recommended price", "we recommend", "optimal price", "set price to", "suggested price"]
    for p in phrases:
        if p in lower:
            trigger = True
            break
    if trigger and ("list_price_proposals" not in lu):
        note = "\n\nNote: No price proposals verified yet; optimization may be running."
        return t + note, {"recommendation_gated": True, "reason": "no_list_price_proposals_call"}
    return t, None


def _extract_token_from_request(request: Optional[Request]) -> Optional[str]:
    try:
        if request is None:
            return None
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


@router.post("/{thread_id}/messages", response_model=MessageOut)
def api_post_message(thread_id: int, req: PostMessageRequest, token: Optional[str] = None, request: Optional[Request] = None):
    import json as _json
    from core.auth_service import validate_session_token
    from core.agents.user_interact.context import set_owner_id

    tok = token or _extract_token_from_request(request)

    settings = _get_user_settings(tok)
    mode = str(settings.get("mode", "user") or "user")
    owner_id = None

    if tok:
        sess = validate_session_token(tok)
        logger.info(f"[DEBUG POST] Session validation result: {sess}")
        if sess and "user_id" in sess:
            owner_id = str(sess["user_id"])
            logger.info(f"[DEBUG POST] Extracted owner_id: {owner_id}")
    else:
        logger.warning("[DEBUG POST] No token provided!")

    um = add_message(thread_id=thread_id, role="user", content=req.content, parent_id=req.parent_id)
    uia = UserInteractionAgent(user_name=req.user_name, mode=mode, owner_id=owner_id)
    logger.info(f"[DEBUG POST] Created UserInteractionAgent with owner_id={owner_id}")

    if owner_id:
        set_owner_id(owner_id)
        logger.info(f"[DEBUG POST] Called set_owner_id({owner_id})")

    for item in _assemble_memory(thread_id):
        uia.add_to_memory(item["role"], item["content"])

    full_parts: List[str] = []
    activated_agents: set = set()
    tool_events: List[Dict[str, Any]] = []
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
                elif et == "tool_call":
                    tool_events.append({"name": delta.get("name"), "status": delta.get("status")})
    except Exception:
        pass

    answer = "".join(full_parts).strip()

    model = getattr(uia, "last_model", None)
    usage = getattr(uia, "last_usage", {}) if hasattr(uia, "last_usage") else {}
    token_in = usage.get("prompt_tokens") if isinstance(usage, dict) else None
    token_out = usage.get("completion_tokens") if isinstance(usage, dict) else None
    tools_used = usage.get("tools_used") if isinstance(usage, dict) else None
    provider = getattr(uia, "last_provider", None)

    gated_answer, gate_meta = _apply_output_gate(answer, tools_used if isinstance(tools_used, list) else [])

    tool_status = _summarize_tool_events(tool_events) if tool_events else {"events": [], "completed": [], "incomplete": []}

    metadata: Dict[str, Any] | None = None
    try:
        base_meta = {"provider": provider, "tools_used": tools_used, "tool_status": tool_status}
        if gate_meta:
            base_meta["output_gate"] = gate_meta
        metadata = base_meta
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
        content=gated_answer,
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
                _safe_add_summary(thread_id, am.id, summary)
    except Exception as e:
        logger.exception(f"Summarization failed for thread {thread_id}, message {am.id}: {e}")

    try:
        if _should_auto_rename_thread(thread_id):
            new_title = _generate_thread_title(thread_id)
            if new_title:
                _update_thread_title(thread_id, new_title)
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
def api_post_message_stream(thread_id: int, req: PostMessageRequest, token: Optional[str] = None, request: Optional[Request] = None):
    import json as _json

    tok = token or _extract_token_from_request(request)

    def _get_show_thinking() -> bool:
        try:
            settings = _get_user_settings(tok)
            return bool(settings.get("show_thinking", False))
        except Exception:
            return False

    def _get_mode() -> str:
        try:
            settings = _get_user_settings(tok)
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
            from core.auth_service import validate_session_token
            from core.agents.user_interact.context import set_owner_id

            owner_id = None
            if tok:
                sess = validate_session_token(tok)
                logger.info(f"[DEBUG STREAM] Session validation result: {sess}")
                if sess and "user_id" in sess:
                    owner_id = str(sess["user_id"])
                    logger.info(f"[DEBUG STREAM] Extracted owner_id: {owner_id}")
            else:
                logger.warning("[DEBUG STREAM] No token provided!")

            um = add_message(thread_id=thread_id, role="user", content=req.content, parent_id=req.parent_id)

            uia = UserInteractionAgent(user_name=req.user_name, mode=_get_mode(), owner_id=owner_id)
            logger.info(f"[DEBUG STREAM] Created UserInteractionAgent with owner_id={owner_id}")

            if owner_id:
                set_owner_id(owner_id)
                logger.info(f"[DEBUG STREAM] Called set_owner_id({owner_id})")

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
            tool_events: List[Dict[str, Any]] = []
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
                                tool_events.append(payload)
                                yield "event: tool_call\n" + "data: " + _json.dumps(payload, ensure_ascii=False) + "\n\n"
                    except Exception as e:
                        logger.warning("Error processing stream delta: %s", e, exc_info=True)
                        continue
            except Exception as e:
                logger.error("Error in stream_response loop: %s", e, exc_info=True)

            full_text = ("".join(full_parts)).strip()
            model = getattr(uia, "last_model", None)
            usage = getattr(uia, "last_usage", {}) if hasattr(uia, "last_usage") else {}
            token_in = usage.get("prompt_tokens") if isinstance(usage, dict) else None
            token_out = usage.get("completion_tokens") if isinstance(usage, dict) else None
            tools_used = usage.get("tools_used") if isinstance(usage, dict) else None
            provider = getattr(uia, "last_provider", None)

            gated_text, gate_meta = _apply_output_gate(full_text, tools_used if isinstance(tools_used, list) else [])
            tool_status = _summarize_tool_events(tool_events) if tool_events else {"events": [], "completed": [], "incomplete": []}

            metadata: Dict[str, Any] | None = None
            try:
                base_meta = {"provider": provider, "tools_used": tools_used, "tool_status": tool_status}
                if gate_meta:
                    base_meta["output_gate"] = gate_meta
                metadata = base_meta
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
                content=gated_text,
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
                        _safe_add_summary(thread_id, am.id, summary)
            except Exception as e:
                logger.exception(f"Summarization failed for thread {thread_id}, message {am.id}: {e}")

            try:
                if _should_auto_rename_thread(thread_id):
                    new_title = _generate_thread_title(thread_id)
                    if new_title:
                        _update_thread_title(thread_id, new_title)
                        yield "event: thread_renamed\n" + "data: " + _json.dumps({"id": thread_id, "title": new_title}, ensure_ascii=False) + "\n\n"
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
