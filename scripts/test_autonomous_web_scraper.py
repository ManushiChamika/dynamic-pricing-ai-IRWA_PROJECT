import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agents.data_collector.agent import DataCollectorAgent
from core.agents.data_collector.repo import DataRepo

async def test_autonomous_collector():
    print("=== Testing Autonomous Data Collector with Web Scraper ===\n")
    
    repo = DataRepo("app/data.db")
    agent = DataCollectorAgent(repo)
    
    print("1. Running autonomous check...")
    result = await agent._handle_autonomous_check()
    
    print(f"\n2. Cycle result:")
    print(f"   Status: {result.get('status')}")
    print(f"   Jobs started: {result.get('jobs_started', 0)}")
    print(f"   Message: {result.get('message')}")
    
    if result.get("stale_products"):
        print(f"\n3. Stale products identified:")
        for product in result["stale_products"][:5]:
            print(f"   - {product['sku']}: {product['title']}")
            print(f"     Stale for: {product.get('minutes_stale', 'unknown')} minutes")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_autonomous_collector())
