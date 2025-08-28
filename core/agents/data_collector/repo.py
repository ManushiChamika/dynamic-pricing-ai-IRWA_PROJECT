# core/agents/data_collector/repo.py
import aiosqlite
from datetime import datetime, timezone
from typing import Dict, Any, List

class DataRepo:
    def __init__(self, path: str = "app/data.db"):
        self.path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.executescript("""
            CREATE TABLE IF NOT EXISTS market_ticks (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              sku TEXT NOT NULL,
              market TEXT NOT NULL,
              our_price REAL NOT NULL,
              competitor_price REAL,
              demand_index REAL,
              ts TEXT NOT NULL,
              source TEXT,
              ingested_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS ix_ticks_sku_market_ts
                ON market_ticks (sku, market, ts);
            """)
            await db.commit()

    async def insert_tick(self, d: Dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT INTO market_ticks
                 (sku, market, our_price, competitor_price, demand_index,
                  ts, source, ingested_at)
                 VALUES (?,?,?,?,?,?,?,?)""",
                (
                    d["sku"], d.get("market", "DEFAULT"),
                    float(d["our_price"]), d.get("competitor_price"),
                    d.get("demand_index"), d["ts"], d.get("source", "mock"),
                    now
                ),
            )
            await db.commit()

    async def recent_ticks(self, sku: str, market: str, limit: int = 50) -> List[Dict[str, Any]]:
        q = ("SELECT our_price, competitor_price, demand_index, ts "
             "FROM market_ticks WHERE sku=? AND market=? "
             "ORDER BY ts DESC LIMIT ?")
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(q, (sku, market, limit))
            rows = await cur.fetchall()
        return [{"our_price": r[0], "competitor_price": r[1], "demand_index": r[2], "ts": r[3]} for r in rows]
