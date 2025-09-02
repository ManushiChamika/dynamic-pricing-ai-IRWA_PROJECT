# core/bus.py
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List

Subscriber = Callable[[Any], Awaitable[None]]


class EventBus:
    """
    Simple in-process async pub/sub bus.
    Agents can publish events (dicts) and subscribe with async handlers.
    """

    def __init__(self) -> None:
        self._subs: Dict[str, List[Subscriber]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Subscriber) -> None:
        """Register an async handler for a topic."""
        self._subs[topic].append(handler)

    async def publish(self, topic: str, event: Any) -> None:
        """Publish an event to all subscribers of that topic."""
        for handler in self._subs.get(topic, []):
            await handler(event)


# Global bus instance to import everywhere
bus = EventBus()
