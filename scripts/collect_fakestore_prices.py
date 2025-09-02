# scripts/collect_fakestore_prices.py
import os, asyncio
from core.agents.data_collector.repo import DataRepo
from core.agents.data_collector.connectors import build_connector
from core.agents.data_collector.collector import DataCollector

DB_PATH = os.getenv("DATA_DB", os.path.join("app","data.db"))  # <— use app/data.db by default

repo = DataRepo(DB_PATH)
collector = DataCollector(repo)
conn = build_connector("fakestore")

async def ingest_for_sku(sku: str, depth: int = 40):
    count = 0
    async for row in conn.ticks(sku=sku, market="DEFAULT", depth=depth):
        await collector.ingest_any(row)
        count += 1
    return sku, count

async def main():
    await repo.init()
    skus = [f"FS-{i}" for i in range(1, 20)]
    print("Collecting ticks for:", ", ".join(skus))
    results = await asyncio.gather(*(ingest_for_sku(s, depth=40) for s in skus))
    for sku, n in results:
        print(f"  {sku}: {n} ticks")

if __name__ == "__main__":
    asyncio.run(main())
