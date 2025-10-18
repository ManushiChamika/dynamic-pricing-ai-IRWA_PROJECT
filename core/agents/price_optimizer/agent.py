from __future__ import annotations

import asyncio
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple
from datetime import datetime

from .optimizer import Features, optimize
from .algorithms import ALGORITHMS

try:
    from core.agents.agent_sdk.activity_log import should_trace, activity_log, safe_redact, generate_trace_id
except Exception:
    should_trace = lambda: False  # type: ignore
    activity_log = None  # type: ignore
    def safe_redact(x):  # type: ignore
        return x
    def generate_trace_id():  # type: ignore
        return ""

try:
    from core.events.journal import write_event
except Exception:
    def write_event(topic: str, payload: Dict[str, Any]) -> None:  # type: ignore
        pass

# Optional bus for publishing price proposals
try:
    from core.agents.agent_sdk.bus_factory import get_bus as _get_bus
    from core.agents.agent_sdk.protocol import Topic as _Topic
except Exception:
    _get_bus = None  # type: ignore
    _Topic = None  # type: ignore


@dataclass
class _DBPaths:
    app_db: Path
    market_db: Path


class PricingOptimizerAgent:
    """
    Minimal async Pricing Optimizer workflow suitable for demo.

    - Builds market context from SQLite DBs
    - Picks a simple algorithm label based on user_request intent
    - Calls the heuristic optimizer and returns a structured result
    - Emits activity + journal events so the UI shows progress
    """

    def __init__(
        self, 
        app_db: Optional[Path] = None, 
        market_db: Optional[Path] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        strict_ai_selection: Optional[bool] = None,
    ) -> None:
        root = Path(__file__).resolve().parents[3]
        self.db = _DBPaths(
            app_db=app_db or (root / "app" / "data.db"),
            market_db=market_db or (root / "app" / "data.db"),
        )
        
        self.llm_brain = None
        try:
            from .llm_brain import LLMBrain
            self.llm_brain = LLMBrain(
                api_key=api_key,
                base_url=base_url,
                model=model,
                strict_ai_selection=strict_ai_selection,
            )
        except Exception:
            pass

    async def process_full_workflow(
        self,
        user_request: str,
        product_name: str,
        wait_seconds: int = 2,
        max_wait_attempts: int = 3,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        started = datetime.now()
        local_trace = trace_id or generate_trace_id()

        # Log start
        try:
            if should_trace():
                activity_log.log(
                    agent="PriceOptimizer",
                    action="workflow.start",
                    status="in_progress",
                    message=f"Request: {user_request[:80]}...",
                    details=safe_redact({
                        "trace_id": local_trace,
                        "product": product_name,
                        "wait_seconds": wait_seconds,
                        "max_wait_attempts": max_wait_attempts,
                    }),
                )
                write_event("price.workflow", {
                    "trace_id": local_trace,
                    "action": "start",
                    "product": product_name,
                    "request": user_request[:160],
                    "timestamp": started.isoformat(),
                })
        except Exception:
            pass

        # Step 1: Read product info (by SKU first, fallback by title)
        sku = product_name
        title = None
        our_price: Optional[float] = None
        cost: Optional[float] = None
        uri_app = f"file:{self.db.app_db.as_posix()}?mode=ro"
        try:
            with sqlite3.connect(uri_app, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT sku, title, current_price, cost FROM product_catalog WHERE sku=? LIMIT 1",
                    (product_name,),
                ).fetchone()
                if not row:
                    row = conn.execute(
                        "SELECT sku, title, current_price, cost FROM product_catalog WHERE title LIKE ? LIMIT 1",
                        (product_name,),
                    ).fetchone()
                if row:
                    sku = row["sku"]
                    title = row["title"]
                    our_price = float(row["current_price"]) if row["current_price"] is not None else None
                    cost = float(row["cost"]) if row["cost"] is not None else None
        except Exception:
            pass

        if our_price is None:
            # Fail fast with structured error
            err = {
                "status": "error",
                "message": f"Product not found or missing price: {product_name}",
            }
            try:
                if should_trace():
                    activity_log.log(
                        agent="PriceOptimizer",
                        action="workflow.done",
                        status="failed",
                        message=err["message"],
                        details=safe_redact({"trace_id": local_trace}),
                    )
                    write_event("price.workflow", {
                        "trace_id": local_trace,
                        "action": "done",
                        "status": "error",
                        "timestamp": datetime.now().isoformat(),
                        "message": err["message"],
                    })
            except Exception:
                pass
            return err

        # Step 2: Build market context, try two sources
        competitor_price: Optional[float] = None
        pricing_list_cnt = 0
        market_data_cnt = 0
        uri_market = f"file:{self.db.market_db.as_posix()}?mode=ro"
        try:
            with sqlite3.connect(uri_market, uri=True) as m:
                m.row_factory = sqlite3.Row
                try:
                    pricing_list_cnt = m.execute("SELECT COUNT(*) FROM pricing_list").fetchone()[0]
                except Exception:
                    pricing_list_cnt = 0
                try:
                    market_data_cnt = m.execute("SELECT COUNT(*) FROM market_data").fetchone()[0]
                except Exception:
                    market_data_cnt = 0
                # Prefer pricing_list optimized_price; fallback to avg(market_data.price)
                if title:
                    r = m.execute(
                        "SELECT optimized_price FROM pricing_list WHERE product_name=? LIMIT 1",
                        (title,),
                    ).fetchone()
                    if r and r[0] is not None:
                        competitor_price = float(r[0])
                    else:
                        r2 = m.execute(
                            "SELECT AVG(price) FROM market_data WHERE product_name=?",
                            (title,),
                        ).fetchone()
                        if r2 and r2[0] is not None:
                            competitor_price = float(r2[0])
        except Exception:
            pass

        market_context = {
            "record_count": pricing_list_cnt + market_data_cnt,
            "pricing_list_count": pricing_list_cnt,
            "market_data_count": market_data_cnt,
            "competitor_price": competitor_price,
            "our_price": our_price,
            "avg_price": competitor_price,
        }

        algorithm = "rule_based"
        llm_reason = None
        
        if self.llm_brain:
            decision = self.llm_brain.decide_tool(user_request, ALGORITHMS, market_context)
            if "error" not in decision:
                algorithm = decision.get("tool_name", "rule_based")
                llm_reason = decision.get("reason")
            else:
                req_l = (user_request or "").lower()
                if any(k in req_l for k in ("maximize", "profit", "greedy")):
                    algorithm = "profit_maximization"
                elif any(k in req_l for k in ("ml", "predict", "model")):
                    algorithm = "ml_model"
        else:
            req_l = (user_request or "").lower()
            if any(k in req_l for k in ("maximize", "profit", "greedy")):
                algorithm = "profit_maximization"
            elif any(k in req_l for k in ("ml", "predict", "model")):
                algorithm = "ml_model"

        market_records: List[Tuple[float, str]] = []
        uri_market = f"file:{self.db.market_db.as_posix()}?mode=ro"
        try:
            with sqlite3.connect(uri_market, uri=True) as m:
                m.row_factory = sqlite3.Row
                if title:
                    rows = m.execute(
                        "SELECT price, scraped_at FROM market_data WHERE product_name=? ORDER BY scraped_at DESC LIMIT 50",
                        (title,),
                    ).fetchall()
                    market_records = [(float(r["price"]), r["scraped_at"]) for r in rows if r["price"] is not None]
        except Exception:
            pass

        res = optimize(
            f=Features(sku=sku, our_price=float(our_price), competitor_price=competitor_price, cost=cost),
            min_price=0.0,
            max_price=1e12,
            min_margin=0.12,
            trace_id=local_trace,
            algorithm=algorithm,
            market_records=market_records,
        )

        completed = datetime.now()
        out = {
            "status": "ok",
            "price": res.get("recommended_price", our_price),
            "recommended_price": res.get("recommended_price", our_price),
            "confidence": res.get("confidence", 0.6),
            "reason": res.get("rationale", ""),
            "algorithm": algorithm,
            "llm_reason": llm_reason,
            "market_context": market_context,
            "inputs": {
                "sku": sku,
                "title": title,
                "our_price": our_price,
                "cost": cost,
            },
            "duration_ms": int((completed - started).total_seconds() * 1000),
        }

        try:
            if should_trace():
                activity_log.log(
                    agent="PriceOptimizer",
                    action="workflow.done",
                    status="completed",
                    message=f"{sku}: {our_price} → {out['price']}",
                    details=safe_redact({
                        "trace_id": local_trace,
                        "algorithm": algorithm,
                        "market_context": market_context,
                        "result": {k: v for k, v in out.items() if k not in {"market_context"}},
                    }),
                )
                write_event("price.workflow", {
                    "trace_id": local_trace,
                    "action": "done",
                    "status": "ok",
                    "sku": sku,
                    "old_price": our_price,
                    "new_price": out["price"],
                    "algorithm": algorithm,
                    "timestamp": completed.isoformat(),
                })
        except Exception:
            pass

        # Publish a price.proposal event for downstream consumers (Activity/Alerts)
        try:
            if _get_bus is not None and _Topic is not None and out.get("status") == "ok":
                bus = _get_bus()
                proposal_payload = {
                    "proposal_id": uuid.uuid4().hex,
                    "product_id": sku,
                    "previous_price": float(our_price) if our_price is not None else 0.0,
                    "proposed_price": float(out.get("price")),
                }
                # Validation is handled by bus; best-effort publish
                await bus.publish(_Topic.PRICE_PROPOSAL.value, proposal_payload)
        except Exception:
            pass

        return out
