# core/bus.py
import asyncio
from typing import Any, Callable, Dict, List
from dataclasses import dataclass


class EventBus:
    """Simple event bus for inter-agent communication."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        print("EventBus: initialized")
        try:
            from datetime import datetime
            import pathlib
            pathlib.Path.cwd().joinpath("runtime_debug.log").write_text(f"{datetime.utcnow().isoformat()} EventBus initialized\n", encoding="utf-8")
        except Exception:
            pass
    
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic with a callback function."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
    
    async def publish(self, topic: str, data: Any):
        """Publish data to a topic, calling all subscribers."""
        if topic in self._subscribers:
            for callback in self._subscribers[topic]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    print(f"Error in subscriber callback for topic {topic}: {e}")
                    try:
                        from datetime import datetime
                        import pathlib
                        pathlib.Path.cwd().joinpath("runtime_debug.log").write_text(f"{datetime.utcnow().isoformat()} Error in subscriber callback for topic {topic}: {e}\n", encoding="utf-8")
                    except Exception:
                        pass
    
    def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribe a callback from a topic."""
        if topic in self._subscribers:
            self._subscribers[topic] = [cb for cb in self._subscribers[topic] if cb != callback]


# Global bus instance
bus = EventBus()
print("EventBus: global instance created")
