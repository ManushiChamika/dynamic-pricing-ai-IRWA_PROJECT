from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable, List, Optional
from .agent_sdk.bus_factory import get_bus
from .agent_sdk.protocol import Topic
from .agent_sdk.events_models import MarketTick, PriceProposal, AlertEvent

@dataclass
class Thresholds:
    undercut_delta: float = 0.01
    demand_spike: float = 0.80
    min_margin: float = 0.10

class AlertNotifier:
    name = "alert_notifier"
    def __init__(self, thresholds: Thresholds | None = None,
                 sinks: Optional[List[Callable[[AlertEvent], Awaitable[None]]]] = None):
        self.thresholds = thresholds or Thresholds()
        self.sinks = sinks or []

    async def start(self):
        async def on_tick(tick: MarketTick):
            t = self.thresholds
            if tick.competitor_price and tick.competitor_price * (1 + t.undercut_delta) < tick.our_price:
                await self._emit("UNDERCUT", f"Competitor {tick.competitor_price} < our {tick.our_price}", "warn", tick.sku)
            if tick.demand_index >= t.demand_spike:
                await self._emit("DEMAND_SPIKE", f"Demand spike index={tick.demand_index}", "info", tick.sku)
        async def on_prop(pp: PriceProposal):
            if pp.margin < self.thresholds.min_margin:
                await self._emit("MARGIN_BREACH", f"Proposed {pp.proposed_price} margin {pp.margin:.2%}", "crit", pp.sku)

        bus = get_bus()
        bus.subscribe(Topic.MARKET_TICK.value, on_tick)
        bus.subscribe(Topic.PRICE_PROPOSAL.value, on_prop)

    async def _emit(self, kind, message, severity, sku):
        alert = AlertEvent(sku=sku, kind=kind, message=message, severity=severity, ts=datetime.utcnow())
        bus = get_bus()
        await bus.publish(Topic.ALERT.value, alert)
        for s in self.sinks:
            await s(alert)
