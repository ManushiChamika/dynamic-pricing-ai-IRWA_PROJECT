# core/bus.py
from __future__ import annotations
import asyncio
import inspect
import logging
from collections import defaultdict
from typing import Any, Callable, DefaultDict, List

log = logging.getLogger(__name__)

Handler = Callable[[Any], Any]  # may be sync or async

class EventBus:
    def __init__(self) -> None:
        self._subs: DefaultDict[str, List[Handler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Handler) -> None:
        """Register a handler for a topic (idempotent)."""
        if handler not in self._subs[topic]:
            self._subs[topic].append(handler)

    def unsubscribe(self, topic: str, handler: Handler) -> None:
        try:
            self._subs.get(topic, []).remove(handler)
        except ValueError:
            pass

    # OPTIONAL: concurrent fan-out
    async def publish(self, topic: str, payload: Any) -> None:
        handlers = list(self._subs.get(topic, []))
        coros = []
        for h in handlers:
            try:
                if inspect.iscoroutinefunction(h):
                    coros.append(h(payload))
                else:
                    res = h(payload)
                    if inspect.isawaitable(res):
                        coros.append(res)
            except Exception as e:
                log.warning("EventBus handler error on %s: %s", topic, e)
        if coros:
            await asyncio.gather(*coros, return_exceptions=True)


# singleton
bus = EventBus()
