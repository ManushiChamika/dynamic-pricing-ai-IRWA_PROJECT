from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple

from .optimizer import Features, optimize
from .algorithms import ALGORITHMS
from .tools import Tools, get_llm_tools, execute_tool_call

try:
    from core.agents.agent_sdk.activity_log import should_trace, activity_log, safe_redact, generate_trace_id
except Exception:
    should_trace = lambda: False
    activity_log = None
    def safe_redact(x):
        return x
    def generate_trace_id():
        return ""

try:
    from core.events.journal import write_event
except Exception:
    def write_event(topic: str, payload: Dict[str, Any]) -> None:
        pass

try:
    from core.agents.agent_sdk.bus_factory import get_bus as _get_bus
    from core.agents.agent_sdk.protocol import Topic as _Topic
except Exception:
    _get_bus = None
    _Topic = None


@dataclass
class _DBPaths:
    app_db: Path
    market_db: Path


SYSTEM_PROMPT = """You are an autonomous Pricing Optimization Agent for a dynamic pricing system. Your primary goal is to analyze pricing requests and determine optimal prices through multi-step reasoning.

When handling optimization requests:
1. ALWAYS start by calling get_product_info() to fetch current product data
2. Call get_market_intelligence() to gather competitive context
3. Analyze the user request and market data to select the appropriate pricing algorithm:
   - rule_based: Conservative pricing based on competitor averages
   - ml_model: Predictive pricing using historical patterns
   - profit_maximization: Aggressive pricing to maximize margins
4. Call run_pricing_algorithm() with selected algorithm and gathered data
5. Call validate_price() to ensure the proposed price meets business constraints
6. If validation passes, call publish_price_proposal() to emit the final proposal

IMPORTANT: You must complete the entire workflow autonomously. Use tools in sequence to gather data, compute prices, validate, and publish."""


