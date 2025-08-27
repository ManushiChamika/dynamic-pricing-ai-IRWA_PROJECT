# core/agents/simulators/demo_publishers.py
import asyncio
from dataclasses import dataclass, asdict, field
from datetime import datetime as dt, timezone
from typing import Optional

# Correct imports: use the core.agent_sdk modules directly
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic

# Initialize a shared bus instance
bus = get_bus()

# Minimal event shapes for the demo (engine uses getattr + dict conversion)
@dataclass
class MarketTick:
    sku: str
    our_price: float
    competitor_price: Optional[float]
    demand_index: float
    ts: dt

@dataclass
class PriceProposal:
    sku: str
    proposed_price: float
    cost: Optional[float] = None
    margin: Optional[float] = None
    # timezone-aware by default
    ts: dt = field(default_factory=lambda: dt.now(timezone.utc))

    def __post_init__(self):
        if self.margin is None and self.cost is not None and self.proposed_price:
            self.margin = (self.proposed_price - self.cost) / self.proposed_price
        if self.margin is None:
            self.margin = 0.0

# Helpers to serialize if any consumer expects dict-like payloads
def _to_dict(obj):
    try:
        return obj.model_dump()
    except Exception:
        pass
    try:
        return asdict(obj)
    except Exception:
        pass
    return getattr(obj, "__dict__", {}) or {}

async def simulate_undercut(
    sku: str = "SKU-123",
    our: float = 100.0,
    comp: float = 98.0,
    seconds: float = 30,
    hz: float = 1.0,
) -> None:
    """
    Competitor undercuts enough to satisfy rule:
    tick.competitor_price * 1.02 < tick.our_price
    98 * 1.02 = 99.96 < 100 -> True
    """
    loop = asyncio.get_running_loop()
    end = loop.time() + float(seconds)
    period = 1.0 / float(hz) if hz else 1.0
    while loop.time() < end:
        tick = MarketTick(
            sku=sku,
            our_price=our,
            competitor_price=comp,
            demand_index=0.50,
            ts=dt.now(timezone.utc),
        )
        await bus.publish(Topic.MARKET_TICK.value, tick)
        await asyncio.sleep(period)

async def simulate_demand_spike(
    sku: str = "SKU-123",
    spike: float = 0.95,
    seconds: float = 30,
    hz: float = 1.0,
) -> None:
    """
    Demand meets the seeded rule where="tick.demand_index >= 0.95".
    """
    loop = asyncio.get_running_loop()
    end = loop.time() + float(seconds)
    period = 1.0 / float(hz) if hz else 1.0
    while loop.time() < end:
        tick = MarketTick(
            sku=sku,
            our_price=100.0,
            competitor_price=100.0,
            demand_index=spike,
            ts=dt.now(timezone.utc),
        )
        await bus.publish(Topic.MARKET_TICK.value, tick)
        await asyncio.sleep(period)

async def simulate_margin_breach(
    sku: str = "SKU-123",
    proposed: float = 90.0,
    cost: float = 82.0,
) -> None:
    """
    Violates where="pp.margin < 0.12".
    margin = (90-82)/90 ≈ 0.089 < 0.12
    """
    pp = PriceProposal(sku=sku, proposed_price=proposed, cost=cost, ts=dt.now(timezone.utc))
    await bus.publish(Topic.PRICE_PROPOSAL.value, pp)
