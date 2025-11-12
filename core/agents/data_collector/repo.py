from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

import aiosqlite
import uuid
import sqlite3


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DataRepo:
    """
    Minimal repo for market ticks. Uses SQLite at DATA_DB or app/data.db.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        root = Path(__file__).resolve().parents[3]
        settings_path = None
        try:
            from core.settings import get_settings
            settings_path = getattr(get_settings(), "data_db", None)
        except Exception:
            settings_path = None
        env_path = os.getenv("DATA_DB")
        base = path or settings_path or env_path
        candidate = Path(base) if base else (root / "app" / "data.db")
        if not candidate.is_absolute():
            candidate = root / candidate
        self.path = candidate

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

                -- Additive tables for product catalog, jobs, and proposals
                CREATE TABLE IF NOT EXISTS product_catalog (
                   sku TEXT,
                   owner_id TEXT NOT NULL,
                   title TEXT,
                   currency TEXT,
                   current_price REAL,
                   cost REAL,
                   stock INTEGER,
                   updated_at TEXT,
                   source_url TEXT,
                   PRIMARY KEY (sku, owner_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_product_catalog_owner_id 
                   ON product_catalog(owner_id);

                CREATE TABLE IF NOT EXISTS ingestion_jobs (
                  id TEXT PRIMARY KEY,
                  sku TEXT,
                  market TEXT,
                  connector TEXT,
                  depth INTEGER,
                  status TEXT,
                  error TEXT,
                  created_at TEXT,
                  started_at TEXT,
                  finished_at TEXT
                );

                CREATE TABLE IF NOT EXISTS price_proposals (
                  id TEXT PRIMARY KEY,
                  sku TEXT,
                  proposed_price REAL,
                  current_price REAL,
                  margin REAL,
                  algorithm TEXT,
                  ts TEXT
                );
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


    async def upsert_products(self, rows: List[Dict[str, Any]], owner_id: str) -> int:
        """Upsert a list of product rows into product_catalog.

        Uses INSERT ... ON CONFLICT(sku, owner_id) DO UPDATE for efficiency; if not
        supported, falls back to INSERT/UPDATE per-row. Returns number of
        processed rows.
        """
        if not rows:
            return 0

        params = []
        for r in rows:
            sku = str(r["sku"]).strip()
            if not sku:
                continue
            title = r.get("title")
            currency = r.get("currency")
            current_price = r.get("current_price")
            cost = r.get("cost")
            stock = r.get("stock")
            updated_at = r.get("updated_at") or _utc_now_iso()
            params.append(
                (sku, owner_id, title, currency, current_price, cost, stock, updated_at)
            )

        if not params:
            return 0

        insert_sql = (
            """
            INSERT INTO product_catalog
              (sku, owner_id, title, currency, current_price, cost, stock, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(sku, owner_id) DO UPDATE SET
              title=excluded.title,
              currency=excluded.currency,
              current_price=excluded.current_price,
              cost=excluded.cost,
              stock=excluded.stock,
              updated_at=excluded.updated_at
            """
        )

        async with aiosqlite.connect(self.path.as_posix()) as db:
            try:
                await db.executemany(insert_sql, params)
                await db.commit()
                return len(params)
            except Exception:
                processed = 0
                for p in params:
                    try:
                        await db.execute(
                            """
                            INSERT INTO product_catalog
                              (sku, owner_id, title, currency, current_price, cost, stock,
                               updated_at)
                            VALUES (?,?,?,?,?,?,?,?)
                            """,
                            p,
                        )
                        processed += 1
                    except sqlite3.IntegrityError:
                        sku = p[0]
                        owner_id_val = p[1]
                        title, currency, current_price, cost, stock, updated_at = (
                            p[2], p[3], p[4], p[5], p[6], p[7]
                        )
                        await db.execute(
                            """
                            UPDATE product_catalog
                            SET title=?, currency=?, current_price=?, cost=?,
                                stock=?, updated_at=?
                            WHERE sku=? AND owner_id=?
                            """,
                            (
                                title,
                                currency,
                                current_price,
                                cost,
                                stock,
                                updated_at,
                                sku,
                                owner_id_val,
                            ),
                        )
                        processed += 1
                await db.commit()
                return processed

    async def get_products_by_owner(self, owner_id: str) -> List[Dict[str, Any]]:
        """Retrieve all products for a specific owner."""
        async with aiosqlite.connect(self.path.as_posix()) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT sku, owner_id, title, currency, current_price, cost, stock, updated_at
                FROM product_catalog
                WHERE owner_id=?
                ORDER BY updated_at DESC
                """,
                (owner_id,),
            )
            rows = await cur.fetchall()
        return [dict(row) for row in rows]

    async def get_product_by_sku_and_owner(self, sku: str, owner_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific product by SKU and owner_id."""
        async with aiosqlite.connect(self.path.as_posix()) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT sku, owner_id, title, currency, current_price, cost, stock, updated_at
                FROM product_catalog
                WHERE sku=? AND owner_id=?
                """,
                (sku, owner_id),
            )
            row = await cur.fetchone()
        return dict(row) if row else None

    async def delete_product_by_owner(self, sku: str, owner_id: str) -> int:
        """Delete a product for a specific owner. Returns rows affected."""
        async with aiosqlite.connect(self.path.as_posix()) as db:
            cursor = await db.execute(
                """
                DELETE FROM product_catalog
                WHERE sku=? AND owner_id=?
                """,
                (sku, owner_id),
            )
            await db.commit()
        return cursor.rowcount

    async def delete_all_products_by_owner(self, owner_id: str) -> int:
        """Delete all products for a specific owner. Returns rows affected."""
        async with aiosqlite.connect(self.path.as_posix()) as db:
            cursor = await db.execute(
                """
                DELETE FROM product_catalog
                WHERE owner_id=?
                """,
                (owner_id,),
            )
            await db.commit()
        return cursor.rowcount

    async def create_job(
        self, sku: str, market: str, connector: str, depth: int
    ) -> str:
        """Create an ingestion job and return its job id (uuid4)."""
        job_id = str(uuid.uuid4())
        now = _utc_now_iso()
        async with aiosqlite.connect(self.path.as_posix()) as db:
            await db.execute(
                """
                INSERT INTO ingestion_jobs
                  (id, sku, market, connector, depth, status, error,
                   created_at, started_at, finished_at)
                VALUES (?,?,?,?,?,?,?, ?, ?, ?)
                """,
                (
                    job_id,
                    sku,
                    market,
                    connector,
                    int(depth),
                    "QUEUED",
                    None,
                    now,
                    None,
                    None,
                ),
            )
            await db.commit()
        return job_id

    async def mark_job_running(self, job_id: str) -> None:
        """Mark an ingestion job as RUNNING and set started_at timestamp."""
        async with aiosqlite.connect(self.path.as_posix()) as db:
            await db.execute(
                """
                UPDATE ingestion_jobs
                SET status=?, started_at=?
                WHERE id=?
                """,
                ("RUNNING", _utc_now_iso(), job_id),
            )
            await db.commit()

    async def mark_job_done(self, job_id: str) -> None:
        """Mark an ingestion job as DONE and set finished_at timestamp."""
        async with aiosqlite.connect(self.path.as_posix()) as db:
            await db.execute(
                """
                UPDATE ingestion_jobs
                SET status=?, finished_at=?
                WHERE id=?
                """,
                ("DONE", _utc_now_iso(), job_id),
            )
            await db.commit()

    async def mark_job_failed(self, job_id: str, error: str) -> None:
        """Mark an ingestion job as FAILED with an error message."""
        async with aiosqlite.connect(self.path.as_posix()) as db:
            await db.execute(
                """
                UPDATE ingestion_jobs
                SET status=?, error=?, finished_at=?
                WHERE id=?
                """,
                ("FAILED", str(error), _utc_now_iso(), job_id),
            )
            await db.commit()

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Return a job row as a dict, or None if not found."""
        async with aiosqlite.connect(self.path.as_posix()) as db:
            cur = await db.execute(
                """
                SELECT id, sku, market, connector, depth, status, error,
                       created_at, started_at, finished_at
                FROM ingestion_jobs
                WHERE id=?
                """,
                (job_id,),
            )
            row = await cur.fetchone()
        if not row:
            return None
        keys = [
            "id",
            "sku",
            "market",
            "connector",
            "depth",
            "status",
            "error",
            "created_at",
            "started_at",
            "finished_at",
        ]
        return {k: row[i] for i, k in enumerate(keys)}

    async def insert_price_proposal(self, pp: Dict[str, Any]) -> None:
        """Insert a price proposal row.

        If 'id' or 'ts' are missing, they will be generated.
        """
        pid = pp.get("id") or str(uuid.uuid4())
        ts = pp.get("ts") or _utc_now_iso()
        async with aiosqlite.connect(self.path.as_posix()) as db:
            await db.execute(
                """
                INSERT INTO price_proposals
                  (id, sku, proposed_price, current_price, margin, algorithm, ts)
                VALUES (?,?,?,?,?,?,?)
                """,
                (
                    pid,
                    pp["sku"],
                    pp["proposed_price"],
                    pp["current_price"],
                    pp["margin"],
                    pp["algorithm"],
                    ts,
                ),
            )
            await db.commit()
