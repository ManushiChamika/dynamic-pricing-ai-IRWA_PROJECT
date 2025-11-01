from __future__ import annotations

import os
import uuid
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Deque, Dict, List, Optional


def generate_trace_id() -> str:
    """Generate a unique trace ID for request correlation."""
    return f"trace-{uuid.uuid4().hex[:8]}"


def should_trace() -> bool:
    """Check if detailed tracing is enabled via env flag."""
    return os.getenv("TRACE_STEPS", "0").strip() in {"1", "true", "True", "yes", "on"}


def safe_redact(obj: Any, max_str_len: int = 500, max_items: int = 10) -> Any:
    """Safely redact and truncate data for logging."""
    try:
        if isinstance(obj, str):
            if len(obj) > max_str_len:
                return obj[:max_str_len] + f"... [truncated {len(obj)-max_str_len} chars]"
            # Basic secret detection
            lower = obj.lower()
            if any(secret in lower for secret in ["api_key", "password", "token", "secret"]):
                return "[REDACTED]"
            return obj
        elif isinstance(obj, dict):
            if len(obj) > max_items:
                keys = list(obj.keys())[:max_items]
                result = {k: safe_redact(obj[k], max_str_len, max_items) for k in keys}
                result["_truncated"] = f"{len(obj) - max_items} more keys"
                return result
            return {k: safe_redact(v, max_str_len, max_items) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            if len(obj) > max_items:
                result = [safe_redact(item, max_str_len, max_items) for item in obj[:max_items]]
                result.append(f"... [truncated {len(obj)-max_items} more items]")
                return result
            return [safe_redact(item, max_str_len, max_items) for item in obj]
        else:
            return obj
    except Exception:
        return "[redaction_error]"


@dataclass
class Activity:
    ts: str
    agent: str
    action: str
    status: str  # in_progress | completed | failed | info
    message: str = ""
    details: Optional[Dict[str, Any]] = None


class _ActivityLog:
    def __init__(self, maxlen: int = 200) -> None:
        self._items: Deque[Activity] = deque(maxlen=maxlen)
        self._lock = Lock()

    def log(
        self,
        agent: str,
        action: str,
        status: str = "info",
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        rec = Activity(
            ts=datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
            agent=agent,
            action=action,
            status=status,
            message=message,
            details=details,
        )
        with self._lock:
            self._items.append(rec)

    def recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            it = list(self._items)[-limit:]
        return [asdict(x) for x in reversed(it)]

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


# Global singleton instance
activity_log = _ActivityLog()


def get_activity_log() -> _ActivityLog:
    """Get the global activity log instance."""
    return activity_log
