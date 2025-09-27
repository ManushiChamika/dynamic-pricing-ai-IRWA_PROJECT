from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Callable, Dict, List


class _AsyncBus:
    def __init__(self):
        self._subs: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, topic: str, callback: Callable):
        # Callback can be sync or async; we'll handle both at publish time.
        self._subs[topic].append(callback)

    async def publish(self, topic: str, message):
        try:
            from core.observability.logging import get_logger
        except Exception:
            get_logger = None  # type: ignore
        log = None
        if get_logger:
            try:
                log = get_logger("bus")
            except Exception:
                log = None

        # Validate payload shape if schema exists
        try:
            from core.events.schemas import validate_payload
            ok, err = validate_payload(topic, message)
            if not ok and log:
                log.warning("invalid_event_payload", topic=topic, error=err, payload=message)
                return
        except Exception:
            pass

        # Best-effort journal write
        try:
            from core.events.journal import write_event
            write_event(topic, message)
        except Exception:
            pass

        # Dispatch to subscribers
        for cb in list(self._subs.get(topic, [])):
            try:
                res = cb(message)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                # Best-effort bus: ignore sink errors but log
                if log:
                    try:
                        log.warning("bus_sink_error", topic=topic, error=str(e), sink=repr(cb))
                    except Exception:
                        pass


_BUS: _AsyncBus | None = None


def get_bus() -> _AsyncBus:
    global _BUS
    if _BUS is None:
        _BUS = _AsyncBus()
    return _BUS