class PricingOptimizerAgent:
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
        
        self.tools = Tools(self.db.app_db, self.db.market_db)
        self.llm = None
        self.logger = logging.getLogger("price_optimizer")
        self.bus = None
        
        try:
            from core.agents.llm_client import get_llm_client
            self.llm = get_llm_client()
            if self.llm and self.llm.is_available():
                self.logger.info("LLM brain initialized successfully - autonomous mode enabled")
            else:
                self.logger.warning("LLM unavailable - will use fallback heuristic mode")
        except Exception as e:
            self.logger.warning(f"Failed to initialize LLM: {e}")
        
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

    async def start(self):
        if _get_bus is None or _Topic is None:
            self.logger.error("Event bus not available - cannot start autonomous agent")
            return
        
        self.bus = _get_bus()
        self.bus.subscribe(_Topic.OPTIMIZATION_REQUEST.value, self.on_optimization_request)
        
        self.logger.info(
            f"PricingOptimizerAgent started - LLM={'enabled' if self.llm and self.llm.is_available() else 'disabled'}"
        )
        
        if self.bus and _Topic:
            await self.bus.publish(_Topic.ALERT.value, {
                "ts": datetime.now().isoformat(),
                "sku": "SYS",
                "severity": "info",
                "title": f"PricingOptimizerAgent ready (LLM={'enabled' if self.llm and self.llm.is_available() else 'disabled'})"
            })

    async def on_optimization_request(self, request: Any):
        request_dict = self._to_dict(request)
        
        product_identifier = request_dict.get("product_name") or request_dict.get("sku") or request_dict.get("product_id")
        user_request = request_dict.get("user_request", "Optimize price")
        
        if not product_identifier:
            self.logger.error("Optimization request missing product identifier")
            return
        
        self.logger.info(f"Received optimization request for {product_identifier}: {user_request}")
        
        if self.llm and self.llm.is_available():
            await self._handle_autonomous_optimization(product_identifier, user_request)
        else:
            await self._handle_fallback_optimization(product_identifier, user_request)

    async def _handle_autonomous_optimization(self, product_identifier: str, user_request: str):
        try:
            prompt = f"""A new pricing optimization request has been received:

Product: {product_identifier}
User Request: {user_request}

You must complete the full pricing optimization workflow:
1. Fetch product information
2. Gather market intelligence
3. Select and run appropriate pricing algorithm
4. Validate the proposed price
5. Publish the price proposal

Use your tools to complete this workflow autonomously."""

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            tools_schema = get_llm_tools()
            
            async def get_product_info_async(sku: str):
                return await execute_tool_call("get_product_info", {"sku": sku}, self.tools)
            
            async def get_market_intelligence_async(product_title: str):
                return await execute_tool_call("get_market_intelligence", {"product_title": product_title}, self.tools)
            
            async def run_pricing_algorithm_async(algorithm: str, sku: str, our_price: float, 
                                                 competitor_price: float = None, cost: float = None,
                                                 market_records: list = None, min_margin: float = 0.12):
                return await execute_tool_call("run_pricing_algorithm", {
                    "algorithm": algorithm, "sku": sku, "our_price": our_price,
                    "competitor_price": competitor_price, "cost": cost,
                    "market_records": market_records or [], "min_margin": min_margin
                }, self.tools)
            
            async def validate_price_async(proposed_price: float, current_price: float,
                                          cost: float = None, min_margin: float = 0.12):
                return await execute_tool_call("validate_price", {
                    "proposed_price": proposed_price, "current_price": current_price,
                    "cost": cost, "min_margin": min_margin
                }, self.tools)
            
            async def publish_price_proposal_async(sku: str, old_price: float, new_price: float):
                return await execute_tool_call("publish_price_proposal", {
                    "sku": sku, "old_price": old_price, "new_price": new_price
                }, self.tools)
            
            functions_map = {
                "get_product_info": get_product_info_async,
                "get_market_intelligence": get_market_intelligence_async,
                "run_pricing_algorithm": run_pricing_algorithm_async,
                "validate_price": validate_price_async,
                "publish_price_proposal": publish_price_proposal_async
            }
            
            try:
                result = self.llm.chat_with_tools(
                    messages=messages,
                    tools=tools_schema,
                    functions_map=functions_map,
                    max_rounds=8,
                    max_tokens=2000
                )
                
                self.logger.info(f"LLM autonomous optimization completed: {result}")
                
            except Exception as e:
                self.logger.error(f"LLM optimization failed: {e}")
                await self._handle_fallback_optimization(product_identifier, user_request)
                
        except Exception as e:
            self.logger.error(f"Autonomous optimization failed: {e}")

    async def _handle_fallback_optimization(self, product_identifier: str, user_request: str):
        self.logger.info(f"Using fallback heuristic optimization for {product_identifier}")
        
        trace_id = generate_trace_id()
        started = datetime.now()
        
        try:
            if should_trace():
                activity_log.log(
                    agent="PriceOptimizer",
                    action="fallback.start",
                    status="in_progress",
                    message=f"Fallback optimization: {product_identifier}",
                    details=safe_redact({"trace_id": trace_id, "product": product_identifier}),
                )
        except Exception:
            pass
        
        product_info = await self.tools.get_product_info(product_identifier)
        if not product_info.get("ok"):
            self.logger.error(f"Product not found: {product_identifier}")
            return
        
        sku = product_info["sku"]
        title = product_info["title"]
        our_price = product_info["current_price"]
        cost = product_info["cost"]
        
        if our_price is None:
            self.logger.error(f"Product missing price: {product_identifier}")
            return
        
        market_intel = await self.tools.get_market_intelligence(title)
        competitor_price = market_intel.get("competitor_price") if market_intel.get("ok") else None
        market_records = market_intel.get("market_records", []) if market_intel.get("ok") else []
        
        algorithm = "rule_based"
        if self.llm_brain:
            market_context = {
                "competitor_price": competitor_price,
                "our_price": our_price,
                "record_count": market_intel.get("record_count", 0) if market_intel.get("ok") else 0,
            }
            decision = self.llm_brain.decide_tool(user_request, ALGORITHMS, market_context)
            if "error" not in decision:
                algorithm = decision.get("tool_name", "rule_based")
        else:
            req_l = (user_request or "").lower()
            if any(k in req_l for k in ("maximize", "profit", "greedy")):
                algorithm = "profit_maximization"
            elif any(k in req_l for k in ("ml", "predict", "model")):
                algorithm = "ml_model"
        
        algo_result = await self.tools.run_pricing_algorithm(
            algorithm=algorithm,
            sku=sku,
            our_price=our_price,
            competitor_price=competitor_price,
            cost=cost,
            market_records=market_records,
            min_margin=0.12,
        )
        
        if not algo_result.get("ok"):
            self.logger.error(f"Algorithm failed: {algo_result.get('error')}")
            return
        
        proposed_price = algo_result["recommended_price"]
        
        validation = await self.tools.validate_price(
            proposed_price=proposed_price,
            current_price=our_price,
            cost=cost,
            min_margin=0.12,
        )
        
        if not validation.get("valid", False):
            self.logger.warning(f"Price validation failed: {validation.get('error')} - publishing anyway")
        
        margin = validation.get("margin", 0.0)
        
        publish_result = await self.tools.publish_price_proposal(
            sku=sku,
            old_price=our_price,
            new_price=proposed_price,
            margin=margin,
            algorithm=algorithm,
        )
        
        completed = datetime.now()
        
        if publish_result.get("ok"):
            self.logger.info(f"Fallback optimization completed: {sku} {our_price} → {proposed_price}")
            try:
                if should_trace():
                    activity_log.log(
                        agent="PriceOptimizer",
                        action="fallback.done",
                        status="completed",
                        message=f"{sku}: {our_price} → {proposed_price}",
                        details=safe_redact({
                            "trace_id": trace_id,
                            "algorithm": algorithm,
                            "proposed_price": proposed_price,
                        }),
                    )
            except Exception:
                pass

    @staticmethod
    def _to_dict(obj: Any) -> Dict[str, Any]:
        fn = getattr(obj, "model_dump", None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
        fn = getattr(obj, "dict", None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
        j = getattr(obj, "model_dump_json", None)
        if callable(j):
            try:
                return json.loads(j())
            except Exception:
                pass
        return getattr(obj, "__dict__", {}) or {}

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

        try:
            if _get_bus is not None and _Topic is not None and out.get("status") == "ok":
                bus = _get_bus()
                proposal_payload = {
                    "proposal_id": uuid.uuid4().hex,
                    "product_id": sku,
                    "previous_price": float(our_price) if our_price is not None else 0.0,
                    "proposed_price": float(out.get("price")),
                }
                await bus.publish(_Topic.PRICE_PROPOSAL.value, proposal_payload)
        except Exception:
            pass

        return out
