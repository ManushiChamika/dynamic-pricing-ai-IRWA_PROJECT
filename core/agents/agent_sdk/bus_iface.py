# core/bus_iface.py
from typing import Any, Callable

Handler = Callable[[Any], Any]  # may be sync or async

class BusIface:
    def subscribe(self, topic: str, handler: Handler) -> None: ...
    async def publish(self, topic: str, payload: Any) -> None: ...
