from __future__ import annotations

from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from threading import Lock
from typing import Any, Deque, Dict, List, Optional


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
            ts=datetime.utcnow().isoformat(timespec="seconds") + "Z",
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
