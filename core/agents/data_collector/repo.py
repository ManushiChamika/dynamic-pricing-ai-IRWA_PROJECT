# core/agents/data_collector/repo.py
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import asyncio
import aiosqlite

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class DataRepo:
    def __init__(self, db_path: Optional[str] = None, *, connect_timeout: float = 30.0) -> None:
        self.db_path = db_path or os.getenv("DATA_DB", os.path.join("app", "data.db"))
        self.connect_timeout = float(connect_timeout)
        self._init_lock = asyncio.Lock()

    async def _column_exists(self, db: aiosqlite.Connection, table: str, column: str) -> bool:
        cur = await db.execute(f"PRAGMA table_info({table})")
        cols = await cur.fetchall()
        return any(r[1] == column for r in cols)

    async def _ensure_ingested_at(self, db: aiosqlite.Connection) -> None:
        """
        Ensure market_ticks.ingested_at exists.
        For existing DBs, add the column WITHOUT a default and backfill from ts (or now()).
        """
        exists = await self._column_exists(db, "market_ticks", "ingested_at")
        if not exists:
            # 1) add column w/o default (SQLite allows this)
            await db.execute("ALTER TABLE market_ticks ADD COLUMN ingested_at TEXT")
            # 2) backfill: prefer ts, else now
            await db.execute(
                "UPDATE market_ticks SET ingested_at = COALESCE(ts, datetime('now')) WHERE ingested_at IS NULL"
            )

    def _db_dir_make(self) -> None:
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    async def init(self) -> None:
        async with self._init_lock:
            self._db_dir_make()
            async with aiosqlite.connect(self.db_path, timeout=self.connect_timeout) as db:
                await db.execute("PRAGMA journal_mode=WAL;")
                await db.execute("PRAGMA synchronous=NORMAL;")
                await db.execute("PRAGMA busy_timeout=10000;")
                await db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS products(
                      id INTEGER PRIMARY KEY,
                      sku TEXT NOT NULL,
                      market TEXT NOT NULL,
                      name TEXT,
                      cost REAL,
                      base_price REAL,
                      currency TEXT,
                      updated_at TEXT NOT NULL,
                      UNIQUE(sku, market)
                    );

                    CREATE TABLE IF NOT EXISTS market_ticks(
                      id INTEGER PRIMARY KEY,
                      sku TEXT NOT NULL,
                      market TEXT NOT NULL,
                      our_price REAL NOT NULL,
                      competitor_price REAL,
                      demand_index REAL,
                      source TEXT NOT NULL,
                      ts TEXT NOT NULL,
                      ingested_at TEXT  -- note: created without default to avoid ALTER default issue
                    );
                    CREATE INDEX IF NOT EXISTS idx_ticks_sku_ts ON market_ticks(sku, ts);

                    CREATE TABLE IF NOT EXISTS jobs(
                      id TEXT PRIMARY KEY,
                      sku TEXT NOT NULL,
                      market TEXT NOT NULL,
                      connector TEXT NOT NULL,
                      depth INTEGER NOT NULL,
                      status TEXT NOT NULL,
                      error TEXT,
                      created_at TEXT NOT NULL,
                      started_at TEXT,
                      finished_at TEXT
                    );
                    """
                )
                # If DB was created earlier without ingested_at, add + backfill now:
                await self._ensure_ingested_at(db)
                await db.commit()

    # --- everywhere you open a connection, keep the same timeout ---
    async def upsert_products(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(products, list):
            raise TypeError("products must be a list of dicts")

        now_iso = _utcnow_iso()
        rows = []
        for p in products:
            sku = p.get("sku")
            if not sku:
                continue
            market = p.get("market") or "DEFAULT"
            rows.append(
                (str(sku), str(market), p.get("name"), p.get("cost"),
                 p.get("base_price"), p.get("currency"), p.get("updated_at") or now_iso)
            )

        if not rows:
            return {"ok": True, "count": 0}

        async with aiosqlite.connect(self.db_path, timeout=self.connect_timeout) as db:
            await db.executemany(
                """
                INSERT INTO products (sku, market, name, cost, base_price, currency, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sku, market) DO UPDATE SET
                  name       = excluded.name,
                  cost       = excluded.cost,
                  base_price = excluded.base_price,
                  currency   = excluded.currency,
                  updated_at = excluded.updated_at
                """,
                rows,
            )
            await db.commit()
        return {"ok": True, "count": len(rows)}

    async def list_products(self, market: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT sku, market, name, cost, base_price, currency, updated_at FROM products"
        params: tuple[Any, ...] = ()
        if market:
            query += " WHERE market = ?"
            params = (market,)

        async with aiosqlite.connect(self.db_path, timeout=self.connect_timeout) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(query, params)
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def insert_tick(
        self,
        *,
        sku: str,
        our_price: float,
        source: str = "mock",
        market: str = "DEFAULT",
        competitor_price: Optional[float] = None,
        demand_index: Optional[float] = None,
        ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        when = ts or _utcnow_iso()
        ingested = when
        async with aiosqlite.connect(self.db_path, timeout=self.connect_timeout) as db:
            await db.execute(
                """
                INSERT INTO market_ticks
                  (sku, market, our_price, competitor_price, demand_index, source, ts, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (sku, market, our_price, competitor_price, demand_index, source, when, ingested),
            )
            await db.commit()

        return {
            "sku": sku, "market": market, "our_price": our_price,
            "competitor_price": competitor_price, "demand_index": demand_index,
            "source": source, "ts": when, "ingested_at": ingested,
        }

    async def insert_tick_dict(self, tick: Dict[str, Any]) -> Dict[str, Any]:
        return await self.insert_tick(
            sku=str(
                tick.get("sku") or tick.get("symbol") or
                tick.get("sym") or tick.get("product_id") or tick.get("ticker")
            ),
            our_price=float(tick.get("our_price") or tick.get("price") or tick.get("px") or tick.get("unit_price")),
            source=str(tick.get("source") or tick.get("src") or "mock"),
            market=str(tick.get("market") or "DEFAULT"),
            competitor_price=tick.get("competitor_price"),
            demand_index=tick.get("demand_index"),
            ts=tick.get("ts"),
        )

    async def latest(self, sku: str, limit: int = 50) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path, timeout=self.connect_timeout) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT sku, market, our_price, competitor_price, demand_index, source, ts, ingested_at
                FROM market_ticks
                WHERE sku = ?
                ORDER BY ts DESC
                LIMIT ?
                """,
                (sku, limit),
            )
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def features_for(self, sku: str, market: str, since_iso: str) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path, timeout=self.connect_timeout) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM market_ticks
                WHERE sku = ? AND market = ? AND ts >= ?
                """,
                (sku, market, since_iso),
            )
            row = await cur.fetchone()
            count = int(row["cnt"]) if row else 0

            cur2 = await db.execute(
                """
                SELECT our_price
                FROM market_ticks
                WHERE sku = ? AND market = ?
                ORDER BY ts DESC
                LIMIT 1
                """,
                (sku, market),
            )
            row2 = await cur2.fetchone()
            last_price = float(row2["our_price"]) if row2 else None

        return {
            "snapshot_id": None,
            "as_of": _utcnow_iso(),
            "features": {"last_price": last_price},
            "provenance": [],
            "count": count,
        }

    # jobs … (unchanged)
