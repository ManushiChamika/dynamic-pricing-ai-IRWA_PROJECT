from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .optimizer import Features, optimize

logger = logging.getLogger("price_optimizer_tools")

class Tools:
    def __init__(self, app_db: Path, market_db: Path):
        self.app_db = app_db
        self.market_db = market_db

    async def get_product_info(self, sku: str) -> Dict[str, Any]:
        uri_app = f"file:{self.app_db.as_posix()}?mode=ro"
        try:
            with sqlite3.connect(uri_app, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT sku, title, current_price, cost FROM product_catalog WHERE sku=? LIMIT 1",
                    (sku,),
                ).fetchone()
                if not row:
                    row = conn.execute(
                        "SELECT sku, title, current_price, cost FROM product_catalog WHERE title LIKE ? LIMIT 1",
                        (sku,),
                    ).fetchone()
                if row:
                    return {
                        "ok": True,
                        "sku": row["sku"],
                        "title": row["title"],
                        "current_price": float(row["current_price"]) if row["current_price"] is not None else None,
                        "cost": float(row["cost"]) if row["cost"] is not None else None,
                    }
                return {"ok": False, "error": f"Product not found: {sku}"}
        except Exception as e:
            logger.error(f"Failed to fetch product info for {sku}: {e}")
            return {"ok": False, "error": str(e)}

    async def get_market_intelligence(self, product_title: str) -> Dict[str, Any]:
        uri_market = f"file:{self.market_db.as_posix()}?mode=ro"
        try:
            with sqlite3.connect(uri_market, uri=True) as m:
                m.row_factory = sqlite3.Row
                
                pricing_list_cnt = 0
                market_data_cnt = 0
                try:
                    pricing_list_cnt = m.execute("SELECT COUNT(*) FROM pricing_list").fetchone()[0]
                except Exception:
                    pass
                try:
                    market_data_cnt = m.execute("SELECT COUNT(*) FROM market_data").fetchone()[0]
                except Exception:
                    pass

                competitor_price = None
                r = m.execute(
                    "SELECT optimized_price FROM pricing_list WHERE product_name=? LIMIT 1",
                    (product_title,),
                ).fetchone()
                if r and r[0] is not None:
                    competitor_price = float(r[0])
                else:
                    r2 = m.execute(
                        "SELECT AVG(price) FROM market_data WHERE product_name=?",
                        (product_title,),
                    ).fetchone()
                    if r2 and r2[0] is not None:
                        competitor_price = float(r2[0])

                market_records: List[Tuple[float, str]] = []
                rows = m.execute(
                    "SELECT price, scraped_at FROM market_data WHERE product_name=? ORDER BY scraped_at DESC LIMIT 50",
                    (product_title,),
                ).fetchall()
                market_records = [(float(r["price"]), r["scraped_at"]) for r in rows if r["price"] is not None]

                return {
                    "ok": True,
                    "competitor_price": competitor_price,
                    "record_count": pricing_list_cnt + market_data_cnt,
                    "pricing_list_count": pricing_list_cnt,
                    "market_data_count": market_data_cnt,
                    "market_records": market_records,
                }
        except Exception as e:
            logger.error(f"Failed to fetch market intelligence for {product_title}: {e}")
            return {"ok": False, "error": str(e)}

    async def run_pricing_algorithm(
        self,
        algorithm: str,
        sku: str,
        our_price: float,
        competitor_price: Optional[float],
        cost: Optional[float],
        market_records: List[Tuple[float, str]],
        min_margin: float = 0.12,
    ) -> Dict[str, Any]:
        try:
            features = Features(
                sku=sku,
                our_price=our_price,
                competitor_price=competitor_price,
                cost=cost,
            )
            result = optimize(
                f=features,
                min_price=0.0,
                max_price=1e12,
                min_margin=min_margin,
                trace_id="",
                algorithm=algorithm,
                market_records=market_records,
            )
            return {
                "ok": True,
                "recommended_price": result.get("recommended_price", our_price),
                "confidence": result.get("confidence", 0.6),
                "rationale": result.get("rationale", ""),
            }
        except Exception as e:
            logger.error(f"Failed to run pricing algorithm {algorithm}: {e}")
            return {"ok": False, "error": str(e)}

    async def validate_price(
        self,
        proposed_price: float,
        current_price: float,
        cost: Optional[float],
        min_margin: float = 0.12,
    ) -> Dict[str, Any]:
        try:
            if cost is not None:
                margin = (proposed_price - cost) / proposed_price if proposed_price > 0 else 0
                if margin < min_margin:
                    return {
                        "ok": False,
                        "error": f"Margin {margin:.2%} below minimum {min_margin:.2%}",
                        "valid": False,
                    }
            
            change_pct = abs((proposed_price - current_price) / current_price) if current_price > 0 else 0
            if change_pct > 0.5:
                return {
                    "ok": False,
                    "error": f"Price change {change_pct:.2%} exceeds 50% threshold",
                    "valid": False,
                }

            return {
                "ok": True,
                "valid": True,
                "margin": (proposed_price - cost) / proposed_price if cost and proposed_price > 0 else None,
                "change_pct": change_pct,
            }
        except Exception as e:
            logger.error(f"Failed to validate price: {e}")
            return {"ok": False, "error": str(e)}

    async def publish_price_proposal(
        self,
        sku: str,
        old_price: float,
        new_price: float,
        margin: float = 0.0,
        algorithm: str = "unknown",
    ) -> Dict[str, Any]:
        try:
            from core.agents.agent_sdk.bus_factory import get_bus
            from core.agents.agent_sdk.protocol import Topic

            bus = get_bus()
            proposal_payload = {
                "proposal_id": uuid.uuid4().hex,
                "sku": sku,
                "product_id": sku,
                "old_price": float(old_price),
                "previous_price": float(old_price),
                "new_price": float(new_price),
                "proposed_price": float(new_price),
                "margin": float(margin),
                "algorithm": algorithm,
            }
            await bus.publish(Topic.PRICE_PROPOSAL.value, proposal_payload)
            
            return {
                "ok": True,
                "proposal_id": proposal_payload["proposal_id"],
                "message": f"Published price proposal: {sku} {old_price} → {new_price}",
            }
        except Exception as e:
            logger.error(f"Failed to publish price proposal: {e}")
            return {"ok": False, "error": str(e)}


