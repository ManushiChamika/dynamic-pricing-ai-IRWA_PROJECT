from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

import aiosqlite


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DataRepo:
    """
    Minimal repo for market ticks. Uses SQLite at DATA_DB or app/data.db.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        db_env = os.getenv("DATA_DB", "app/data.db")
        self.path = Path(path or db_env)

    async def init(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path.as_posix()) as db:
            await db.executescript(
                """
                PRAGMA journal_mode=WAL;

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
                """
            )
            await db.commit()

    async def insert_tick(self, d: Dict[str, Any]) -> None:
        # Expect ISO ts; if missing, use now
        ts = d.get("ts") or _utc_now_iso()
        async with aiosqlite.connect(self.path.as_posix()) as db:
            await db.execute(
                """
                INSERT INTO market_ticks
                  (sku, market, our_price, competitor_price, demand_index, ts,
                   source, ingested_at)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    d["sku"],
                    d.get("market", "DEFAULT"),
                    float(d["our_price"]),
                    d.get("competitor_price"),
                    d.get("demand_index"),
                    ts,
                    d.get("source", "unknown"),
                    _utc_now_iso(),
                ),
            )
            await db.commit()

    async def features_for(
        self, sku: str, market: str, since_iso: str
    ) -> Dict[str, Any]:
        """
        Return simple recent features for a window: latest values + basic gap.
        """
        q = """
        SELECT our_price, competitor_price, demand_index, ts
        FROM market_ticks
        WHERE sku=? AND market=? AND ts>=?
        ORDER BY ts DESC
        LIMIT 100
        """
        async with aiosqlite.connect(self.path.as_posix()) as db:
            cur = await db.execute(q, (sku, market, since_iso))
            rows = await cur.fetchall()

        if not rows:
            return {
                "snapshot_id": None,
                "as_of": None,
                "features": {},
                "provenance": [],
                "count": 0,
            }

        # Latest row
        our_latest, comp_latest, dem_latest, as_of = rows[0]
        gap_pct = None
        if our_latest and comp_latest is not None:
            try:
                gap_pct = (our_latest - comp_latest) / our_latest if our_latest else None
            except ZeroDivisionError:
                gap_pct = None

        return {
            "snapshot_id": f"snap:{sku}:{market}:{as_of}",
            "as_of": as_of,
            "features": {
                "our_price": our_latest,
                "competitor_price": comp_latest,
                "demand_index": dem_latest,
                "price_gap_pct": gap_pct,
            },
            "provenance": ["market_ticks"],
            "count": len(rows),
        }


