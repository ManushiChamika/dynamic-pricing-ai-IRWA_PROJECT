import asyncio
import sys
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agents.data_collector.agent import DataCollectorAgent
from core.agents.data_collector.repo import DataRepo

async def test_autonomous_collector():
    print("=== Testing Autonomous Data Collector with Web Scraper ===\n")
    
    repo = DataRepo("app/data.db")
    agent = DataCollectorAgent(repo)
    
    print("1. Running heuristic check (bypassing LLM rate limits)...")
    await agent._handle_heuristic_check()
    
    print("\n2. Querying database for started jobs...")
    conn = sqlite3.connect("app/data.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, sku, status, created_at 
        FROM ingestion_jobs 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    jobs = cursor.fetchall()
    
    if jobs:
        print(f"   Found {len(jobs)} recent ingestion jobs:")
        for job in jobs:
            print(f"   - Job {job[0]}: SKU={job[1]}, Status={job[2]}, Created={job[3]}")
    else:
        print("   No ingestion jobs found")
    
    print("\n3. Checking market_ticks for scraped data...")
    cursor.execute("""
        SELECT sku, competitor_price, source, ts 
        FROM market_ticks 
        ORDER BY ts DESC 
        LIMIT 10
    """)
    ticks = cursor.fetchall()
    
    if ticks:
        print(f"   Found {len(ticks)} recent market ticks:")
        for tick in ticks:
            price_str = f"${tick[1]}" if tick[1] else "N/A"
            print(f"   - {tick[0]}: {price_str} from {tick[2]} at {tick[3]}")
    else:
        print("   No market ticks found")
    
    conn.close()
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_autonomous_collector())
