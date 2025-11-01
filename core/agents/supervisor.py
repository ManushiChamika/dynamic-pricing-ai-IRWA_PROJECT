from __future__ import annotations

import asyncio
import time
import sqlite3
from typing import Any, Dict, List, Optional
from pathlib import Path

from core.tool_registry import get_tool_registry
from core.agents.data_collector.repo import DataRepo
from core.agents.data_collector.collector import DataCollector
from core.agents.agent_sdk.mcp_client import get_data_collector_client
import uuid
from core.agents.price_optimizer.agent import PricingOptimizerAgent
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic
from core.workflow_templates import collect_and_optimize_prelude



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
        use_templates: bool = True,
    ) -> None:
        self.repo = repo or DataRepo()
        self.collector = collector or DataCollector(self.repo)
        self.optimizer = optimizer or PricingOptimizerAgent()
        self.dc_client = get_data_collector_client()
        self.tool_registry = get_tool_registry()
        self.concurrency = max(1, int(concurrency))
        self.use_templates = bool(use_templates)

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
                    if self.use_templates:
                        pre = await collect_and_optimize_prelude(row, timeout_s=timeout_s)
                        summary.update({k: v for k, v in pre.items() if k in {"job_id", "job_status"}})
                        if not pre.get("ok") or pre.get("job_status") != "DONE":
                            results[sku] = summary
                            return
                    else:
                        await self.tool_registry.execute_tool("upsert_product", product_data=row)
                        start_res = await self.tool_registry.execute_tool(
                            "start_data_collection",
                            sku=sku,
                            market=market,
                            connector=connector,
                            depth=depth,
                        )
                        if not start_res.get("ok"):
                            summary.update({"job_start": "error", "error": start_res})
                            results[sku] = summary
                            return
                        job_id = start_res["job_id"]
                        summary["job_id"] = job_id
                        t0 = time.time()
                        status = None
                        while time.time() - t0 < timeout_s:
                            st = await self.tool_registry.execute_tool("get_job_status", job_id=job_id)
                            job = st.get("job") if st.get("ok") else None
                            status = (job or {}).get("status")
                            if status in {"DONE", "FAILED", "CANCELLED"}:
                                break
                            await asyncio.sleep(0.25)
                        summary["job_status"] = status or "UNKNOWN"
                        if status != "DONE":
                            results[sku] = summary
                            return

                    self._seed_market_if_needed(sku)

                    opt_res = await self.tool_registry.execute_tool(
                        "optimize_price", sku=sku, objective="maximize profit"
                    )
                    summary["optimizer"] = opt_res
                    if not isinstance(opt_res, dict) or opt_res.get("status") != "ok":
                        results[sku] = summary
                        return


                    price = opt_res.get("recommended_price") or opt_res.get("price")
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

                    # Persist row with generated proposal_id reused for event
                    proposal_id = str(uuid.uuid4())
                    await self.repo.insert_price_proposal(
                        {
                            "id": proposal_id,
                            "sku": pp.sku,
                            "proposed_price": pp.proposed_price,
                            "current_price": pp.current_price,
                            "margin": pp.margin,
                            "algorithm": pp.algorithm,
                            "ts": pp.timestamp.isoformat(),
                        }
                    )

                    # Publish event (let governance/auto-applier decide on apply)
                    payload = {
                        "proposal_id": proposal_id,
                        "product_id": sku,
                        "previous_price": float(current_price or 0.0),
                        "proposed_price": float(price),
                    }
                    await get_bus().publish(Topic.PRICE_PROPOSAL.value, payload)
                    summary["proposal_published"] = True



                except Exception as e:
                    summary["error"] = str(e)
                finally:
                    results[sku] = summary

        await asyncio.gather(*(worker(r) for r in rows))
        return {"items": results, "count": len(results)}

    # ----------------- helpers -----------------
    def _seed_market_if_needed(self, sku: str, owner_id: int = 1) -> None:
        """Ensure app/data.db has some competitor rows for the optimizer.

        This POC method seeds minimal rows if none exist.
        """
        root = Path(__file__).resolve().parents[2]
        mdb = (root / "app" / "data.db").as_posix()
        conn = sqlite3.connect(mdb, check_same_thread=False)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS market_data (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL, product_name TEXT NOT NULL, price REAL NOT NULL, update_time TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS pricing_list (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL, product_name TEXT NOT NULL, optimized_price REAL NOT NULL, last_update TEXT DEFAULT CURRENT_TIMESTAMP, reason TEXT)"
        )
        cur.execute("SELECT COUNT(*) FROM market_data WHERE product_name=? AND owner_id=?", (sku, owner_id))
        n = cur.fetchone()[0]
        if n == 0:
            now = time.strftime("%Y-%m-%dT%H:%M:%S")
            for p in (98.0, 100.0, 101.5, 99.5):
                cur.execute(
                    "INSERT INTO market_data (owner_id, product_name, price, update_time) VALUES (?,?,?,?)",
                    (owner_id, sku, float(p), now),
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
            """CREATE TABLE IF NOT EXISTS product_catalog (
                   sku TEXT, 
                   owner_id TEXT, 
                   title TEXT, 
                   currency TEXT, 
                   current_price REAL, 
                   cost REAL, 
                   stock INTEGER, 
                   updated_at TEXT,
                   PRIMARY KEY (sku, owner_id)
               )"""
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





