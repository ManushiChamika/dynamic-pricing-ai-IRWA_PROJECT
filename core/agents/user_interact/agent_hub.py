from __future__ import annotations

import asyncio
import json
import random
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from core.agents.price_optimizer.agent import PricingOptimizerAgent

try:
    from core.agents.data_collector.connectors.web_scraper import fetch_competitor_price  # type: ignore
except Exception:
    fetch_competitor_price = None  # type: ignore


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _round_price(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), 2)


@dataclass(slots=True)
class ProductRecord:
    sku: str
    title: str
    currency: str
    current_price: Optional[float]
    cost: Optional[float]
    stock: Optional[int]


class AgentHub:
    """Coordinated façade that lets the Interaction Agent drive the end-to-end pipeline.

    The hub exposes synchronous helper methods so function-call tools can:
    - register products (Interaction + Supervisor)
    - collect competitor prices (Data Collection Agent)
    - run price optimizations (Pricing Optimizer Agent)
    - evaluate alert rules (Alert Agent)
    - assemble enriched status snapshots for chat responses
    """

    def __init__(self, owner_id: str = "1") -> None:
        self.root = Path(__file__).resolve().parents[3]
        self.owner_id = owner_id
        self.app_db = self.root / "app" / "data.db"
        self.app_db.parent.mkdir(parents=True, exist_ok=True)
        self._schema_ready = False
        self._ensure_schema()

    # ------------------------------------------------------------------ #
    # Schema helpers
    # ------------------------------------------------------------------ #
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.app_db.as_posix(), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        ddl = """
        PRAGMA journal_mode=WAL;

        CREATE TABLE IF NOT EXISTS product_catalog (
            sku TEXT NOT NULL,
            owner_id TEXT NOT NULL DEFAULT '1',
            title TEXT,
            currency TEXT,
            current_price REAL,
            cost REAL,
            stock INTEGER,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (sku, owner_id)
        );

        CREATE TABLE IF NOT EXISTS product_competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            source_url TEXT NOT NULL,
            market TEXT DEFAULT 'DEFAULT',
            label TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS market_ticks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            market TEXT NOT NULL,
            our_price REAL,
            competitor_price REAL,
            demand_index REAL,
            ts TEXT DEFAULT (datetime('now')),
            source TEXT
        );

        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            features TEXT,
            scraped_at TEXT DEFAULT (datetime('now')),
            source TEXT
        );

        CREATE TABLE IF NOT EXISTS pricing_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            optimized_price REAL NOT NULL,
            last_update TEXT DEFAULT (datetime('now')),
            reason TEXT
        );

        CREATE TABLE IF NOT EXISTS price_proposals (
            id TEXT PRIMARY KEY,
            sku TEXT NOT NULL,
            proposed_price REAL NOT NULL,
            current_price REAL,
            margin REAL,
            algorithm TEXT,
            ts TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS agent_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            kind TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """
        with self._connect() as conn:
            conn.executescript(ddl)
            conn.commit()
        self._schema_ready = True

    # ------------------------------------------------------------------ #
    # Public API used by tools
    # ------------------------------------------------------------------ #
    def register_product(
        self,
        *,
        title: str,
        cost: Optional[float],
        sku: Optional[str] = None,
        currency: str = "USD",
        list_price: Optional[float] = None,
        stock: Optional[int] = None,
        competitor_urls: Optional[Sequence[str]] = None,
        market: str = "DEFAULT",
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._ensure_schema()
        clean_title = (title or "").strip()
        if not clean_title and not sku:
            return {"status": "error", "message": "Title or SKU is required"}

        final_sku = self._normalize_sku(sku or clean_title)
        final_currency = (currency or "USD").upper()
        now = _utc_now()
        baseline = None
        if cost is not None:
            baseline = float(cost)
        computed_price = list_price
        if computed_price is None:
            if baseline is not None:
                computed_price = max(baseline * 1.15, baseline + 1.0)
            else:
                computed_price = 10.0
        computed_price = _round_price(computed_price)

        competitor_list = self._coerce_urls(competitor_urls)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO product_catalog
                  (sku, owner_id, title, currency, current_price, cost, stock, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sku, owner_id) DO UPDATE SET
                  title=excluded.title,
                  currency=excluded.currency,
                  current_price=excluded.current_price,
                  cost=excluded.cost,
                  stock=excluded.stock,
                  notes=excluded.notes,
                  updated_at=excluded.updated_at
                """,
                (
                    final_sku,
                    self.owner_id,
                    clean_title or final_sku,
                    final_currency,
                    computed_price,
                    baseline,
                    stock,
                    notes,
                    now,
                    now,
                ),
            )
            conn.execute("DELETE FROM product_competitors WHERE sku=?", (final_sku,))
            for url in competitor_list:
                conn.execute(
                    """
                    INSERT INTO product_competitors (sku, source_url, market)
                    VALUES (?, ?, ?)
                    """,
                    (final_sku, url, market),
                )
            conn.commit()

        return {
            "status": "ok",
            "agent": "SupervisorAgent",
            "sku": final_sku,
            "title": clean_title or final_sku,
            "currency": final_currency,
            "current_price": computed_price,
            "cost": baseline,
            "stock": stock,
            "competitor_urls": competitor_list,
            "notes": notes,
            "market": market,
            "timestamp": now,
        }

    def collect_market_data(
        self,
        *,
        sku: str,
        competitor_urls: Optional[Sequence[str]] = None,
        market: str = "DEFAULT",
        depth: int = 3,
        inject_baseline: Optional[float] = None,
    ) -> Dict[str, Any]:
        self._ensure_schema()
        record = self._get_product(sku)
        if record is None:
            return {"status": "error", "message": f"Unknown SKU '{sku}'"}

        urls = list(self._coerce_urls(competitor_urls))
        if not urls:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT source_url FROM product_competitors WHERE sku=?",
                    (sku,),
                ).fetchall()
                urls = [r["source_url"] for r in rows]

        if not urls:
            urls = [f"mock://competitor-{i+1}" for i in range(max(1, depth))]

        observed: List[Dict[str, Any]] = []
        our_price = record.current_price or inject_baseline or record.cost or 0.0
        for idx, url in enumerate(urls):
            measurement = self._fetch_competitor_quote(
                url=url,
                fallback_anchor=our_price or max(record.cost or 0.0, 1.0),
                variation=0.08 + (idx * 0.02),
            )
            observed.append(measurement)

        with self._connect() as conn:
            title = record.title or record.sku
            for entry in observed:
                features = {
                    "sku": record.sku,
                    "source": entry["source"],
                    "confidence": entry["confidence"],
                    "note": entry.get("note"),
                }
                conn.execute(
                    """
                    INSERT INTO market_data (product_name, price, features, scraped_at, source)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        title,
                        entry["price"],
                        json.dumps(features),
                        entry["timestamp"],
                        entry["source"],
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO market_ticks (sku, market, our_price, competitor_price, demand_index, ts, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.sku,
                        market,
                        our_price,
                        entry["price"],
                        entry["demand_index"],
                        entry["timestamp"],
                        entry["source"],
                    ),
                )
            conn.commit()

        prices = [item["price"] for item in observed if item.get("price") is not None]
        summary = {
            "count": len(prices),
            "min": _round_price(min(prices)) if prices else None,
            "max": _round_price(max(prices)) if prices else None,
            "avg": _round_price(sum(prices) / len(prices)) if prices else None,
        }

        return {
            "status": "ok",
            "agent": "DataCollectionAgent",
            "sku": record.sku,
            "product_title": record.title,
            "market": market,
            "observations": observed,
            "summary": summary,
        }

    def optimize_price(
        self,
        *,
        sku: str,
        user_request: Optional[str] = None,
        refresh_market: bool = False,
        competitor_urls: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        self._ensure_schema()
        record = self._get_product(sku)
        if record is None:
            return {"status": "error", "message": f"Unknown SKU '{sku}'"}

        if refresh_market:
            self.collect_market_data(
                sku=sku,
                competitor_urls=competitor_urls,
                inject_baseline=record.current_price or record.cost or 0.0,
            )

        request = user_request or "Recommend the optimal selling price."
        agent = PricingOptimizerAgent()
        result = asyncio.run(
            agent.process_full_workflow(
                user_request=request,
                product_name=record.sku,
            )
        )

        recommended = _round_price(result.get("recommended_price"))
        now = _utc_now()
        with self._connect() as conn:
            if recommended is not None:
                reason = result.get("reason") or "Automated pricing recommendation"
                conn.execute(
                    """
                    INSERT INTO pricing_list (product_name, optimized_price, last_update, reason)
                    VALUES (?, ?, ?, ?)
                    """,
                    (record.title or record.sku, recommended, now, reason),
                )

                margin = None
                if record.cost and recommended:
                    if recommended > 0:
                        margin = (recommended - record.cost) / recommended

                conn.execute(
                    """
                    INSERT OR REPLACE INTO price_proposals
                      (id, sku, proposed_price, current_price, margin, algorithm, ts)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        uuid.uuid4().hex,
                        record.sku,
                        recommended,
                        record.current_price,
                        margin,
                        result.get("algorithm"),
                        now,
                    ),
                )
            conn.commit()

        result["status"] = result.get("status", "ok")
        result["agent"] = "PricingOptimizerAgent"
        result["timestamp"] = now
        return result

    def evaluate_alerts(self, *, sku: str) -> Dict[str, Any]:
        self._ensure_schema()
        record = self._get_product(sku)
        if record is None:
            return {"status": "error", "message": f"Unknown SKU '{sku}'"}

        alerts: List[Dict[str, Any]] = []
        now = _utc_now()
        with self._connect() as conn:
            title = record.title or record.sku
            stats = conn.execute(
                """
                SELECT AVG(price) AS avg_price,
                       MIN(price) AS min_price,
                       MAX(price) AS max_price
                FROM market_data
                WHERE product_name=?
                """,
                (title,),
            ).fetchone()

            margin_alert = None
            if record.current_price and record.cost:
                margin = (record.current_price - record.cost) / record.current_price if record.current_price else None
                if margin is not None and margin < 0.12:
                    margin_alert = {
                        "kind": "LOW_MARGIN",
                        "severity": "warn",
                        "message": f"Margin is {margin:.1%} which is below the 12% floor.",
                    }

            gap_alert = None
            if stats and stats["avg_price"] is not None and record.current_price:
                avg_price = float(stats["avg_price"])
                if avg_price < record.current_price * 0.92:
                    gap_alert = {
                        "kind": "PRICE_GAP",
                        "severity": "crit",
                        "message": (
                            f"Average competitor price {avg_price:.2f} undercuts our {record.current_price:.2f} "
                            "by more than 8%."
                        ),
                    }

            for candidate in (margin_alert, gap_alert):
                if candidate:
                    conn.execute(
                        """
                        INSERT INTO agent_alerts (sku, kind, severity, message, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (record.sku, candidate["kind"], candidate["severity"], candidate["message"], now),
                    )
                    candidate["timestamp"] = now
                    alerts.append(candidate)
            conn.commit()

        return {
            "status": "ok",
            "agent": "AlertAgent",
            "sku": record.sku,
            "alerts": alerts,
            "timestamp": now,
        }

    def run_full_workflow(
        self,
        *,
        title: str,
        cost: Optional[float],
        sku: Optional[str] = None,
        currency: str = "USD",
        list_price: Optional[float] = None,
        stock: Optional[int] = None,
        competitor_urls: Optional[Sequence[str]] = None,
        market: str = "DEFAULT",
        notes: Optional[str] = None,
        user_intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        registration = self.register_product(
            title=title,
            cost=cost,
            sku=sku,
            currency=currency,
            list_price=list_price,
            stock=stock,
            competitor_urls=competitor_urls,
            market=market,
            notes=notes,
        )
        if registration.get("status") != "ok":
            return registration

        sku_val = registration["sku"]
        collection = self.collect_market_data(
            sku=sku_val,
            competitor_urls=competitor_urls,
            market=market,
            inject_baseline=registration.get("current_price") or registration.get("cost"),
        )
        optimizer = self.optimize_price(
            sku=sku_val,
            user_request=user_intent,
        )
        alerts = self.evaluate_alerts(sku=sku_val)

        steps = [
            {
                "agent": "InteractionAgent",
                "status": registration["status"],
                "message": f"Product '{registration['title']}' registered for market '{market}'.",
                "details": {
                    "sku": sku_val,
                    "currency": registration["currency"],
                    "current_price": registration["current_price"],
                    "cost": registration["cost"],
                    "competitor_urls": registration["competitor_urls"],
                },
            },
            {
                "agent": collection.get("agent", "DataCollectionAgent"),
                "status": collection.get("status"),
                "message": f"Collected {collection.get('summary', {}).get('count', 0)} competitor quotes.",
                "details": collection.get("summary"),
            },
            {
                "agent": optimizer.get("agent", "PricingOptimizerAgent"),
                "status": optimizer.get("status"),
                "message": "Generated pricing recommendation.",
                "details": {
                    "recommended_price": optimizer.get("recommended_price"),
                    "algorithm": optimizer.get("algorithm"),
                    "confidence": optimizer.get("confidence"),
                    "reason": optimizer.get("reason"),
                },
            },
            {
                "agent": alerts.get("agent", "AlertAgent"),
                "status": alerts.get("status"),
                "message": f"Generated {len(alerts.get('alerts', []))} alert(s).",
                "details": alerts.get("alerts"),
            },
        ]

        return {
            "status": "ok",
            "agent": "SupervisorAgent",
            "sku": sku_val,
            "title": registration["title"],
            "currency": registration["currency"],
            "recommended_price": optimizer.get("recommended_price"),
            "confidence": optimizer.get("confidence"),
            "reason": optimizer.get("reason"),
            "alerts": alerts.get("alerts"),
            "market_snapshot": collection.get("summary"),
            "steps": steps,
        }

    def list_inventory(self, *, search: Optional[str], limit: int) -> Dict[str, Any]:
        self._ensure_schema()
        clause = ""
        params: List[Any] = [self.owner_id, limit]
        if search:
            clause = "AND (sku LIKE ? OR title LIKE ?)"
            params.insert(1, f"%{search}%")
            params.insert(2, f"%{search}%")

        query = f"""
            SELECT sku, title, currency, current_price, cost, stock, updated_at
            FROM product_catalog
            WHERE owner_id=? {clause}
            ORDER BY updated_at DESC
            LIMIT ?
        """
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            items = [dict(r) for r in rows]
        return {"items": items, "total": len(items)}

    def get_inventory_item(self, *, sku: str) -> Dict[str, Any]:
        self._ensure_schema()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT sku, title, currency, current_price, cost, stock, notes, updated_at
                FROM product_catalog
                WHERE sku=? AND owner_id=?
                LIMIT 1
                """,
                (sku, self.owner_id),
            ).fetchone()
        return {"item": dict(row) if row else None}

    def list_pricing(self, *, search: Optional[str], limit: int) -> Dict[str, Any]:
        self._ensure_schema()
        clause = ""
        params: List[Any] = [limit]
        if search:
            clause = "WHERE product_name LIKE ?"
            params.insert(0, f"%{search}%")
        query = f"""
            SELECT product_name, optimized_price, last_update, reason
            FROM pricing_list
            {clause}
            ORDER BY last_update DESC
            LIMIT ?
        """
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            items = [dict(r) for r in rows]
        return {"items": items, "total": len(items)}

    def list_market_data(self, *, search: Optional[str], limit: int) -> Dict[str, Any]:
        self._ensure_schema()
        clause = ""
        params: List[Any] = [limit]
        if search:
            clause = "WHERE product_name LIKE ?"
            params.insert(0, f"%{search}%")

        query = f"""
            SELECT product_name, price, scraped_at, source, features
            FROM market_data
            {clause}
            ORDER BY scraped_at DESC
            LIMIT ?
        """
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            items = []
            for row in rows:
                data = dict(row)
                try:
                    data["features"] = json.loads(data.get("features") or "{}")
                except Exception:
                    pass
                items.append(data)
        return {"items": items, "total": len(items)}

    def list_price_proposals(self, *, sku: Optional[str], limit: int) -> Dict[str, Any]:
        self._ensure_schema()
        clause = ""
        params: List[Any] = [limit]
        if sku:
            clause = "WHERE sku=?"
            params.insert(0, sku)

        query = f"""
            SELECT id, sku, proposed_price, current_price, margin, algorithm, ts
            FROM price_proposals
            {clause}
            ORDER BY ts DESC
            LIMIT ?
        """
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            items = [dict(r) for r in rows]
        return {"items": items, "total": len(items)}

    def list_alerts(self, *, limit: int = 20) -> Dict[str, Any]:
        self._ensure_schema()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT sku, kind, severity, message, created_at
                FROM agent_alerts
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            items = [dict(r) for r in rows]
        return {"items": items, "total": len(items)}

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _normalize_sku(self, value: str) -> str:
        slug = re.sub(r"[^A-Za-z0-9]+", "-", value.upper()).strip("-")
        return slug or f"SKU-{uuid.uuid4().hex[:8].upper()}"

    def _coerce_urls(self, urls: Optional[Sequence[str]]) -> List[str]:
        if not urls:
            return []
        out: List[str] = []
        for url in urls:
            if not url:
                continue
            candidate = str(url).strip()
            if not candidate:
                continue
            out.append(candidate)
        # Deduplicate while preserving order
        seen = set()
        deduped: List[str] = []
        for url in out:
            if url not in seen:
                deduped.append(url)
                seen.add(url)
        return deduped

    def _get_product(self, sku: str) -> Optional[ProductRecord]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT sku, title, currency, current_price, cost, stock
                FROM product_catalog
                WHERE sku=? AND owner_id=?
                LIMIT 1
                """,
                (sku, self.owner_id),
            ).fetchone()
            if not row:
                return None
            return ProductRecord(
                sku=row["sku"],
                title=row["title"],
                currency=row["currency"],
                current_price=row["current_price"],
                cost=row["cost"],
                stock=row["stock"],
            )

    def _fetch_competitor_quote(
        self, *, url: str, fallback_anchor: float, variation: float
    ) -> Dict[str, Any]:
        now = _utc_now()
        if fetch_competitor_price and url.startswith(("http://", "https://")):
            try:
                response = fetch_competitor_price(url)
                if response.get("status") == "success" and response.get("price") is not None:
                    price = _round_price(response["price"])
                    return {
                        "source": url,
                        "price": price,
                        "status": "scraped",
                        "confidence": 0.85,
                        "timestamp": now,
                        "demand_index": self._estimate_demand_index(price, fallback_anchor),
                    }
            except Exception:
                pass

        base = fallback_anchor if fallback_anchor and fallback_anchor > 0 else 20.0
        low = max(base * (1 - variation), 1.0)
        high = base * (1 + variation)
        price = _round_price(random.uniform(low, high))
        return {
            "source": url,
            "price": price,
            "status": "simulated",
            "confidence": 0.55,
            "note": "Fallback synthetic quote (web scrape unavailable).",
            "timestamp": now,
            "demand_index": self._estimate_demand_index(price, fallback_anchor),
        }

    def _estimate_demand_index(self, competitor_price: float, anchor_price: float) -> float:
        if not anchor_price:
            return round(random.uniform(0.3, 0.9), 2)
        gap = anchor_price - competitor_price
        normalized = 0.5 + (gap / max(anchor_price, 1.0)) * 0.5
        return round(min(max(normalized, 0.1), 0.95), 2)


HUB = AgentHub()
