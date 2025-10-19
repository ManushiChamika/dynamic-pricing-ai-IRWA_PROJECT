import asyncio
import logging
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from core.agents.data_collector.repo import DataRepo
from core.agents.data_collector.agent import DataCollectorAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("autonomous_test")


async def main():
    logger.info("Starting autonomous data collector test...")
    
    db_path = root / "data" / "market.db"
    repo = DataRepo(db_path)
    
    agent = DataCollectorAgent(
        repo=repo,
        check_interval_seconds=30
    )
    
    await agent.start()
    
    logger.info("Agent started - will run autonomous checks every 30 seconds")
    logger.info("Press Ctrl+C to stop...")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
