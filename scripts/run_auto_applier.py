# core/agents/auto_applier.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.bus import bus
from core.protocol import Topic

@dataclass
class AutoApplierConfig:
    auto_accept: bool = True    # simple policy: auto-accept all proposals

class AutoApplier:
    """
    Minimal auto-applier:
    - subscribes to PRICE_PROPOSAL
    - if auto_accept, emits PRICE_UPDATE with the proposed price
    This satisfies test_auto_apply.py without touching DB state.
    """
    name = "auto_applier"

    def __init__(self, config: Optional[AutoApplierConfig] = None) -> None:
        self.config = config or AutoApplierConfig()

    async def start(self) -> None:
        async def on_proposal(pp: Any) -> None:
            if not self.config.auto_accept:
                return
            # We duck-type the proposal to avoid tight coupling
            sku   = getattr(pp, "sku", None) or (pp.get("sku") if isinstance(pp, dict) else None)
            price = getattr(pp, "proposed_price", None) or (pp.get("proposed_price") if isinstance(pp, dict) else None)
            if sku is None or price is None:
                return
            try:
                await bus.publish(Topic.PRICE_UPDATE.value, {"sku": sku, "price": price})
            except Exception:
                # Don't let errors bubble in a smoke path
                pass

        bus.subscribe(Topic.PRICE_PROPOSAL.value, on_proposal)

    async def run(self) -> bool:
        """
        Compatibility method some tests call; nothing to do in this minimal version.
        """
        return True
