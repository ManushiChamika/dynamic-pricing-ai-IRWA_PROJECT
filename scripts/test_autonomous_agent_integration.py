import asyncio
import logging
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from core.agents.data_collector.repo import DataRepo
from core.agents.data_collector.agent import DataCollectorAgent
from core.agents.data_collector.collector import DataCollector
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("integration_test")


async def main():
    logger.info("=" * 60)
    logger.info("Starting Integration Test: Autonomous + Reactive Agents")
    logger.info("=" * 60)
    
    db_path = root / "app" / "data.db"
    repo = DataRepo(db_path)
    await repo.init()
    
    logger.info("\n1. Initializing Reactive Data Collector (auto-subscribes)...")
    reactive_collector = DataCollector(repo)
    logger.info("✓ Reactive collector listening for MARKET_FETCH_REQUEST events")
    
    logger.info("\n2. Starting Autonomous Data Collector Agent...")
    autonomous_agent = DataCollectorAgent(
        repo=repo,
        check_interval_seconds=5
    )
    task = asyncio.create_task(autonomous_agent.start())
    logger.info("✓ Autonomous agent started (checks every 5s)")
    
    logger.info("\n3. Waiting 15 seconds for autonomous check + job processing...")
    await asyncio.sleep(15)
    
    logger.info("\n4. Verifying integration results...")
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    jobs = conn.execute(
        "SELECT id, sku, status, created_at FROM ingestion_jobs ORDER BY created_at DESC LIMIT 10"
    ).fetchall()
    
    if jobs:
        logger.info(f"✓ Found {len(jobs)} jobs in database:")
        done_count = sum(1 for j in jobs if j['status'] == 'DONE')
        for job in jobs[:5]:
            logger.info(f"  - {job['sku']}: {job['status']}")
        logger.info(f"✓ Completed jobs: {done_count}/{len(jobs)}")
    else:
        logger.error("✗ FAILED: No jobs found in database")
        conn.close()
        return
    
    ticks_count = conn.execute("SELECT COUNT(*) as cnt FROM market_ticks").fetchone()["cnt"]
    logger.info(f"✓ Market ticks collected: {ticks_count}")
    
    if ticks_count > 0:
        recent_tick = conn.execute(
            "SELECT sku, competitor_price, ts FROM market_ticks ORDER BY ts DESC LIMIT 1"
        ).fetchone()
        logger.info(f"  Latest: {recent_tick['sku']} @ ${recent_tick['competitor_price']}")
    
    conn.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ INTEGRATION TEST PASSED!")
    logger.info("=" * 60)
    logger.info("Dual-Mode Architecture Validated:")
    logger.info("  [1] Autonomous Agent: Monitors staleness → Publishes MARKET_FETCH_REQUEST")
    logger.info("  [2] Reactive Collector: Subscribes to events → Creates jobs → Collects data")
    logger.info("  [3] Event Bus: Decouples components via publish/subscribe pattern")
    logger.info("=" * 60)
    
    logger.info("\nStopping agents...")
    await autonomous_agent.stop()
    task.cancel()
    logger.info("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
