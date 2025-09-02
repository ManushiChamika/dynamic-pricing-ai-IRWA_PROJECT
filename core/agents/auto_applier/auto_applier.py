# core/agents/auto_applier.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Tuple, List

from core.bus import bus
from core.protocol import Topic

try:
    from core.agents.data_collector.repo import DataRepo
except Exception:  # pragma: no cover
    DataRepo = None  # type: ignore


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Guardrails:
    min_margin: float = 0.10
    max_raise_pct: float = 1.50
    max_drop_pct: float = 0.50


def _validate_price(current: Optional[float],
                    proposed: float,
                    cost: Optional[float],
                    g: Guardrails) -> Tuple[bool, str]:
    if cost is not None and proposed:
        margin = (proposed - cost) / proposed
        if margin < g.min_margin:
            return False, f"margin {margin:.2%} under {g.min_margin:.0%} minimum"
    if current is not None and current > 0:
        if proposed > current * g.max_raise_pct:
            return False, f"raise too large: {proposed} vs current {current}"
        if proposed < current * (1 - g.max_drop_pct):
            return False, f"drop too large: {proposed} vs current {current}"
    return True, "ok"


class AutoApplier:
    """
    Subscribes to PRICE_PROPOSAL, (optionally) validates with guardrails,
    applies to product catalog (if DataRepo available), and publishes PRICE_UPDATE.
    Provides start(), run(), and stop().
    """
    name = "auto_applier"

    def __init__(self, repo: Optional[Any] = None, guardrails: Optional[Guardrails] = None) -> None:
        self.repo = repo or (DataRepo() if DataRepo else None)
        self.g = guardrails or Guardrails()
        self._stopped: bool = False
        self._subs: List[tuple] = []  # (topic, callback, token_or_None)

    async def start(self) -> None:
        if self.repo and hasattr(self.repo, "init"):
            await self.repo.init()
        self._stopped = False

        async def on_proposal(pp: Any) -> None:
            if self._stopped:
                return

            if hasattr(pp, "sku"):
                sku = getattr(pp, "sku")
                market = getattr(pp, "market", "DEFAULT") or "DEFAULT"
                proposed = float(getattr(pp, "proposed_price"))
                current = getattr(pp, "current_price", None)
                ts = getattr(pp, "ts", _utcnow_iso())
            elif isinstance(pp, dict):
                sku = pp.get("sku")
                market = pp.get("market") or "DEFAULT"
                proposed = float(pp.get("proposed_price"))
                current = pp.get("current_price")
                ts = pp.get("ts") or _utcnow_iso()
            else:
                return

            if sku is None or proposed is None:
                return

            cost: Optional[float] = None
            if (current is None or cost is None) and self.repo and hasattr(self.repo, "list_products"):
                try:
                    rows = await self.repo.list_products(market=market)
                    for r in rows:
                        if r.get("sku") == sku:
                            if cost is None:
                                cost = r.get("cost")
                            if current is None:
                                current = r.get("base_price")
                            break
                except Exception:
                    pass

            ok, reason = _validate_price(current, proposed, cost, self.g)
            if not ok:
                try:
                    await bus.publish(Topic.ALERT.value, {
                        "sku": sku, "market": market, "kind": "GUARDRAIL_VIOLATION",
                        "message": reason, "severity": "warn", "ts": ts,
                    })
                except Exception:
                    pass
                return

            if self.repo and hasattr(self.repo, "upsert_products"):
                try:
                    await self.repo.upsert_products([{
                        "sku": sku, "market": market, "base_price": proposed, "updated_at": _utcnow_iso(),
                    }])
                except Exception:
                    pass

            try:
                await bus.publish(Topic.PRICE_UPDATE.value, {
                    "sku": sku, "market": market, "price": proposed, "ts": ts,
                })
            except Exception:
                pass

        token = None
        try:
            token = bus.subscribe(Topic.PRICE_PROPOSAL.value, on_proposal)
        except TypeError:
            bus.subscribe(Topic.PRICE_PROPOSAL.value, on_proposal)
        self._subs.append((Topic.PRICE_PROPOSAL.value, on_proposal, token))

    async def run(self) -> bool:
        await self.start()
        await asyncio.sleep(0)
        return True

    async def stop(self) -> None:
        self._stopped = True
        if hasattr(bus, "unsubscribe"):
            for topic, cb, token in self._subs:
                try:
                    if token is not None:
                        bus.unsubscribe(topic, token)
                    else:
                        bus.unsubscribe(topic, cb)
                except Exception:
                    pass
        self._subs.clear()


__all__ = ["AutoApplier", "Guardrails"]
