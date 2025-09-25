# core/agents/data_collector/collector.py
from __future__ import annotations

import asyncio
import inspect
from typing import Any, AsyncIterable, Iterable, Optional, Tuple, TYPE_CHECKING

from core.agents.agent_sdk.bus_factory import get_bus as _get_bus
from core.agents.agent_sdk.protocol import Topic
from core.agents.agent_sdk.events_models import MarketTick
from .repo import DataRepo

if TYPE_CHECKING:
    # Optional for type checkers; not required at runtime
    from core.models import MarketTick  # noqa: F401


def _normalize_tick(item: Any) -> Tuple[str, float, str, str, Optional[float], Optional[float], Optional[str]]:
    """
    Normalize an incoming tick-like value to a canonical tuple:

        (sku, our_price, source, market, competitor_price, demand_index, ts)

    Accepted shapes:
      • Dict with keys like:
          sku/symbol/sym/product_id/ticker,
          our_price/price/px/unit_price,
          source/src,
          market,
          competitor_price, demand_index, ts
      • Tuple/List:
          (sku, price)
          (sku, price, source, market, competitor_price, demand_index, ts)
      • "Tick-like" object (duck-typed) with attributes:
          .sku or .symbol, .our_price or .price, optional .source/.market/.competitor_price/.demand_index/.ts
    """
    # Duck-typed object (avoid hard dependency on ORM class)
    if hasattr(item, "sku") or hasattr(item, "symbol"):
        sku = getattr(item, "sku", None) or getattr(item, "symbol", None)
        price = getattr(item, "our_price", None) or getattr(item, "price", None)
        source = getattr(item, "source", "mock")
        market = getattr(item, "market", "DEFAULT")
        comp = getattr(item, "competitor_price", None)
        dem = getattr(item, "demand_index", None)
        ts = getattr(item, "ts", None)
        if sku is None or price is None:
            raise ValueError(f"Tick object missing sku/price: {item!r}")
        return str(sku), float(price), str(source), str(market), comp, dem, ts

    # dict-like
    if isinstance(item, dict):
        sku = (
            item.get("sku")
            or item.get("symbol")
            or item.get("sym")
            or item.get("product_id")
            or item.get("ticker")
        )
        price = (
            item.get("our_price")
            or item.get("price")
            or item.get("px")
            or item.get("unit_price")
        )
        source = item.get("source") or item.get("src") or "mock"
        market = item.get("market") or "DEFAULT"
        comp = item.get("competitor_price")
        dem = item.get("demand_index")
        ts = item.get("ts")
        if sku is None or price is None:
            raise ValueError(f"Tick dict missing sku/price fields: {item}")
        return str(sku), float(price), str(source), str(market), comp, dem, ts

    # tuple/list
    if isinstance(item, (tuple, list)):
        # Minimal: (sku, price)
        if len(item) == 2:
            sku, price = item
            return str(sku), float(price), "mock", "DEFAULT", None, None, None
        # Up to 7 fields
        sku = item[0]
        price = item[1]
        source = item[2] if len(item) > 2 else "mock"
        market = item[3] if len(item) > 3 else "DEFAULT"
        comp = item[4] if len(item) > 4 else None
        dem = item[5] if len(item) > 5 else None
        ts = item[6] if len(item) > 6 else None
        return str(sku), float(price), str(source), str(market), comp, dem, ts

    raise ValueError(f"Unsupported tick shape: {type(item)} -> {item!r}")


class DataCollector:
    """
    Async-friendly collector that writes ticks via DataRepo.

    Key methods:
      • ingest(...)       : insert a single normalized tick
      • ingest_any(obj)   : accept dict/tuple/object and normalize internally
      • ingest_batch(iter): insert from a synchronous iterable
      • ingest_stream(gen): insert from a sync or async generator/iterable
    """

    def __init__(self, repo: Optional[DataRepo] = None) -> None:
        self.repo = repo or DataRepo()
        # cache insert_tick signature for robust calling on older shims
        self._insert_sig = inspect.signature(self.repo.insert_tick)

    async def ingest(
        self,
        sku: str,
        price: float,
        source: str = "mock",
        market: str = "DEFAULT",
        competitor_price: Optional[float] = None,
        demand_index: Optional[float] = None,
        ts: Optional[str] = None,
    ) -> Any:
        """
        Insert one tick using DataRepo.
        Tries canonical kwargs first; falls back to dict-style if needed.
        """
        fn = self.repo.insert_tick
        try:
            # canonical async DataRepo signature
            return await fn(
                sku=sku,
                our_price=price,
                source=source,
                market=market,
                competitor_price=competitor_price,
                demand_index=demand_index,
                ts=ts,
            )
        except TypeError:
            # Fallback for legacy signatures: call helper or pass a single dict
            tick = {
                "sku": sku,
                "our_price": price,
                "source": source,
                "market": market,
                "competitor_price": competitor_price,
                "demand_index": demand_index,
                "ts": ts,
            }
            if hasattr(self.repo, "insert_tick_dict"):
                return await getattr(self.repo, "insert_tick_dict")(tick)
            return await fn(tick)  # type: ignore[misc]

    async def ingest_tick(self, d: dict) -> Any:
        """
        Helper used by tools/APIs that already supply a dict.
        """
        if hasattr(self.repo, "insert_tick_dict"):
            return await getattr(self.repo, "insert_tick_dict")(d)
        # Normalize to kwargs if insert_tick_dict not available
        sku, price, source, market, comp, dem, ts = _normalize_tick(d)
        return await self.ingest(
            sku=sku,
            price=price,
            source=source,
            market=market,
            competitor_price=comp,
            demand_index=dem,
            ts=ts,
        )

    async def ingest_any(self, tick_like: Any) -> Any:
        """
        Accept any supported tick shape, normalize it, and insert via repo.
        Also publishes a MarketTick on the async bus for live consumers.
        """
        sku, price, source, market, comp, dem, ts = _normalize_tick(tick_like)
        res = await self.ingest(
            sku=sku,
            price=price,
            source=source,
            market=market,
            competitor_price=comp,
            demand_index=dem,
            ts=ts,
        )
        try:
            mt = MarketTick(
                sku=sku,
                our_price=price,
                competitor_price=(comp if comp is not None else None),
                demand_index=(float(dem) if dem is not None else 0.0),
            )
            await _get_bus().publish(Topic.MARKET_TICK.value, mt)
        except Exception:
            pass
        return res



    async def ingest_batch(self, ticks: Iterable[Any]) -> int:
        """
        Insert many ticks from a normal (synchronous) iterable.
        """
        count = 0
        for t in ticks:
            await self.ingest_any(t)
            count += 1
        return count

    async def ingest_stream(
        self,
        agen: AsyncIterable[Any] | Iterable[Any],
        delay_s: Optional[float] = None,
    ) -> int:
        """
        Ingest from either:
          • a synchronous iterable (list/generator), or
          • an async iterable/generator.

        Adds an optional delay between inserts to simulate pacing.
        """
        inserted = 0

        # Async iterable/generator path
        if hasattr(agen, "__aiter__") or inspect.isasyncgen(agen):
            async for t in agen:  # type: ignore[arg-type]
                await self.ingest_any(t)
                inserted += 1
                if delay_s:
                    await asyncio.sleep(delay_s)
            return inserted

        # Sync iterable path
        for t in agen:  # type: ignore[assignment]
            await self.ingest_any(t)
            inserted += 1
            if delay_s:
                await asyncio.sleep(delay_s)

        return inserted
