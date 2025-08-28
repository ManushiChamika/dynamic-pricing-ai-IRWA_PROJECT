# core/agents/data_collector/collector.py
from datetime import datetime, timezone
from typing import Dict, Any, Iterable
from core.agents.agent_sdk import get_bus, Topic
from .repo import DataRepo

bus = get_bus()

class DataCollector:
    def __init__(self, repo: DataRepo):
        self.repo = repo

    async def ingest_tick(self, d: Dict[str, Any]) -> None:
        payload = {
            "sku": d["sku"],
            "market": d.get("market", "DEFAULT"),
            "our_price": float(d["our_price"]),
            "competitor_price": d.get("competitor_price"),
            "demand_index": d.get("demand_index"),
            "ts": d.get("ts") or datetime.now(timezone.utc).isoformat(),
            "source": d.get("source", "mock"),
        }
        await self.repo.insert_tick(payload)
        await bus.publish(Topic.MARKET_TICK.value, payload)

    async def ingest_stream(self, it: Iterable[Dict[str, Any]], delay_s: float = 0.0):
        import asyncio
        for d in it:
            await self.ingest_tick(d)
            if delay_s:
                await asyncio.sleep(delay_s)
