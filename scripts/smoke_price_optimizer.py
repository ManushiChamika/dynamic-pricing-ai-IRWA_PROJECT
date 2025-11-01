# scripts/smoke_price_optimizer.py
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Ensure repo root on sys.path for module imports
from pathlib import Path as _Path0
import sys as _sys0
_root0 = _Path0(__file__).resolve().parents[1]
if str(_root0) not in _sys0.path:
    _sys0.path.insert(0, str(_root0))

from core.agents.price_optimizer.agent import PricingOptimizerAgent
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic
from core.agents.data_collector.repo import DataRepo


SKU = "TEST-SKU"


async def seed_app_db() -> DataRepo:
    repo = DataRepo("app/data.db")
    await repo.init()

    # Ensure product exists
    await repo.upsert_products([
        {
            "sku": SKU,
            "title": "Demo Product",
            "currency": "USD",
            "current_price": 110.0,
            "cost": 80.0,
            "stock": 25,
        }
    ])

    # Seed recent market ticks with competitor prices
    ticks = [
        {"sku": SKU, "market": "DEFAULT", "our_price": 110.0, "competitor_price": 100.0, "demand_index": 0.6, "source": "seed"},
        {"sku": SKU, "market": "DEFAULT", "our_price": 110.0, "competitor_price": 102.0, "demand_index": 0.7, "source": "seed"},
        {"sku": SKU, "market": "DEFAULT", "our_price": 110.0, "competitor_price": 98.0,  "demand_index": 0.65, "source": "seed"},
    ]
    for t in ticks:
        await repo.insert_tick(t)

    return repo


async def run_smoke() -> int:
    await seed_app_db()

    # Capture price.proposal events
    events: List[Dict[str, Any]] = []

    def _on_proposal(msg):
        events.append(msg)
        print("BUS price.proposal:", msg)

    bus = get_bus()
    bus.subscribe(Topic.PRICE_PROPOSAL.value, _on_proposal)

    # Run optimizer end-to-end (governance-enabled; returns a proposal)
    agent = PricingOptimizerAgent()
    res = await agent.process_full_workflow("maximize profit", SKU, db_path="app/data.db")
    print("optimizer_result:", res)

    if not isinstance(res, dict) or res.get("status") != "ok":
        print("FAIL: optimizer did not produce a successful result:", res)
        return 1

    # Verify at least one price.proposal event captured
    if not events:
        print("FAIL: no price.proposal event captured")
        return 1

    # Basic payload validation
    last = events[-1]
    if not isinstance(last, dict) or last.get("product_id") != SKU or "proposed_price" not in last:
        print("FAIL: invalid price.proposal payload:", last)
        return 1

    print("SMOKE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_smoke()))
