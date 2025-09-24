from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from core.agents.agent_sdk.bus_factory import get_bus as _get_bus
from core.agents.agent_sdk.protocol import Topic
from core.agents.agent_sdk.events_models import MarketTick
from .repo import DataRepo

# Optional legacy agent SDK bus for backward compatibility.
# If available, we will dual-publish the raw dict payload to the legacy bus/topic.
try:  # Safe import; legacy module may not exist in all environments
    from core.agents.agent_sdk import get_bus as get_legacy_bus, Topic as LegacyTopic
except Exception:
    get_legacy_bus = None  # type: ignore[assignment]
    LegacyTopic = None  # type: ignore[assignment]


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
        # Publish MARKET_TICK as a typed dataclass on the global bus so downstream
        # consumers (e.g., AlertNotifier) receive the expected structure.
        competitor_price_value = payload.get("competitor_price")
        comp_price: Optional[float] = (
            float(competitor_price_value) if competitor_price_value is not None else None
        )
        demand_index_value = float(payload.get("demand_index") or 0.0)

        tick = MarketTick(
            sku=payload["sku"],
            our_price=payload["our_price"],
            competitor_price=comp_price,
            demand_index=demand_index_value,
        )
        await _get_bus().publish(Topic.MARKET_TICK.value, tick)

        # Best-effort legacy publish for backward compatibility.
        # If the legacy bus exists, also publish the original dict payload; ignore errors.
        if get_legacy_bus is not None and LegacyTopic is not None:
            try:
                legacy_bus = get_legacy_bus()
                res = legacy_bus.publish(LegacyTopic.MARKET_TICK.value, payload)
                # Handle both coroutine and sync publish implementations.
                import asyncio as _asyncio

                if _asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                # Non-fatal: continue if legacy publish fails.
                try:
                    print(f"[DataCollector] Legacy bus publish failed: {e}")
                except Exception:
                    pass

    async def ingest_stream(
        self, it: Iterable[Dict[str, Any]], delay_s: float = 1.0
    ) -> None:
        import asyncio

        for d in it:
            await self.ingest_tick(d)
            await asyncio.sleep(delay_s)


