# scripts/smoke_data_collector.py
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, Iterable

from core.db import init_db, SessionLocal
from core.models import MarketTick
from core.agents.data_collector.collector import DataCollector


def mock_ticks(n: int = 5) -> Iterable[Dict]:
    """
    Simple sync iterable of dicts in a flexible shape (sym/px/src);
    the collector normalizes these.
    """
    for i in range(n):
        yield {
            "sym": f"SKU-{i+1}",                  # 'sym' is OK (collector maps to symbol)
            "px": 10.0 + i,                       # 'px' is OK (collector maps to price)
            "src": "smoke",                       # 'src' is OK (collector maps to source)
            "ts": datetime.utcnow().isoformat(),  # optional
        }


async def main():
    # Ensure tables exist
    init_db()

    # Collector uses TickRepo under the hood
    dc = DataCollector()

    # Ingest a few mock ticks (sync iterable is fine)
    inserted = await dc.ingest_stream(mock_ticks(n=5), delay_s=0.05)
    print(f"[smoke] Inserted {inserted} ticks via DataCollector")

    # Verify we actually wrote rows
    with SessionLocal() as db:
        count = db.query(MarketTick).filter(MarketTick.source == "smoke").count()
        print(f"[smoke] Rows with source='smoke': {count}")
        if count > 0:
            print("SMOKE PASS ✅")
        else:
            print("SMOKE FAIL ❌")
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
