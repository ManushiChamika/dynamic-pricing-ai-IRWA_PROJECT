import asyncio
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from core.agents.data_collector.repo import DataRepo
from core.agents.data_collector.tools import Tools

async def test_stale_products():
    print("=== Testing DataCollector Tools ===\n")
    
    repo = DataRepo(root / "app" / "data.db")
    print(f"Using database: {repo.path}\n")
    
    tools = Tools(repo)
    
    print("1. Testing get_all_products()...")
    result = await tools.get_all_products()
    if result["ok"]:
        print(f"   [OK] Found {result['count']} products")
        if result['products']:
            first = result['products'][0]
            print(f"   First product: {first['sku']} - {first['title']}")
            print(f"   Has URL: {bool(first.get('source_url'))}")
    else:
        print(f"   [ERROR] {result['error']}")
    
    print("\n2. Testing get_stale_products()...")
    result = await tools.get_stale_products(threshold_minutes=60)
    if result["ok"]:
        print(f"   [OK] Found {result['count']} stale products")
        if result['stale_products']:
            print(f"\n   Top 5 stalest products:")
            for i, p in enumerate(result['stale_products'][:5], 1):
                has_url = "with URL" if p.get('source_url') else "NO URL"
                stale_time = f"{p.get('minutes_stale', 'N/A'):.0f}min" if p.get('minutes_stale') else "never updated"
                print(f"   {i}. {p['sku']} - {p['title'][:40]} ({has_url}, stale: {stale_time})")
    else:
        print(f"   [ERROR] {result['error']}")
    
    print("\n3. Testing get_active_jobs()...")
    result = await tools.get_active_jobs()
    if result["ok"]:
        print(f"   [OK] Found {result['count']} active jobs")
    else:
        print(f"   [ERROR] {result['error']}")

    print("\n4. Testing MacBook Air M3 data freshness...")
    result = await tools.check_data_freshness("LAPTOP-APPLE-MACBOOK-AIR-M3", "DEFAULT")
    if result["ok"]:
        if result['has_data']:
            print(f"   [OK] Has data - last updated: {result['last_update']}")
            print(f"      Minutes stale: {result['minutes_stale']:.1f}")
            print(f"      Is stale: {result['is_stale']}")
        else:
            print(f"   [WARNING] No market data found for MacBook Air M3")
    else:
        print(f"   [ERROR] {result['error']}")

    print("\n5. Starting a mock collection job for MacBook Air M3...")
    start = await tools.start_collection_job(
        sku="LAPTOP-APPLE-MACBOOK-AIR-M3",
        market="DEFAULT",
        connector="mock",
        depth=3,
    )
    if start.get("ok"):
        print(f"   [OK] Published MARKET_FETCH_REQUEST request_id={start['request_id']}")
    else:
        print(f"   [ERROR] Failed to publish request: {start.get('error')}")

    await asyncio.sleep(0.5)

    print("\n6. Checking recent jobs...")
    recent = await tools.get_recent_jobs(limit=5)
    if recent.get("ok"):
        print(f"   Recent jobs count: {recent['count']}")
        for j in recent["recent_jobs"]:
            print(f"   - {j['id'][:8]} {j['sku']} {j['status']} created={j['created_at']} finished={j['finished_at']}")
    else:
        print(f"   [ERROR] {recent.get('error')}")

    print("\n7. Re-checking data freshness for MacBook Air M3...")
    result2 = await tools.check_data_freshness("LAPTOP-APPLE-MACBOOK-AIR-M3", "DEFAULT")
    if result2.get("ok") and result2.get("has_data"):
        print(f"   [OK] Now has data - last updated: {result2['last_update']}")
    else:
        print("   Still no data; ensure backend is running so collector subscriptions are active.")

if __name__ == "__main__":
    asyncio.run(test_stale_products())

