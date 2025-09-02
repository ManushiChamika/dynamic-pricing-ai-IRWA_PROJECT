from __future__ import annotations
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio

# ---------- small helpers ----------
def cheapest_product(db_path: str, days: int = 7) -> Dict[str, Any]:
    conn = _open(db_path)
    try:
        q = """
        SELECT t.sku, MIN(t.our_price) AS price, COALESCE(p.name, t.sku) AS label
        FROM market_ticks t
        LEFT JOIN products p ON p.sku = t.sku
        WHERE datetime(t.ts) >= datetime('now', ?)
        GROUP BY t.sku
        ORDER BY price ASC
        LIMIT 1
        """
        row = conn.execute(q, (f"-{days} days",)).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()

def most_expensive_product(db_path: str, days: int = 7) -> Dict[str, Any]:
    conn = _open(db_path)
    try:
        q = """
        SELECT t.sku, MAX(t.our_price) AS price, COALESCE(p.name, t.sku) AS label
        FROM market_ticks t
        LEFT JOIN products p ON p.sku = t.sku
        WHERE datetime(t.ts) >= datetime('now', ?)
        GROUP BY t.sku
        ORDER BY price DESC
        LIMIT 1
        """
        row = conn.execute(q, (f"-{days} days",)).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()

def _to_thread(fn, *a, **k):
    return asyncio.to_thread(fn, *a, **k)

def _open(db_path: str):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def _window_bounds(days: int):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    return start, end

def _as_list(cur) -> List[Dict[str, Any]]:
    return [dict(r) for r in cur.fetchall()]

def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


