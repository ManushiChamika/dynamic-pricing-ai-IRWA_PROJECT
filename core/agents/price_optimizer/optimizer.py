import asyncio
from typing import Optional
from core.models import MarketTick, PriceProposal
from core.message_bus import MessageBus
from core.topics import Topic
from core.repositories.proposal_repo import ProposalRepo

class Optimizer:
    """
    Subscribes to MARKET_TICK events and proposes new prices.
    Simple strategy (example): follow competitor by small offset weighted by demand.
    """

    def __init__(self, bus: MessageBus, repo: Optional[ProposalRepo] = None):
        self.bus = bus
        self.repo = repo or ProposalRepo()

    async def run(self):
        q = self.bus.subscribe(Topic.MARKET_TICK)
        while True:
            tick: MarketTick = await q.get()
            # compute proposal
            proposed = self._propose(tick)
            # persist + publish
            self.repo.insert_proposal(proposed.dict())
            await self.bus.publish(Topic.PRICE_PROPOSAL, proposed)

    def _propose(self, tick: MarketTick) -> PriceProposal:
        base = tick.our_price
        comp = tick.competitor_price
        if comp is None:
            # Nudge by demand: if demand high -> small up, else down slightly
            adj = (0.02 if tick.demand_index > 0.6 else -0.01)
            new_price = max(0.01, base * (1.0 + adj))
        else:
            # Blend toward competitor with demand tilt
            weight = 0.7 if tick.demand_index < 0.4 else 0.3
            target = comp * (1.0 + (0.01 if tick.demand_index > 0.6 else -0.005))
            new_price = (1 - weight) * base + weight * target

        # pseudo margin (if we don't know cost yet just compute vs base as proxy)
        margin = max(0.0, (new_price - (base * 0.85)) / new_price)
        return PriceProposal(
            sku=tick.sku,
            proposed_price=round(new_price, 2),
            current_price=base,
            margin=margin,
            algorithm="simple",
            ts=tick.ts,
        )

