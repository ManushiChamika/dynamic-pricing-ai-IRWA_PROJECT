"""
Test script to verify PricingOptimizerAgent startup and event listening.
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

async def test_agent_startup():
    """Test that the PricingOptimizerAgent can start and listen for events"""
    print("\n=== Testing PricingOptimizerAgent Startup ===\n")
    
    # Import after path setup
    from core.agents.price_optimizer.agent import PricingOptimizerAgent
    from core.agents.agent_sdk.bus_factory import get_bus
    from core.agents.agent_sdk.protocol import Topic
    
    print("[OK] Imports successful")
    
    # Create agent
    print("\nCreating PricingOptimizerAgent...")
    agent = PricingOptimizerAgent()
    print("[OK] Agent created")
    
    # Start agent
    print("\nStarting agent...")
    await agent.start()
    print("[OK] Agent started")
    
    # Verify bus subscription
    bus = get_bus()
    topic = Topic.OPTIMIZATION_REQUEST.value
    subscribers = bus._subs.get(topic, [])
    
    print(f"\n[OK] Bus has {len(subscribers)} subscriber(s) for topic '{topic}'")
    
    if agent.on_optimization_request in subscribers:
        print("[OK] Agent's on_optimization_request callback is registered")
    else:
        print("[WARN] Agent's callback NOT found in subscribers!")
    
    # Test event publishing
    print("\nPublishing test OPTIMIZATION_REQUEST event...")
    test_request = {
        "product_name": "ASUS-ProArt-4910S",
        "user_request": "Test optimization request"
    }
    
    await bus.publish(topic, test_request)
    print("[OK] Event published")
    
    # Give agent time to process
    print("\nWaiting 2 seconds for agent to process event...")
    await asyncio.sleep(2)
    
    print("\n=== Test Complete ===")
    print("If you see log messages from PricingOptimizerAgent above, the agent is working!")

if __name__ == "__main__":
    asyncio.run(test_agent_startup())
