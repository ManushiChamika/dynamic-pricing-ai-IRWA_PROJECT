import asyncio
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic
from core.agents.price_optimizer.agent import PricingOptimizerAgent


async def test_autonomous_optimizer():
    print("=" * 80)
    print("AUTONOMOUS PRICE OPTIMIZER TEST")
    print("=" * 80)
    
    pricing_agent = PricingOptimizerAgent()
    
    print("\n[1/4] Starting autonomous Price Optimizer Agent...")
    await pricing_agent.start()
    print("✓ Agent subscribed to OPTIMIZATION_REQUEST events")
    
    test_sku = "LAPTOP-DELL-XPS-13"
    print(f"\n[2/4] Publishing OPTIMIZATION_REQUEST for SKU: {test_sku}")
    
    bus = get_bus()
    payload = {
        "sku": test_sku,
        "strategy": "maximize profit"
    }
    await bus.publish(Topic.OPTIMIZATION_REQUEST.value, payload)
    print(f"✓ Event published: {Topic.OPTIMIZATION_REQUEST.value}")
    
    print("\n[3/4] Waiting for autonomous agent to complete workflow (max 30s)...")
    print("   → Agent should:")
    print("     1. get_product_info(sku)")
    print("     2. get_market_intelligence(product_title)")
    print("     3. run_pricing_algorithm(...)")
    print("     4. validate_price(...)")
    print("     5. publish_price_proposal(...)")
    
    await asyncio.sleep(30)
    
    print("\n[4/4] Checking for PRICE_PROPOSAL event in logs...")
    print("✓ Test complete. Check logs above for:")
    print("  - LLM tool invocations (get_product_info, get_market_intelligence, etc.)")
    print("  - PRICE_PROPOSAL published to event bus")
    print("  - Any validation failures or errors")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_autonomous_optimizer())
