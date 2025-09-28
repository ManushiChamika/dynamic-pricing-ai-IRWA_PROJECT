from typing import List, Dict, Any

try:
    from core.agents.agent_sdk.activity_log import activity_log
except Exception:
    activity_log = None  # type: ignore

# Optional bridge from the shared bus to the activity log
try:
    from core.agents.agent_sdk import get_bus, Topic  # type: ignore
except Exception:
    get_bus = None  # type: ignore
    Topic = None  # type: ignore

_bridge_started = False


def _to_dict(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    for name in ("model_dump", "dict"):
        fn = getattr(obj, name, None)
        if callable(fn):
            try:
                d = fn()
                if isinstance(d, dict):
                    return d
            except Exception:
                pass
    return getattr(obj, "__dict__", {}) or {}


def ensure_bus_bridge() -> bool:
    global _bridge_started
    if _bridge_started:
        return True
    if activity_log is None or get_bus is None or Topic is None:
        return False

    bus = get_bus()

    def on_alert(ev: Any):  # sync callback is fine
        try:
            d = _to_dict(ev)
            sev = str(d.get("severity", "info")).lower()
            status = {"crit": "failed", "warn": "in_progress", "info": "info"}.get(sev, "info")
            agent = "Alerts" if d.get("rule_id") else "System"
            action = d.get("title") or d.get("message") or d.get("kind") or "alert"
            msg = str(d.get("sku", ""))
            activity_log.log(agent=agent, action=action, status=status, message=msg, details=d)
        except Exception:
            # Best-effort logging only
            pass

    def on_price_update(ev: Any):
        try:
            d = _to_dict(ev)
            sku = str(d.get("sku", ""))
            old_p = d.get("old_price")
            new_p = d.get("new_price")
            actor = d.get("actor") or "system"
            algo = d.get("algorithm") or "unknown"
            msg = f"{sku} {old_p}→{new_p} by {actor} ({algo})"
            activity_log.log(agent="Pricing", action="price.update", status="completed", message=msg, details=d)
        except Exception:
            pass

    def on_price_proposal(ev: Any):
        try:
            d = _to_dict(ev)
            trace_id = d.get("trace_id", "")
            sku = str(d.get("sku", ""))
            old_p = d.get("old_price")
            new_p = d.get("new_price")
            rationale = d.get("rationale", "")
            confidence = d.get("confidence", 0)
            msg = f"{sku}: {old_p} → {new_p} ({confidence:.1%} confidence)"
            details = dict(d)
            if trace_id:
                details["trace_id"] = trace_id
            activity_log.log(agent="PriceOptimizer", action="proposal.generated", status="completed", message=msg, details=details)
        except Exception:
            pass

    def on_chat_prompt(ev: Any):
        try:
            d = _to_dict(ev)
            trace_id = d.get("trace_id", "")
            action = d.get("action", "unknown")
            user = d.get("user", "")
            duration_ms = d.get("duration_ms")
            
            if action == "start":
                msg = f"Processing prompt from {user}" if user else "Processing prompt"
                status = "in_progress"
            elif action == "done":
                msg = f"Response generated ({duration_ms}ms)" if duration_ms else "Response generated"
                status = "completed"
            elif action == "fallback":
                msg = f"LLM unavailable, using fallback ({duration_ms}ms)" if duration_ms else "LLM unavailable"
                status = "completed"
            else:
                msg = f"Chat {action}"
                status = "info"
            
            details = dict(d)
            if trace_id:
                details["trace_id"] = trace_id
            activity_log.log(agent="Chat", action=f"prompt.{action}", status=status, message=msg, details=details)
        except Exception:
            pass

    def on_chat_tool_call(ev: Any):
        try:
            d = _to_dict(ev)
            trace_id = d.get("trace_id", "")
            action = d.get("action", "unknown")
            tool_name = d.get("tool_name", "unknown")
            duration_ms = d.get("duration_ms")
            error = d.get("error", False)
            
            if action == "start":
                msg = f"Calling {tool_name}"
                status = "in_progress"
            elif action == "done":
                if error:
                    msg = f"Tool {tool_name} failed ({duration_ms}ms)" if duration_ms else f"Tool {tool_name} failed"
                    status = "failed"
                else:
                    msg = f"Tool {tool_name} completed ({duration_ms}ms)" if duration_ms else f"Tool {tool_name} completed"
                    status = "completed"
            else:
                msg = f"Tool {tool_name} {action}"
                status = "info"
            
            details = dict(d)
            if trace_id:
                details["trace_id"] = trace_id
            activity_log.log(agent="LLM", action=f"tool_call.{action}", status=status, message=msg, details=details)
        except Exception:
            pass

    try:
        bus.subscribe(Topic.ALERT.value, on_alert)
        bus.subscribe(Topic.PRICE_UPDATE.value, on_price_update)
        bus.subscribe(Topic.PRICE_PROPOSAL.value, on_price_proposal)
        bus.subscribe(Topic.CHAT_PROMPT.value, on_chat_prompt)
        bus.subscribe(Topic.CHAT_TOOL_CALL.value, on_chat_tool_call)
        _bridge_started = True
        return True
    except Exception:
        return False


def recent(limit: int = 50) -> List[Dict[str, Any]]:
    # Lazily start the bridge so Activity view works without extra wiring
    try:
        ensure_bus_bridge()
    except Exception:
        pass
    if activity_log is None:
        return []
    try:
        return activity_log.recent(limit)
    except Exception:
        return []
