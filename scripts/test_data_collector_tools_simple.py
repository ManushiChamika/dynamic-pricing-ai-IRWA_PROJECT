import asyncio
import logging
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from core.agents.data_collector.repo import DataRepo
from core.agents.data_collector.tools import Tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("tools_test")


async def main():
    logger.info("Testing Data Collector tools...")
    
    repo = DataRepo()
    logger.info(f"Using database: {repo.path}")
    
    tools = Tools(repo)
    
    logger.info("\n=== Testing get_all_products ===")
    result = await tools.get_all_products()
    if result.get("ok"):
        logger.info(f"Found {result['count']} products")
        if result['products']:
            logger.info(f"Sample product: {result['products'][0]}")
    else:
        logger.error(f"Error: {result.get('error')}")
    
    logger.info("\n=== Testing get_stale_products ===")
    result = await tools.get_stale_products(threshold_minutes=60)
    if result.get("ok"):
        logger.info(f"Found {result['count']} stale products (>60 min old)")
        for p in result['stale_products'][:3]:
            logger.info(f"  - {p['sku']}: {p['title']} (last update: {p['last_update']})")
    else:
        logger.error(f"Error: {result.get('error')}")
    
    logger.info("\n=== Testing get_active_jobs ===")
    result = await tools.get_active_jobs()
    if result.get("ok"):
        logger.info(f"Found {result['count']} active jobs")
    else:
        logger.error(f"Error: {result.get('error')}")
    
    logger.info("\n=== Testing get_recent_jobs ===")
    result = await tools.get_recent_jobs(limit=5)
    if result.get("ok"):
        logger.info(f"Found {result['count']} recent jobs")
        for j in result['recent_jobs']:
            logger.info(f"  - {j['id'][:8]}... {j['sku']}: {j['status']}")
    else:
        logger.error(f"Error: {result.get('error')}")
    
    logger.info("\nAll tool tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
