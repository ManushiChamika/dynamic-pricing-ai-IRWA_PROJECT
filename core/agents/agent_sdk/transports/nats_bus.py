# core/brokers/nats_bus.py
import asyncio, json
from typing import Any, Dict, List
from nats.aio.client import Client as NATS  # pip install nats-py

from ..bus_iface import BusIface, Handler
from ....brokers.types import to_jsonable

class NatsBus(BusIface):
    def __init__(self, url: str):
        self.url = url
        self.nc: NATS | None = None
        self._subs: Dict[str, List[Handler]] = {}

    async def _ensure(self):
        if self.nc:
            return
        self.nc = NATS()
        await self.nc.connect(servers=[self.url])
        # subscribe all pre-registered topics
        for topic in list(self._subs.keys()):
            await self.nc.subscribe(topic, cb=self._on_msg)

    async def _on_msg(self, msg):
        try:
            payload = json.loads(msg.data.decode("utf-8"))
        except Exception:
            payload = None
        handlers = list(self._subs.get(msg.subject, []))
        coros = []
        for h in handlers:
            try:
                res = h(payload)
                if asyncio.iscoroutine(res):
                    coros.append(res)
            except Exception:
                # swallow to avoid breaking the stream
                pass
        if coros:
            await asyncio.gather(*coros, return_exceptions=True)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._subs.setdefault(topic, []).append(handler)

    async def publish(self, topic: str, payload: Any) -> None:
        await self._ensure()
        assert self.nc
        body = json.dumps(to_jsonable(payload)).encode("utf-8")
        await self.nc.publish(topic, body)
