# scripts/smoke_event_driven.py
"""Smoke test for the new event-driven data collection architecture."""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Ensure repo root on sys.path for module imports
from pathlib import Path as _Path0
import sys as _sys0
_root0 = _Path0(__file__).resolve().parents[1]
if str(_root0) not in _sys0.path:
    _sys0.path.insert(0, str(_root0))

from core.agents.price_optimizer.agent import PricingOptimizerAgent
from core.agents.data_collector.collector import DataCollector
from core.agents.data_collector.repo import DataRepo
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic


SKU = "TEST-SKU-EVENT"


async def setup_test_data():
    """Set up test data in app/data.db."""
    repo = DataRepo("app/data.db")
    await repo.init()
    
    # Add a test product to catalog
    await repo.upsert_products([{
        "sku": SKU,
        "title": "Test Product",
        "currency": "USD", 
        "current_price": 100.0,
        "cost": 80.0,
        "stock": 50
    }], owner_id="1")
    
    return repo


async def run_smoke() -> int:
    """Run the smoke test."""
    print("Starting event-driven smoke test...")
    
    # Setup
    repo = await setup_test_data()
    
    # Initialize data collector (sets up subscriptions)
    collector = DataCollector(repo)
    
    # Track events
    events: List[Dict[str, Any]] = []
    
    def _on_proposal(msg):
        events.append(("price.proposal", msg))
        print("BUS price.proposal:", msg)
    
    def _on_fetch_ack(msg):
        events.append(("market.fetch.ack", msg))
        print("BUS market.fetch.ack:", msg)
        
    def _on_fetch_done(msg):
        events.append(("market.fetch.done", msg))
        print("BUS market.fetch.done:", msg)
    
    def _on_market_tick(msg):
        events.append(("market.tick", msg))
        print("BUS market.tick:", msg)
    
    bus = get_bus()
    bus.subscribe(Topic.PRICE_PROPOSAL.value, _on_proposal)
    bus.subscribe(Topic.MARKET_FETCH_ACK.value, _on_fetch_ack)
    bus.subscribe(Topic.MARKET_FETCH_DONE.value, _on_fetch_done)
    bus.subscribe(Topic.MARKET_TICK.value, _on_market_tick)
    
    # Test the pricing optimizer with URL (should trigger data fetch)
    agent = PricingOptimizerAgent()
    test_url = "https://example.com/product/123"  # Mock URL
    user_request = f"get competitor price from {test_url} and maximize profit"
    
    try:
        res = await agent.process_full_workflow(user_request, SKU, db_path="app/data.db")
        print("optimizer_result:", res)
        
        if not isinstance(res, dict):
            print("FAIL: optimizer returned non-dict:", res)
            return 1
        
        # Check if it's a successful result (folder-based version returns "ok")
        if res.get("status") == "ok":
            print("SUCCESS: Got price recommendation")
        elif res.get("status") == "error":
            print("FAIL: optimizer returned error:", res.get("message"))
            return 1
        else:
            print("UNEXPECTED: Unknown status:", res.get("status"))
        
        # Wait a bit for async events to process
        await asyncio.sleep(1)
        
        # Verify we got some events
        print(f"Captured {len(events)} events:")
        for event_type, payload in events:
            print(f"  {event_type}: {payload}")
        
        # Should have at least a price proposal
        proposal_events = [e for e in events if e[0] == "price.proposal"]
        if not proposal_events:
            print("FAIL: no price.proposal events captured")
            return 1
        
        print("SMOKE PASS")
        return 0
        
    except Exception as e:
        print(f"FAIL: Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_smoke())
    raise SystemExit(exit_code)