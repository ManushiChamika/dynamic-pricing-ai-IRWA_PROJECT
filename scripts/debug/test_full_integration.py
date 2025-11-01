"""
End-to-end test: User Interaction Agent -> Price Optimizer Agent -> Data Collector
Tests the full autonomous workflow integration.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_full_integration():
    """Test the complete autonomous optimization workflow"""
    print("\n" + "="*70)
    print(" TESTING: User -> Price Optimizer -> Data Collector Integration")
    print("="*70 + "\n")
    
    # Import components
    from core.agents.price_optimizer.agent import PricingOptimizerAgent
    from core.agents.agent_sdk.bus_factory import get_bus
    from core.agents.agent_sdk.protocol import Topic
    
    print("[1/5] Starting PricingOptimizerAgent...")
    agent = PricingOptimizerAgent()
    await agent.start()
    print("      -> Agent started and listening for optimization requests\n")
    
    # Verify subscription
    bus = get_bus()
    topic = Topic.OPTIMIZATION_REQUEST.value
    subscribers = bus._subs.get(topic, [])
    print(f"[2/5] Event bus has {len(subscribers)} subscriber(s) for '{topic}'")
    
    if agent.on_optimization_request not in subscribers:
        print("      [ERROR] Agent not subscribed properly!")
        return
    print("      -> Agent subscription verified\n")
    
    # Send optimization request for real product
    print("[3/5] Publishing OPTIMIZATION_REQUEST for 'ASUS-ProArt-4910S'...")
    test_request = {
        "product_name": "ASUS-ProArt-4910S",
        "sku": "ASUS-ProArt-4910S",
        "user_request": "Optimize price to maximize profit"
    }
    
    await bus.publish(topic, test_request)
    print("      -> Request published to event bus\n")
    
    # Wait for agent to process (includes market data check + optimization)
    print("[4/5] Waiting for autonomous workflow to complete...")
    print("      This may take 30-60 seconds if market data needs collection...")
    print("      Watch the logs above for agent activity\n")
    
    await asyncio.sleep(10)  # Give it time to start processing
    
    print("[5/5] Checking for generated price proposals...")
    
    # Check if proposal was published to database
    import sqlite3
    db_path = root / "app" / "data.db"
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        # Get latest proposal for this product
        row = conn.execute("""
            SELECT sku, current_price, proposed_price, ts
            FROM price_proposals
            WHERE sku = 'ASUS-ProArt-4910S'
            ORDER BY ts DESC
            LIMIT 1
        """).fetchone()
        
        if row:
            print(f"      [SUCCESS] Price proposal generated!")
            print(f"      -> Product: {row['sku']}")
            print(f"      -> Current: ${row['current_price']:,.2f}")
            print(f"      -> Proposed: ${row['proposed_price']:,.2f}")
            print(f"      -> Created: {row['ts']}")
        else:
            print("      [WARN] No proposals found in database yet")
            print("      The agent may still be processing - check logs above")
        
        conn.close()
        
    except Exception as e:
        print(f"      [ERROR] Failed to check proposals: {e}")
    
    print("\n" + "="*70)
    print(" TEST COMPLETE")
    print("="*70 + "\n")
    
    print("Key observations:")
    print("1. Agent should have logged 'Received optimization request'")
    print("2. Agent should check market data freshness")
    print("3. If data is stale, it triggers data collection")
    print("4. Agent runs pricing algorithm and publishes proposal")
    print("\nCheck the logs above to verify the workflow executed correctly!")

if __name__ == "__main__":
    asyncio.run(test_full_integration())
