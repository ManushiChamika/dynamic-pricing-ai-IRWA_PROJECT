from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Awaitable, Callable, Dict, List


class _AsyncBus:
    def __init__(self):
        self._subs: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, topic: str, callback: Callable):
        # Callback can be sync or async; we'll handle both at publish time.
        self._subs[topic].append(callback)

    async def publish(self, topic: str, message):
        for cb in list(self._subs.get(topic, [])):
            try:
                res = cb(message)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                # Best-effort bus: ignore sink errors
                pass


_BUS: _AsyncBus | None = None


def get_bus() -> _AsyncBus:
    global _BUS
    if _BUS is None:
        _BUS = _AsyncBus()
    return _BUS
