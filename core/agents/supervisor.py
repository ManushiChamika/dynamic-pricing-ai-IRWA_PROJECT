from __future__ import annotations

import asyncio
import time
import sqlite3
from typing import Any, Dict, List, Optional
from pathlib import Path

from core.agents.data_collector.repo import DataRepo
from core.agents.data_collector.collector import DataCollector
from core.agents.data_collector import mcp_server
from core.agents.pricing_optimizer import PricingOptimizerAgent
from core.bus import bus
from core.protocol import Topic
from core.models import PriceProposal


class Supervisor:
    """Lightweight orchestrator for end-to-end POC flows.

    Orchestrates: catalog import -> start collection -> wait -> optimize ->
    persist + publish price proposals (and optionally auto-apply via events).
    """

    def __init__(
        self,
        repo: Optional[DataRepo] = None,
        collector: Optional[DataCollector] = None,
        optimizer: Optional[PricingOptimizerAgent] = None,
        concurrency: int = 4,
    ) -> None:
        self.repo = repo or DataRepo()
        self.collector = collector or DataCollector(self.repo)
        self.optimizer = optimizer or PricingOptimizerAgent()
        self.concurrency = max(1, int(concurrency))

    async def run_for_catalog(
        self, rows: List[Dict[str, Any]], apply_auto: bool = False, timeout_s: int = 60
    ) -> Dict[str, Any]:
        await self.repo.init()

        sem = asyncio.Semaphore(self.concurrency)
        results: Dict[str, Any] = {}

        async def worker(row: Dict[str, Any]) -> None:
            sku: str = str(row.get("sku") or "").strip()
            market: str = str(row.get("market") or "DEFAULT")
            connector: str = str(row.get("connector") or "mock")
            depth: int = int(row.get("depth") or 3)
            if not sku:
                return

            async with sem:
                summary: Dict[str, Any] = {"sku": sku}
                try:
                    # 1) Upsert product row
                    await self.repo.upsert_products([row])

                    # 2) Start collection job via MCP
                    start_res = await mcp_server.start_collection(
                        sku, market=market, connector=connector, depth=depth
                    )
                    if not start_res.get("ok"):
                        summary.update({"job_start": "error", "error": start_res})
                        results[sku] = summary
                        return
                    job_id = start_res["job_id"]
                    summary["job_id"] = job_id

                    # 3) Poll job status until DONE/FAILED (timeout)
                    t0 = time.time()
                    status = None
                    while time.time() - t0 < timeout_s:
                        st = await mcp_server.get_job_status(job_id)
                        job = st.get("job") if st.get("ok") else None
                        status = (job or {}).get("status")
                        if status in {"DONE", "FAILED", "CANCELLED"}:
                            break
                        await asyncio.sleep(0.25)
                    summary["job_status"] = status or "UNKNOWN"
                    if status != "DONE":
                        results[sku] = summary
                        return

                    # Ensure market.db has some data for optimizer to read
                    self._seed_market_if_needed(sku)

                    # 4) Run optimizer synchronously in executor
                    loop = asyncio.get_running_loop()
                    opt_res = await loop.run_in_executor(
                        None,
                        lambda: self.optimizer.process_full_workflow(
                            "maximize profit", sku
                        ),
                    )
                    summary["optimizer"] = opt_res
                    if not isinstance(opt_res, dict) or opt_res.get("status") != "success":
                        results[sku] = summary
                        return

                    price = opt_res.get("price")
                    algorithm = opt_res.get("algorithm")
                    if price is None:
                        results[sku] = summary
                        return

                    # 5) Persist and publish a PriceProposal
                    current_price, cost = self._read_product_prices(sku)
                    margin = (
                        (float(price) - float(cost)) / float(price)
                        if (cost is not None and float(price) > 0)
                        else 1.0
                    )
                    pp = PriceProposal(
                        sku=sku,
                        proposed_price=float(price),
                        current_price=float(current_price or price),
                        margin=float(margin),
                        algorithm=str(algorithm or "supervisor"),
                    )

                    # Persist row
                    await self.repo.insert_price_proposal(
                        {
                            "sku": pp.sku,
                            "proposed_price": pp.proposed_price,
                            "current_price": pp.current_price,
                            "margin": pp.margin,
                            "algorithm": pp.algorithm,
                            "ts": pp.timestamp.isoformat(),
                        }
                    )

                    # Publish event (let AutoApplier decide on apply)
                    await bus.publish(Topic.PRICE_PROPOSAL.value, pp)
                    summary["proposal_published"] = True

                except Exception as e:
                    summary["error"] = str(e)
                finally:
                    results[sku] = summary

        await asyncio.gather(*(worker(r) for r in rows))
        return {"items": results, "count": len(results)}

    # ----------------- helpers -----------------
    def _seed_market_if_needed(self, sku: str) -> None:
        """Ensure market.db has some competitor rows for the optimizer.

        This POC method seeds minimal rows if none exist.
        """
        root = Path(__file__).resolve().parents[2]
        mdb = (root / "data" / "market.db").as_posix()
        conn = sqlite3.connect(mdb, check_same_thread=False)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS market_data (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT NOT NULL, price REAL NOT NULL, update_time TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS pricing_list (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT NOT NULL, optimized_price REAL NOT NULL, last_update TEXT DEFAULT CURRENT_TIMESTAMP, reason TEXT)"
        )
        cur.execute("SELECT COUNT(*) FROM market_data WHERE product_name=?", (sku,))
        n = cur.fetchone()[0]
        if n == 0:
            now = time.strftime("%Y-%m-%dT%H:%M:%S")
            for p in (98.0, 100.0, 101.5, 99.5):
                cur.execute(
                    "INSERT INTO market_data (product_name, price, update_time) VALUES (?,?,?)",
                    (sku, float(p), now),
                )
            conn.commit()
        conn.close()

    def _read_product_prices(self, sku: str) -> tuple[Optional[float], Optional[float]]:
        """Read current_price and cost from product_catalog in app/data.db."""
        root = Path(__file__).resolve().parents[2]
        adb = (root / "app" / "data.db").as_posix()
        conn = sqlite3.connect(adb, check_same_thread=False)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS product_catalog (sku TEXT PRIMARY KEY, title TEXT, currency TEXT, current_price REAL, cost REAL, stock INTEGER, updated_at TEXT)"
        )
        cur.execute(
            "SELECT current_price, cost FROM product_catalog WHERE sku=? LIMIT 1",
            (sku,),
        )
        r = cur.fetchone()
        conn.close()
        if r:
            cp = float(r[0]) if r[0] is not None else None
            cost = float(r[1]) if r[1] is not None else None
            return cp, cost
        return None, None