def _columns(conn, table: str) -> set[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {r[1] for r in cur.fetchall()}

def _has_column(conn, table: str, col: str) -> bool:
    return col in _columns(conn, table)

def _pick_price_column(conn, table: str) -> str:
    cols = _columns(conn, table)
    if "our_price" in cols:
        return "our_price"
    if "price" in cols:
        return "price"
    return next(iter(cols))  # fallback

def _pick_sku_column(conn, table: str) -> str:
    cols = _columns(conn, table)
    for c in ("sku", "product_name", "symbol"):
        if c in cols:
            return c
    return next(iter(cols))

def _pick_time_column(conn, table: str) -> Optional[str]:
    cols = _columns(conn, table)
    if "ts" in cols:
        return "ts"
    if "update_time" in cols:
        return "update_time"
    return None

# ---------- product resolution ----------

async def resolve_products(db_path: str, hint: str, limit: int = 5):
    def run():
        conn = _open(db_path)
        try:
            has_market = _has_column(conn, "products", "market")
            if has_market:
                q = """
                SELECT sku, market, COALESCE(name, sku) AS label
                FROM products
                WHERE lower(sku) = lower(?)
                   OR lower(name) LIKE lower(?)
                ORDER BY (lower(sku) = lower(?)) DESC, label ASC
                LIMIT ?
                """
                cur = conn.execute(q, (hint, f"%{hint}%", hint, limit))
            else:
                q = """
                SELECT sku, COALESCE(name, sku) AS label
                FROM products
                WHERE lower(sku) = lower(?)
                   OR lower(name) LIKE lower(?)
                ORDER BY (lower(sku) = lower(?)) DESC, label ASC
                LIMIT ?
                """
                cur = conn.execute(q, (hint, f"%{hint}%", hint, limit))
            return _as_list(cur)
        finally:
            conn.close()
    return await _to_thread(run)

# ---------- latest price ----------

async def latest_price_for(db_path: str, sku: str, market: str = "DEFAULT"):
    def run():
        conn = _open(db_path)
        try:
            has_market = _has_column(conn, "products", "market")
            join_cond = "p.sku = t.sku AND p.market = t.market" if has_market else "p.sku = t.sku"
            where_cond = "t.sku = ? AND t.market = ?" if has_market else "t.sku = ?"

            q = f"""
            SELECT t.sku, t.market, t.our_price, t.competitor_price, t.ts,
                   COALESCE(p.name, t.sku) AS label
            FROM market_ticks t
            LEFT JOIN products p ON {join_cond}
            WHERE {where_cond}
            ORDER BY datetime(t.ts) DESC
            LIMIT 1
            """
            args = (sku, market) if has_market else (sku,)
            row = conn.execute(q, args).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    return await _to_thread(run)

# ---------- stats for a period ----------

async def stats_for_period(db_path: str, sku: str, days: int = 7, market: str = "DEFAULT"):
    def run():
        conn = _open(db_path)
        try:
            start, _ = _window_bounds(days)
            has_market = _has_column(conn, "products", "market")

            if has_market:
                q = """
                WITH w AS (
                  SELECT our_price AS price, competitor_price AS comp, ts
                  FROM market_ticks
                  WHERE sku = ? AND market = ? AND datetime(ts) >= datetime(?)
                )
                SELECT
                  (SELECT COALESCE(name, ?) FROM products WHERE sku = ? AND market = ? LIMIT 1) AS label,
                  (SELECT price FROM w ORDER BY datetime(ts) ASC LIMIT 1) AS first_price,
                  (SELECT price FROM w ORDER BY datetime(ts) DESC LIMIT 1) AS last_price,
                  (SELECT MIN(price) FROM w) AS min_price,
                  (SELECT MAX(price) FROM w) AS max_price,
                  (SELECT AVG(price) FROM w) AS avg_price,
                  (SELECT COUNT(*) FROM w) AS updates,
                  (SELECT AVG(comp) FROM w WHERE comp IS NOT NULL) AS avg_comp
                """
                args = (sku, market, start.isoformat(), sku, sku, market)
            else:
                q = """
                WITH w AS (
                  SELECT our_price AS price, competitor_price AS comp, ts
                  FROM market_ticks
                  WHERE sku = ? AND datetime(ts) >= datetime(?)
                )
                SELECT
                  (SELECT COALESCE(name, ?) FROM products WHERE sku = ? LIMIT 1) AS label,
                  (SELECT price FROM w ORDER BY datetime(ts) ASC LIMIT 1) AS first_price,
                  (SELECT price FROM w ORDER BY datetime(ts) DESC LIMIT 1) AS last_price,
                  (SELECT MIN(price) FROM w) AS min_price,
                  (SELECT MAX(price) FROM w) AS max_price,
                  (SELECT AVG(price) FROM w) AS avg_price,
                  (SELECT COUNT(*) FROM w) AS updates,
                  (SELECT AVG(comp) FROM w WHERE comp IS NOT NULL) AS avg_comp
                """
                args = (sku, start.isoformat(), sku, sku)

            row = conn.execute(q, args).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    return await _to_thread(run)

# ---------- trending by volume ----------

async def top_trending_by_volume(db_path: str, days: int = 7, market: Optional[str] = None,
                                 limit: int = 5, ascending: bool = False):
    def run():
        conn = _open(db_path)
        try:
            table = "market_ticks" if _table_exists(conn, "market_ticks") else "market_data"
            sku_col = _pick_sku_column(conn, table)
            tcol = _pick_time_column(conn, table)

            has_market = _has_column(conn, "products", "market")
            where = []
            args: list[Any] = []

            if tcol:
                start, _ = _window_bounds(days)
                where.append(f"datetime({tcol}) >= datetime(?)")
                args.append(start.isoformat())
            if has_market and market:
                where.append("market = ?")
                args.append(market)

            where_sql = "WHERE " + " AND ".join(where) if where else ""

            if has_market:
                q = f"""
                SELECT t.{sku_col} AS sku,
                       COALESCE(p.name, t.{sku_col}) AS label,
                       COUNT(*) AS n
                FROM {table} t
                LEFT JOIN products p ON p.sku = t.{sku_col} AND p.market = t.market
                {where_sql}
                GROUP BY t.{sku_col}, label
                ORDER BY n {"ASC" if ascending else "DESC"}
                LIMIT ?
                """
            else:
                q = f"""
                SELECT t.{sku_col} AS sku,
                       COALESCE(p.name, t.{sku_col}) AS label,
                       COUNT(*) AS n
                FROM {table} t
                LEFT JOIN products p ON p.sku = t.{sku_col}
                {where_sql}
                GROUP BY t.{sku_col}, label
                ORDER BY n {"ASC" if ascending else "DESC"}
                LIMIT ?
                """

            args.append(limit)
            cur = conn.execute(q, args)
            return _as_list(cur)
        finally:
            conn.close()
    return await _to_thread(run)

# ---------- top price movers ----------

async def top_price_movers(db_path: str, days: int = 7, market: Optional[str] = None, limit: int = 5):
    def run():
        conn = _open(db_path)
        try:
            table = "market_ticks" if _table_exists(conn, "market_ticks") else "market_data"
            sku_col = _pick_sku_column(conn, table)
            tcol = _pick_time_column(conn, table)
            pcol = _pick_price_column(conn, table)

            has_market = _has_column(conn, "products", "market")
            where = []
            args: list[Any] = []

            if tcol:
                start, _ = _window_bounds(days)
                where.append(f"datetime({tcol}) >= datetime(?)")
                args.append(start.isoformat())
            if has_market and market:
                where.append("market = ?")
                args.append(market)

            where_sql = "WHERE " + " AND ".join(where) if where else ""

            if has_market:
                q = f"""
                WITH w AS (
                    SELECT {sku_col} AS sku, market, {pcol} AS price, {tcol or "'1970-01-01'"} AS ts
                    FROM {table}
                    {where_sql}
                ),
                firsts AS (
                    SELECT sku, market, price AS first_price
                    FROM (
                        SELECT sku, market, price, ts,
                               ROW_NUMBER() OVER (PARTITION BY sku, market ORDER BY ts ASC) rn
                        FROM w
                    ) WHERE rn = 1
                ),
                lasts AS (
                    SELECT sku, market, price AS last_price
                    FROM (
                        SELECT sku, market, price, ts,
                               ROW_NUMBER() OVER (PARTITION BY sku, market ORDER BY ts DESC) rn
                        FROM w
                    ) WHERE rn = 1
                )
                SELECT f.sku,
                       COALESCE(p.name, f.sku) AS label,
                       f.first_price,
                       l.last_price,
                       CASE WHEN f.first_price>0
                            THEN (l.last_price - f.first_price)/f.first_price
                            ELSE 0 END AS pct_change
                FROM firsts f
                JOIN lasts l ON l.sku = f.sku AND l.market = f.market
                LEFT JOIN products p ON p.sku = f.sku AND p.market = f.market
                ORDER BY ABS(pct_change) DESC
                LIMIT ?
                """
            else:
                q = f"""
                WITH w AS (
                    SELECT {sku_col} AS sku, {pcol} AS price, {tcol or "'1970-01-01'"} AS ts
                    FROM {table}
                    {where_sql}
                ),
                firsts AS (
                    SELECT sku, price AS first_price
                    FROM (
                        SELECT sku, price, ts,
                               ROW_NUMBER() OVER (PARTITION BY sku ORDER BY ts ASC) rn
                        FROM w
                    ) WHERE rn = 1
                ),
                lasts AS (
                    SELECT sku, price AS last_price
                    FROM (
                        SELECT sku, price, ts,
                               ROW_NUMBER() OVER (PARTITION BY sku ORDER BY ts DESC) rn
                        FROM w
                    ) WHERE rn = 1
                )
                SELECT f.sku,
                       COALESCE(p.name, f.sku) AS label,
                       f.first_price,
                       l.last_price,
                       CASE WHEN f.first_price>0
                            THEN (l.last_price - f.first_price)/f.first_price
                            ELSE 0 END AS pct_change
                FROM firsts f
                JOIN lasts l ON l.sku = f.sku
                LEFT JOIN products p ON p.sku = f.sku
                ORDER BY ABS(pct_change) DESC
                LIMIT ?
                """

            args.append(limit)
            cur = conn.execute(q, args)
            return _as_list(cur)
        finally:
            conn.close()
    return await _to_thread(run)

# ---------- competitor pressure ----------

async def highest_competitor_pressure(db_path: str, days: int = 7, market: Optional[str] = None, limit: int = 5):
    def run():
        conn = _open(db_path)
        try:
            table = "market_ticks" if _table_exists(conn, "market_ticks") else "market_data"
            sku_col = _pick_sku_column(conn, table)
            tcol = _pick_time_column(conn, table)

            cols = _columns(conn, table)
            comp_col = "competitor_price" if "competitor_price" in cols else None
            our_col = "our_price" if "our_price" in cols else _pick_price_column(conn, table)
            if not comp_col:
                return []

            has_market = _has_column(conn, "products", "market")
            where = []
            args: list[Any] = []

            if tcol:
                start, _ = _window_bounds(days)
                where.append(f"datetime({tcol}) >= datetime(?)")
                args.append(start.isoformat())
            if has_market and market:
                where.append("market = ?")
                args.append(market)

            where_sql = "WHERE " + " AND ".join(where) if where else ""

            if has_market:
                q = f"""
                WITH w AS (
                  SELECT {sku_col} AS sku, market, {our_col} AS our_price, {comp_col} AS comp_price
                  FROM {table}
                  {where_sql}
                  AND {comp_col} IS NOT NULL
                )
                SELECT w.sku,
                       COALESCE(p.name, w.sku) AS label,
                       AVG(w.our_price) AS avg_ours,
                       AVG(w.comp_price) AS avg_comp,
                       (AVG(w.comp_price) - AVG(w.our_price)) AS comp_delta
                FROM w
                LEFT JOIN products p ON p.sku = w.sku AND p.market = w.market
                GROUP BY w.sku, label
                ORDER BY comp_delta ASC
                LIMIT ?
                """
            else:
                q = f"""
                WITH w AS (
                  SELECT {sku_col} AS sku, {our_col} AS our_price, {comp_col} AS comp_price
                  FROM {table}
                  {where_sql}
                  AND {comp_col} IS NOT NULL
                )
                SELECT w.sku,
                       COALESCE(p.name, w.sku) AS label,
                       AVG(w.our_price) AS avg_ours,
                       AVG(w.comp_price) AS avg_comp,
                       (AVG(w.comp_price) - AVG(w.our_price)) AS comp_delta
                FROM w
                LEFT JOIN products p ON p.sku = w.sku
                GROUP BY w.sku, label
                ORDER BY comp_delta ASC
                LIMIT ?
                """

            args.append(limit)
            cur = conn.execute(q, args)
            return _as_list(cur)
        finally:
            conn.close()
    return await _to_thread(run)
