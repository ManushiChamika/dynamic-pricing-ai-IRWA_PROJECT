"""
Test User Interaction Agent -> Price Optimizer Agent Integration

This test verifies that when a user requests price optimization through the
User Interaction Agent, it properly triggers the autonomous Price Optimizer
Agent with the new market data collection integration.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).parent
sys.path.insert(0, str(root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_user_interaction_optimization():
    """Test the full user interaction -> price optimization workflow."""
    
    print("\n" + "="*70)
    print("Testing User Interaction -> Price Optimizer Integration")
    print("="*70)
    
    # Import required components
    from core.agents.user_interact.tools import optimize_price
    from core.agents.price_optimizer.agent import PricingOptimizerAgent
    from core.agents.agent_sdk.bus_factory import get_bus
    from core.agents.agent_sdk.protocol import Topic
    
    # Test SKU
    test_sku = "ASUS-ProArt-4910S"
    
    print(f"\n📦 Test Product: {test_sku}")
    print("-" * 70)
    
    # Initialize Price Optimizer Agent to listen for events
    print("\n1️⃣ Starting Price Optimizer Agent...")
    optimizer_agent = PricingOptimizerAgent()
    await optimizer_agent.start()
    print("   ✅ Price Optimizer Agent is listening for OPTIMIZATION_REQUEST events")
    
    # Give the agent a moment to subscribe
    await asyncio.sleep(1)
    
    # Trigger optimization via User Interaction tool
    print(f"\n2️⃣ Triggering optimization via optimize_price() tool...")
    result = optimize_price(test_sku)
    
    if result.get("ok"):
        print(f"   ✅ Optimization request sent successfully!")
        print(f"   📝 Message: {result.get('message', '').splitlines()[0]}")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return
    
    # Wait for the autonomous workflow to complete
    print(f"\n3️⃣ Waiting for autonomous workflow to complete...")
    print("   🔄 The Price Optimizer Agent will:")
    print("      • Check market data freshness")
    print("      • Trigger data collection if needed")
    print("      • Run pricing algorithm")
    print("      • Publish price proposal")
    
    # Wait longer to allow for data collection
    for i in range(6):
        await asyncio.sleep(5)
        print(f"   ⏳ Elapsed: {(i+1)*5} seconds...")
    
    # Check if proposal was created
    print(f"\n4️⃣ Checking for price proposals...")
    from core.agents.user_interact.tools import list_price_proposals
    
    proposals_result = list_price_proposals(sku=test_sku, limit=5)
    
    if proposals_result.get("items"):
        proposals = proposals_result["items"]
        latest = proposals[0]
        
        print(f"   ✅ Found {len(proposals)} proposal(s) for {test_sku}!")
        print(f"\n   📊 Latest Proposal:")
        print(f"      • SKU: {latest.get('sku')}")
        print(f"      • Current Price: LKR {latest.get('current_price', 0):,.2f}")
        print(f"      • Proposed Price: LKR {latest.get('proposed_price', 0):,.2f}")
        print(f"      • Algorithm: {latest.get('algorithm')}")
        print(f"      • Margin: {latest.get('margin', 0)*100:.2f}%")
        print(f"      • Timestamp: {latest.get('ts')}")
        
    elif proposals_result.get("message"):
        print(f"   ⚠️  {proposals_result['message']}")
    else:
        print(f"   ❌ Error: {proposals_result.get('error')}")
    
    print("\n" + "="*70)
    print("Test Complete!")
    print("="*70 + "\n")


async def main():
    try:
        await test_user_interaction_optimization()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
