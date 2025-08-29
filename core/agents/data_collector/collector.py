from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from core.agents.agent_sdk import get_bus, Topic
from .repo import DataRepo

_bus = get_bus()


class DataCollector:
    def __init__(self, repo: DataRepo):
        self.repo = repo

    async def ingest_tick(self, d: Dict[str, Any]) -> None:
        # Normalize required fields
        payload = {
            "sku": d["sku"],
            "market": d.get("market", "DEFAULT"),
            "our_price": float(d["our_price"]),
            "competitor_price": d.get("competitor_price"),
            "demand_index": d.get("demand_index"),
            "ts": d.get("ts")
            or datetime.now(timezone.utc).isoformat(),
            "source": d.get("source", "manual"),
        }
        await self.repo.insert_tick(payload)
        # Publish MARKET_TICK for live processing/alerts
        await _bus.publish(Topic.MARKET_TICK.value, payload)

    async def ingest_stream(
        self, it: Iterable[Dict[str, Any]], delay_s: float = 1.0
    ) -> None:
        import asyncio

        for d in it:
            await self.ingest_tick(d)
            await asyncio.sleep(delay_s)


