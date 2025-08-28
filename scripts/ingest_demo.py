# scripts/ingest_demo.py
"""
Run a small demo ingestion using the mock connector.
Usage: python scripts/ingest_demo.py
"""
import asyncio
import os, sys
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)

from core.agents.data_collector.repo import DataRepo
from core.agents.data_collector.collector import DataCollector
from core.agents.data_collector.connectors.mock import mock_ticks

async def main():
    repo = DataRepo(path="app/data.db")
    await repo.init()
    coll = DataCollector(repo)
    for tick in mock_ticks(n=8):
        await coll.ingest_tick(tick)
    print("Ingest demo completed.")

if __name__ == "__main__":
    asyncio.run(main())
