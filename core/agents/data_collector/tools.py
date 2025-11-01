from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("data_collector_tools")

class Tools:
    def __init__(self, repo):
        self.repo = repo

    async def get_all_products(self) -> Dict[str, Any]:
        try:
            uri_app = f"file:{self.repo.path.as_posix()}?mode=ro"
            import sqlite3
            with sqlite3.connect(uri_app, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT sku, title, current_price, updated_at, source_url FROM product_catalog LIMIT 100"
                ).fetchall()
                
                products = [
                    {
                        "sku": r["sku"],
                        "title": r["title"],
                        "current_price": float(r["current_price"]) if r["current_price"] else None,
                        "updated_at": r["updated_at"],
                        "source_url": r["source_url"],
                    }
                    for r in rows
                ]
                
                return {
                    "ok": True,
                    "products": products,
                    "count": len(products),
                }
        except Exception as e:
            logger.error(f"Failed to get all products: {e}")
            return {"ok": False, "error": str(e)}

    async def check_data_freshness(self, sku: str, market: str = "DEFAULT") -> Dict[str, Any]:
        try:
            uri_app = f"file:{self.repo.path.as_posix()}?mode=ro"
            import sqlite3
            with sqlite3.connect(uri_app, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    """
                    SELECT MAX(ts) as last_ts, COUNT(*) as tick_count
                    FROM market_ticks
                    WHERE sku=? AND market=?
                    """,
                    (sku, market),
                ).fetchone()
                
                if not row or not row["last_ts"]:
                    return {
                        "ok": True,
                        "sku": sku,
                        "market": market,
                        "has_data": False,
                        "last_update": None,
                        "minutes_stale": None,
                        "tick_count": 0,
                        "is_stale": True,
                    }
                
                last_ts = datetime.fromisoformat(row["last_ts"])
                now = datetime.now(timezone.utc)
                if last_ts.tzinfo is None:
                    last_ts = last_ts.replace(tzinfo=timezone.utc)
                
                minutes_stale = (now - last_ts).total_seconds() / 60
                
                return {
                    "ok": True,
                    "sku": sku,
                    "market": market,
                    "has_data": True,
                    "last_update": row["last_ts"],
                    "minutes_stale": minutes_stale,
                    "tick_count": row["tick_count"],
                    "is_stale": minutes_stale > 60,
                }
        except Exception as e:
            logger.error(f"Failed to check data freshness for {sku}: {e}")
            return {"ok": False, "error": str(e)}

    async def get_stale_products(self, threshold_minutes: int = 60) -> Dict[str, Any]:
        try:
            uri_app = f"file:{self.repo.path.as_posix()}?mode=ro"
            import sqlite3
            
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=threshold_minutes)).isoformat()
            
            with sqlite3.connect(uri_app, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                
                rows = conn.execute(
                    """
                    SELECT 
                        pc.sku,
                        pc.title,
                        pc.source_url,
                        MAX(mt.ts) as last_update,
                        COUNT(mt.id) as tick_count
                    FROM product_catalog pc
                    LEFT JOIN market_ticks mt ON pc.sku = mt.sku
                    GROUP BY pc.sku, pc.title, pc.source_url
                    HAVING last_update IS NULL OR last_update < ?
                    ORDER BY 
                        CASE WHEN pc.source_url IS NOT NULL THEN 0 ELSE 1 END,
                        last_update ASC NULLS FIRST
                    LIMIT 20
                    """,
                    (cutoff,),
                ).fetchall()
                
                stale_products = []
                for r in rows:
                    last_ts = None
                    minutes_stale = None
                    
                    if r["last_update"]:
                        last_ts = datetime.fromisoformat(r["last_update"])
                        now = datetime.now(timezone.utc)
                        if last_ts.tzinfo is None:
                            last_ts = last_ts.replace(tzinfo=timezone.utc)
                        minutes_stale = (now - last_ts).total_seconds() / 60
                    
                    stale_products.append({
                        "sku": r["sku"],
                        "title": r["title"],
                        "source_url": r["source_url"],
                        "last_update": r["last_update"],
                        "minutes_stale": minutes_stale,
                        "tick_count": r["tick_count"] or 0,
                    })
                
                return {
                    "ok": True,
                    "stale_products": stale_products,
                    "count": len(stale_products),
                    "threshold_minutes": threshold_minutes,
                }
        except Exception as e:
            logger.error(f"Failed to get stale products: {e}")
            return {"ok": False, "error": str(e)}

    async def start_collection_job(
        self,
        sku: str,
        market: str = "DEFAULT",
        connector: str = "mock",
        depth: int = 5,
    ) -> Dict[str, Any]:
        try:
            from core.agents.agent_sdk.bus_factory import get_bus
            from core.agents.agent_sdk.protocol import Topic
            from core.payloads import MarketFetchRequestPayload
            
            request_id = uuid.uuid4().hex
            
            urls = []
            if connector == "web_scraper":
                uri_app = f"file:{self.repo.path.as_posix()}?mode=ro"
                import sqlite3
                with sqlite3.connect(uri_app, uri=True) as conn:
                    row = conn.execute(
                        "SELECT source_url FROM product_catalog WHERE sku = ?",
                        (sku,),
                    ).fetchone()
                    if row and row[0]:
                        urls = [row[0]]
            
            request_payload: MarketFetchRequestPayload = {
                "request_id": request_id,
                "sku": sku,
                "market": market,
                "sources": [connector],
                "urls": urls,
                "depth": depth,
                "horizon_minutes": 60,
            }
            
            bus = get_bus()
            await bus.publish(Topic.MARKET_FETCH_REQUEST.value, request_payload)
            
            return {
                "ok": True,
                "request_id": request_id,
                "sku": sku,
                "market": market,
                "connector": connector,
                "depth": depth,
                "urls": urls,
                "message": f"Collection job started for {sku}",
            }
        except Exception as e:
            logger.error(f"Failed to start collection job for {sku}: {e}")
            return {"ok": False, "error": str(e)}

    async def get_active_jobs(self) -> Dict[str, Any]:
        try:
            uri_app = f"file:{self.repo.path.as_posix()}?mode=ro"
            import sqlite3
            with sqlite3.connect(uri_app, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT id, sku, market, connector, status, created_at, started_at
                    FROM ingestion_jobs
                    WHERE status IN ('QUEUED', 'RUNNING')
                    ORDER BY created_at DESC
                    LIMIT 50
                    """
                ).fetchall()
                
                jobs = [
                    {
                        "id": r["id"],
                        "sku": r["sku"],
                        "market": r["market"],
                        "connector": r["connector"],
                        "status": r["status"],
                        "created_at": r["created_at"],
                        "started_at": r["started_at"],
                    }
                    for r in rows
                ]
                
                return {
                    "ok": True,
                    "active_jobs": jobs,
                    "count": len(jobs),
                }
        except Exception as e:
            logger.error(f"Failed to get active jobs: {e}")
            return {"ok": False, "error": str(e)}

    async def get_recent_jobs(self, limit: int = 10) -> Dict[str, Any]:
        try:
            uri_app = f"file:{self.repo.path.as_posix()}?mode=ro"
            import sqlite3
            with sqlite3.connect(uri_app, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT id, sku, market, connector, status, created_at, finished_at, error
                    FROM ingestion_jobs
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
                
                jobs = [
                    {
                        "id": r["id"],
                        "sku": r["sku"],
                        "market": r["market"],
                        "connector": r["connector"],
                        "status": r["status"],
                        "created_at": r["created_at"],
                        "finished_at": r["finished_at"],
                        "error": r["error"],
                    }
                    for r in rows
                ]
                
                return {
                    "ok": True,
                    "recent_jobs": jobs,
                    "count": len(jobs),
                }
        except Exception as e:
            logger.error(f"Failed to get recent jobs: {e}")
            return {"ok": False, "error": str(e)}


def get_llm_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "get_all_products",
                "description": "Fetches all products from the catalog to understand what items need market data monitoring.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_data_freshness",
                "description": "Checks the freshness of market data for a specific product by examining when it was last updated.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "Product SKU to check"
                        },
                        "market": {
                            "type": "string",
                            "description": "Market identifier (default: DEFAULT)"
                        }
                    },
                    "required": ["sku"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_stale_products",
                "description": "Identifies products with stale market data that may need refreshing. Returns products ordered by staleness.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "threshold_minutes": {
                            "type": "number",
                            "description": "Age threshold in minutes to consider data stale (default: 60)"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "start_collection_job",
                "description": "Initiates a new market data collection job for a specific product. This will gather fresh competitor pricing and market intelligence.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "description": "Product SKU to collect data for"
                        },
                        "market": {
                            "type": "string",
                            "description": "Market identifier (default: DEFAULT)"
                        },
                        "connector": {
                            "type": "string",
                            "description": "Data connector to use (default: mock)",
                            "enum": ["mock", "web_scraper"]
                        },
                        "depth": {
                            "type": "number",
                            "description": "Number of data points to collect (default: 5)"
                        }
                    },
                    "required": ["sku"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_active_jobs",
                "description": "Lists all currently running or queued collection jobs to avoid duplicate work and monitor system load.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_recent_jobs",
                "description": "Retrieves recently completed collection jobs to understand recent activity and success rates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "number",
                            "description": "Number of recent jobs to return (default: 10)"
                        }
                    },
                    "required": []
                }
            }
        }
    ]


async def execute_tool_call(tool_name: str, tool_args: dict, tools_instance: Tools) -> dict:
    logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
    
    if tool_name == "get_all_products":
        result = await tools_instance.get_all_products()
        logger.info(f"get_all_products result: {result}")
        return result
    
    elif tool_name == "check_data_freshness":
        result = await tools_instance.check_data_freshness(
            sku=tool_args["sku"],
            market=tool_args.get("market", "DEFAULT"),
        )
        logger.info(f"check_data_freshness result: {result}")
        return result
    
    elif tool_name == "get_stale_products":
        result = await tools_instance.get_stale_products(
            threshold_minutes=tool_args.get("threshold_minutes", 60),
        )
        logger.info(f"get_stale_products result: {result}")
        return result
    
    elif tool_name == "start_collection_job":
        result = await tools_instance.start_collection_job(
            sku=tool_args["sku"],
            market=tool_args.get("market", "DEFAULT"),
            connector=tool_args.get("connector", "mock"),
            depth=tool_args.get("depth", 5),
        )
        logger.info(f"start_collection_job result: {result}")
        return result
    
    elif tool_name == "get_active_jobs":
        result = await tools_instance.get_active_jobs()
        logger.info(f"get_active_jobs result: {result}")
        return result
    
    elif tool_name == "get_recent_jobs":
        result = await tools_instance.get_recent_jobs(
            limit=tool_args.get("limit", 10),
        )
        logger.info(f"get_recent_jobs result: {result}")
        return result
    
    else:
        logger.error(f"Unknown tool: {tool_name}")
        return {"ok": False, "error": f"Unknown tool: {tool_name}"}