def get_llm_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "get_product_info",
                "description": "Fetches product information from the catalog including SKU, title, current price, and cost.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "Product SKU or title to look up"
                        }
                    },
                    "required": ["sku"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_market_intelligence",
                "description": "Gathers competitive market data including competitor prices, historical trends, and market record counts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_title": {
                            "type": "string",
                            "description": "Product title to search for in market data"
                        }
                    },
                    "required": ["product_title"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "run_pricing_algorithm",
                "description": "Executes a pricing optimization algorithm (rule_based, ml_model, or profit_maximization) with given market context.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "algorithm": {
                            "type": "string",
                            "description": "Algorithm to use: rule_based, ml_model, or profit_maximization",
                            "enum": ["rule_based", "ml_model", "profit_maximization"]
                        },
                        "sku": {
                            "type": "string",
                            "description": "Product SKU"
                        },
                        "our_price": {
                            "type": "number",
                            "description": "Current price of the product"
                        },
                        "competitor_price": {
                            "type": "number",
                            "description": "Competitor price (can be null)"
                        },
                        "cost": {
                            "type": "number",
                            "description": "Product cost (can be null)"
                        },
                        "market_records": {
                            "type": "array",
                            "description": "Historical market price records as tuples of (price, timestamp)"
                        },
                        "min_margin": {
                            "type": "number",
                            "description": "Minimum profit margin (default 0.12)"
                        }
                    },
                    "required": ["algorithm", "sku", "our_price"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "validate_price",
                "description": "Validates a proposed price against business constraints including minimum margin and maximum price change thresholds.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "proposed_price": {
                            "type": "number",
                            "description": "Proposed new price to validate"
                        },
                        "current_price": {
                            "type": "number",
                            "description": "Current price of the product"
                        },
                        "cost": {
                            "type": "number",
                            "description": "Product cost (can be null)"
                        },
                        "min_margin": {
                            "type": "number",
                            "description": "Minimum profit margin threshold (default 0.12)"
                        }
                    },
                    "required": ["proposed_price", "current_price"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "publish_price_proposal",
                "description": "Publishes a validated price proposal to the event bus for downstream processing by alerts and activity tracking.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "Product SKU"
                        },
                        "old_price": {
                            "type": "number",
                            "description": "Current/old price"
                        },
                        "new_price": {
                            "type": "number",
                            "description": "Proposed/new price"
                        }
                    },
                    "required": ["sku", "old_price", "new_price"]
                }
            }
        }
    ]


async def execute_tool_call(tool_name: str, tool_args: dict, tools_instance: Tools) -> dict:
    logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
    
    if tool_name == "get_product_info":
        result = await tools_instance.get_product_info(tool_args["sku"])
        logger.info(f"get_product_info result: {result}")
        return result
    
    elif tool_name == "get_market_intelligence":
        result = await tools_instance.get_market_intelligence(tool_args["product_title"])
        logger.info(f"get_market_intelligence result: {result}")
        return result
    
    elif tool_name == "run_pricing_algorithm":
        result = await tools_instance.run_pricing_algorithm(
            algorithm=tool_args["algorithm"],
            sku=tool_args["sku"],
            our_price=tool_args["our_price"],
            competitor_price=tool_args.get("competitor_price"),
            cost=tool_args.get("cost"),
            market_records=tool_args.get("market_records", []),
            min_margin=tool_args.get("min_margin", 0.12),
        )
        logger.info(f"run_pricing_algorithm result: {result}")
        return result
    
    elif tool_name == "validate_price":
        result = await tools_instance.validate_price(
            proposed_price=tool_args["proposed_price"],
            current_price=tool_args["current_price"],
            cost=tool_args.get("cost"),
            min_margin=tool_args.get("min_margin", 0.12),
        )
        logger.info(f"validate_price result: {result}")
        return result
    
    elif tool_name == "publish_price_proposal":
        result = await tools_instance.publish_price_proposal(
            sku=tool_args["sku"],
            old_price=tool_args["old_price"],
            new_price=tool_args["new_price"],
        )
        logger.info(f"publish_price_proposal result: {result}")
        return result
    
    else:
        logger.error(f"Unknown tool: {tool_name}")
        return {"ok": False, "error": f"Unknown tool: {tool_name}"}
