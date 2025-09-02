# scripts/seed_fakestore_products.py
import os
import asyncio
import httpx
from datetime import datetime, timezone
from core.agents.data_collector.repo import DataRepo

FAKESTORE_URL = "https://fakestoreapi.com/products"

async def main():
    # Use DATA_DB if set, else default to app/data.db
    db_path = os.getenv("DATA_DB", os.path.join("app", "data.db"))
    repo = DataRepo(db_path=db_path)

    # Ensure tables exist
    await repo.init()

    # Pull 20 fake products
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(FAKESTORE_URL)
        r.raise_for_status()
        items = r.json()

    # Map to your products schema (sku = FS-{id})
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for it in items:
        sku = f"FS-{it['id']}"
        rows.append({
            "sku": sku,
            "market": "DEFAULT",
            "name": it.get("title"),
            "cost": None,
            "base_price": it.get("price"),
            "currency": "USD",
            "updated_at": now,
        })

    res = await repo.upsert_products(rows)
    print(f"Seeded {res.get('count', 0)} products into products table ({db_path})")

if __name__ == "__main__":
    asyncio.run(main())
