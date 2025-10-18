import os
import sqlite3
from pathlib import Path

from datetime import datetime
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
from typing import Any, Dict, List, Optional
import subprocess
import platform

# Load .env variables if available
if 'load_dotenv' in globals() and callable(load_dotenv):
    load_dotenv()

# Optional LLM helper
try:
    from core.agents.llm_client import get_llm_client
except Exception:
    get_llm_client = None

class UserInteractionAgent:
    def __init__(self, user_name, mode: str = "user"):
        self.user_name = user_name
        self.mode = (mode or "user").lower()
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.model_name = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")
        self.keywords = [
            "price", "pricing", "discount", "offer", "demand", "supply",
            "cost", "profit", "margin", "dynamic pricing", "price optimization"
        ]
        # Feature flags
        self.enable_sound = os.getenv("SOUND_NOTIFICATIONS", "0").strip() in {"1", "true", "True", "yes", "on"}
        # Memory to store conversation history
        self.memory = []
        # Resolve DB paths
        root = Path(__file__).resolve().parents[3]
        self.app_db = root / "app" / "data.db"
        self.market_db = root / "data" / "market.db"
        # Last-inference metadata (populated on LLM calls)
        self.last_model = None
        self.last_provider = None

    def _play_completion_sound(self):
        """Play a sound to indicate task completion (guarded by feature flag)."""
        if not getattr(self, "enable_sound", False):
            return
        try:
            if platform.system() == 'Windows':
                subprocess.call(['powershell', '-c', '[console]::beep(800, 1200)'], shell=True)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['afplay', '/System/Library/Sounds/Glass.aiff'])
            elif platform.system() == 'Linux':
                subprocess.call(['beep', '-f', '800', '-l', '1200'])
        except Exception:
            pass  # Silent failure if sound not available



    def is_dynamic_pricing_related(self, message):
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.keywords)

    def add_to_memory(self, role, content):
        """Add message to memory"""
        self.memory.append({"role": role, "content": content})

    def get_response(self, message):
        """Return an LLM-powered response for any query when available.

        Behavior:
        - If an LLM client is available, forward the message (with memory/system prompt) and return the model answer.
        - If LLM is not available, keep the original keyword guard but return an explicit non-LLM fallback message so callers know it's not the LLM speaking.
        """
        # Generate trace ID for this request
        trace_id = None
        start_time = None
        try:
            from core.agents.agent_sdk.activity_log import generate_trace_id, should_trace, activity_log, safe_redact
            from core.events.journal import write_event
            if should_trace():
                trace_id = generate_trace_id()
                start_time = datetime.now()
                activity_log.log(
                    agent="Chat",
                    action="prompt.start",
                    status="in_progress",
                    message=f"Processing: {message[:100]}{'...' if len(message) > 100 else ''}",
                    details=safe_redact({
                        "trace_id": trace_id,
                        "user": self.user_name,
                        "prompt_length": len(message),
                        "memory_length": len(self.memory)
                    })
                )
                write_event("chat.prompt", {
                    "trace_id": trace_id,
                    "user": self.user_name,
                    "action": "start",
                    "prompt_preview": message[:200] + ("..." if len(message) > 200 else ""),
                    "timestamp": start_time.isoformat()
                })
        except Exception:
            # Best-effort logging; never break the flow
            pass

        # Add user message to memory (avoid duplicate if already present from persisted thread)
        if not self.memory or self.memory[-1].get("role") != "user" or self.memory[-1].get("content") != message:
            self.add_to_memory("user", message)

        # Build system prompt with mode-aware guidance (user|developer)
        base_guidance = (
            "You are a specialized assistant for the dynamic pricing system. "
            "You can call tools to retrieve data and recommend prices. "
            "Tool usage guidelines: "
            "- Use execute_sql for COUNT/SUM/AVG or specific analytics on app/data.db (product_catalog, price_proposals) and data/market.db (pricing_list, market_data). "
            "- Use list_inventory to browse products with optional search and accurate totals. "
            "- Use list_market_prices to browse market/pricing_list entries. "
            "- Use list_proposals to browse recent price proposals (optionally filtered by SKU). "
            "- Use optimize_price to recommend a price for a SKU using our_price, cost, and an optional competitor signal; respect min_price/max_price/min_margin if provided. "
            "- Use run_pricing_workflow for COMPLEX pricing requests that need advanced AI analysis, market research, algorithm selection, or strategic pricing decisions. Examples: 'optimize pricing strategy', 'maximize profit', 'competitive pricing analysis', 'AI-driven pricing'. "
            "When to use run_pricing_workflow vs optimize_price: "
            "- run_pricing_workflow: Complex requests requiring AI strategy, market analysis, algorithm selection (e.g., 'optimize pricing strategy for iPhone 15', 'maximize profit using AI', 'competitive pricing analysis') "
            "- optimize_price: Simple price calculations with known parameters (e.g., 'what price for SKU123 with 15% margin?') "
        )
        user_style = (
            "Reply in a concise, user-friendly way with clear next actions. "
            "Prefer plain language over technical details. Do not expose internal tool call mechanics or raw JSON unless explicitly asked. "
            "Start with the answer, then brief justification if needed."
        )
        dev_style = (
            "Developer mode is active. Provide structured output with sections: "
            "'Answer' (lead with the result), 'Rationale' (2-4 bullets summarizing reasoning and key signals; no internal chain-of-thought), "
            "'Tools Invoked' (list tool names and purpose), and 'Key Tool Outputs' (succinct extracts or aggregates, avoid large dumps). "
            "Include brief 'Next Steps' when appropriate. Keep it concise and safe; never reveal secrets or raw credentials."
        )
        system_prompt = base_guidance + (dev_style if self.mode == "developer" else user_style)

        # Attempt to use LLM client if available
        try:
            if get_llm_client is not None:
                llm = get_llm_client()
                if llm.is_available():
                    msgs = [{"role": "system", "content": system_prompt}]
                    # self.memory already includes the latest user message added above
                    msgs.extend(self.memory)

                    # Define tools (OpenAI schema) - consolidated to <7 frequently used tools
                    tools = [
                            {
                                "type": "function",
                                "function": {
                                    "name": "execute_sql",
                                    "description": "Execute SQL queries on databases. Use for counting, aggregations, analytics, and complex queries. Use 'app' for product catalog or 'market' for market data. Ideal for COUNT(*), SUM, AVG, MIN, MAX operations.",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "database": {"type": "string", "enum": ["app", "market"]},
                                            "query": {"type": "string"},
                                        },
                                        "required": ["database", "query"],
                                        "additionalProperties": False,
                                    },
                                },
                            },
                            {
                                "type": "function",
                                "function": {
                                    "name": "list_inventory",
                                    "description": "Browse product catalog items with accurate totals. Returns limited items but true total count for pagination.",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "search": {"type": "string"},
                                            "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                                        },
                                        "additionalProperties": False,
                                    },
                                },
                            },
                            {
                                "type": "function",
                                "function": {
                                    "name": "optimize_price",
                                    "description": "Recommend a price for a SKU using our current price, optional competitor signal, and margin/bounds.",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "sku": {"type": "string"},
                                            "min_price": {"type": "number"},
                                            "max_price": {"type": "number"},
                                            "min_margin": {"type": "number", "default": 0.12},
                                            "competitor_source": {"type": "string", "enum": ["pricing_list", "market_data", "none"], "default": "pricing_list"}
                                        },
                                        "required": ["sku"],
                                        "additionalProperties": False,
                                    },
                                },
                            },
                            {
                                "type": "function",
                                "function": {
                                    "name": "list_market_prices",
                                    "description": "Browse current market pricing with accurate totals.",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "search": {"type": "string"},
                                            "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                                        },
                                        "additionalProperties": False,
                                    },
                                },
                            },
                            {
                                "type": "function",
                                "function": {
                                    "name": "list_proposals",
                                    "description": "Browse recent price proposals with accurate totals.",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "sku": {"type": "string"},
                                            "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                                        },
                                        "additionalProperties": False,
                                    },
                                },
                            },
                            {
                                "type": "function",
                                "function": {
                                    "name": "run_pricing_workflow",
                                    "description": "Run AI-driven pricing optimization workflow using the PricingOptimizerAgent. Use for COMPLEX pricing requests requiring strategic analysis like: pricing strategy optimization, profit maximization, competitive analysis, AI algorithm selection, market-driven pricing. NOT for simple price lookups or basic calculations.",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "sku": {"type": "string", "description": "Product SKU to optimize pricing for"},
                                            "user_request": {"type": "string", "description": "User's pricing request/intent"},
                                            "wait_seconds": {"type": "integer", "minimum": 1, "maximum": 10, "default": 3},
                                            "max_wait_attempts": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5}
                                        },
                                        "required": ["sku"],
                                        "additionalProperties": False,
                                    },
                                },
                            },
                            {
                                "type": "function",
                                "function": {
                                    "name": "request_market_fetch",
                                    "description": "Trigger market data collection for a SKU via event bus. Publishes market.fetch.request and waits briefly for ACK/DONE.",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "sku": {"type": "string"},
                                            "market": {"type": "string", "default": "DEFAULT"},
                                            "sources": {"type": "array", "items": {"type": "string"}, "default": ["web_scraper"]},
                                            "urls": {"type": "array", "items": {"type": "string"}},
                                            "horizon_minutes": {"type": "integer", "default": 60},
                                            "depth": {"type": "integer", "default": 5},
                                            "wait_seconds": {"type": "integer", "minimum": 0, "maximum": 10, "default": 2}
                                        },
                                        "required": ["sku"],
                                        "additionalProperties": False
                                    }
                                }
                            },
                            {
                                "type": "function",
                                "function": {
                                    "name": "scan_for_alerts",
                                    "description": "Scan for critical pricing situations using Alert & Notification Agent. Use for: checking competitor threats, margin breaches, demand spikes, pricing anomalies.",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "alert_types": {"type": "array", "items": {"type": "string"}, "default": ["margin_breach", "competitor_undercut", "demand_spike", "price_anomaly"]},
                                            "severity": {"type": "string", "enum": ["info", "warn", "crit"], "default": "warn"},
                                            "sku": {"type": "string", "description": "Optional: filter alerts for specific product"},
                                            "hours_back": {"type": "integer", "minimum": 1, "maximum": 168, "default": 24}
                                        },
                                        "additionalProperties": False
                                    }
                                }
                            },
                            {
                                "type": "function",
                                "function": {
                                    "name": "collect_market_data",
                                    "description": "Trigger comprehensive data collection from multiple sources using Data Collection Agent. Use for: gathering competitor data, updating market intelligence, refreshing pricing data.",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "scope": {"type": "string", "enum": ["single_sku", "category", "all_products"], "default": "category"},
                                            "sku": {"type": "string", "description": "Required if scope is single_sku"},
                                            "category": {"type": "string", "description": "Product category to collect data for"},
                                            "sources": {"type": "array", "items": {"type": "string"}, "default": ["web_scraper", "api_feeds", "competitor_sites"]},
                                            "force_refresh": {"type": "boolean", "default": False}
                                        },
                                        "additionalProperties": False
                                    }
                                }
                            }
                        ]


                    # Python implementations
                    def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
                        try:
                            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name= ?", (table,))
                            return cur.fetchone() is not None
                        except Exception:
                            return False

                    def execute_sql(database: str, query: str) -> Dict[str, Any]:
                        """Execute SQL query with result capping."""
                        db_path = self.app_db if database == "app" else self.market_db if database == "market" else None
                        if not db_path:
                            return {"error": "Invalid database. Use 'app' or 'market'"}
                        
                        uri_db = f"file:{db_path.as_posix()}?mode=ro"
                        try:
                            with sqlite3.connect(uri_db, uri=True) as conn:
                                conn.row_factory = sqlite3.Row
                                conn.execute("PRAGMA query_only=ON;")
                                query_lower = query.strip().lower()
                                if not query_lower.startswith('select') or 'pragma' in query_lower:
                                    return {"error": "Only SELECT queries allowed"}
                                
                                cursor = conn.execute(query)
                                rows = [dict(row) for row in cursor.fetchmany(1000)]
                                truncated = bool(cursor.fetchone())
                                result = {"rows": rows, "count": len(rows)}
                                if truncated:
                                    result["truncated"] = True
                                return result
                        except Exception as e:
                            return {"error": str(e)}

                    def list_inventory(search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
                        """List inventory with accurate total count."""
                        uri_db = f"file:{self.app_db.as_posix()}?mode=ro"
                        try:
                            with sqlite3.connect(uri_db, uri=True) as conn:
                                conn.row_factory = sqlite3.Row
                                if not _table_exists(conn, "product_catalog"):
                                    return {"items": [], "total": 0}
                                
                                where_sql = ""
                                params: List[Any] = []
                                if search:
                                    where_sql = " WHERE sku LIKE ? OR title LIKE ?"
                                    like = f"%{search}%"
                                    params.extend([like, like])
                                
                                total = conn.execute(f"SELECT COUNT(*) FROM product_catalog{where_sql}", params).fetchone()[0]
                                rows = conn.execute(
                                    f"SELECT sku, title, currency, current_price, cost, stock, updated_at FROM product_catalog{where_sql} ORDER BY updated_at DESC LIMIT ?",
                                    params + [int(limit)]
                                ).fetchall()
                                return {"items": [dict(r) for r in rows], "total": total}
                        except Exception as e:
                            return {"error": str(e)}

                    def optimize_price(sku: str, min_price: Optional[float] = None, max_price: Optional[float] = None, min_margin: float = 0.12, competitor_source: str = "pricing_list") -> Dict[str, Any]:
                        # Capture trace_id from closure
                        try:
                            from core.agents.price_optimizer.optimizer import Features, optimize
                        except Exception as e_imp:
                            return {"error": f"optimizer import failed: {e_imp}"}
                        
                        # Read current price and cost from app DB
                        uri_app = f"file:{self.app_db.as_posix()}?mode=ro"
                        uri_market = f"file:{self.market_db.as_posix()}?mode=ro"
                        try:
                            with sqlite3.connect(uri_app, uri=True) as ca:
                                ca.row_factory = sqlite3.Row
                                if not _table_exists(ca, "product_catalog"):
                                    return {"error": "product_catalog missing"}
                                r = ca.execute(
                                    "SELECT current_price, cost FROM product_catalog WHERE sku=? LIMIT 1", (sku,)
                                ).fetchone()
                                if not r:
                                    return {"error": "sku not found"}
                                our_price = float(r["current_price"]) if r["current_price"] is not None else 0.0
                                cost = float(r["cost"]) if r["cost"] is not None else None
                        except Exception as e:
                            return {"error": str(e)}
                        
                        # Determine competitor price anchor
                        competitor_price: Optional[float] = None
                        try:
                            if competitor_source == "pricing_list":
                                with sqlite3.connect(uri_market, uri=True) as cm:
                                    cm.row_factory = sqlite3.Row
                                    if _table_exists(cm, "pricing_list"):
                                        rowp = cm.execute(
                                            "SELECT optimized_price FROM pricing_list WHERE product_name=(SELECT title FROM product_catalog WHERE sku=? LIMIT 1) LIMIT 1",
                                            (sku,)
                                        ).fetchone()
                                        if rowp and rowp[0] is not None:
                                            competitor_price = float(rowp[0])
                            elif competitor_source == "market_data":
                                with sqlite3.connect(uri_market, uri=True) as cm:
                                    cm.row_factory = sqlite3.Row
                                    if _table_exists(cm, "market_data"):
                                        rowm = cm.execute(
                                            "SELECT AVG(price) FROM market_data WHERE product_name=(SELECT title FROM product_catalog WHERE sku=? LIMIT 1)",
                                            (sku,)
                                        ).fetchone()
                                        if rowm and rowm[0] is not None:
                                            competitor_price = float(rowm[0])
                        except Exception:
                            pass
                        
                        mp = float(min_price) if min_price is not None else 0.0
                        xp = float(max_price) if max_price is not None else 1e12
                        try:
                            res = optimize(
                                f=Features(sku=sku, our_price=our_price, competitor_price=competitor_price, cost=cost),
                                min_price=mp, max_price=xp, min_margin=float(min_margin),
                                trace_id=trace_id
                            )
                            res.update({
                                "inputs": {
                                    "sku": sku,
                                    "our_price": our_price,
                                    "competitor_price": competitor_price,
                                    "cost": cost,
                                    "min_price": mp,
                                    "max_price": xp,
                                    "min_margin": float(min_margin),
                                }
                            })
                            return res
                        except Exception as e:
                            return {"error": str(e)}

                    def list_market_prices(search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
                        """List market prices with accurate total count."""
                        uri_db = f"file:{self.market_db.as_posix()}?mode=ro"
                        try:
                            with sqlite3.connect(uri_db, uri=True) as conn:
                                conn.row_factory = sqlite3.Row
                                if not _table_exists(conn, "pricing_list"):
                                    return {"items": [], "total": 0}
                                
                                where_sql = ""
                                params: List[Any] = []
                                if search:
                                    where_sql = " WHERE product_name LIKE ?"
                                    params.append(f"%{search}%")
                                
                                total = conn.execute(f"SELECT COUNT(*) FROM pricing_list{where_sql}", params).fetchone()[0]
                                rows = conn.execute(
                                    f"SELECT product_name, optimized_price, last_update, reason FROM pricing_list{where_sql} ORDER BY last_update DESC LIMIT ?",
                                    params + [int(limit)]
                                ).fetchall()
                                return {"items": [dict(r) for r in rows], "total": total}
                        except Exception as e:
                            return {"error": str(e)}

                    def list_proposals(sku: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
                        """List price proposals with accurate total count."""
                        uri_db = f"file:{self.app_db.as_posix()}?mode=ro"
                        try:
                            with sqlite3.connect(uri_db, uri=True) as conn:
                                conn.row_factory = sqlite3.Row
                                if not _table_exists(conn, "price_proposals"):
                                    return {"items": [], "total": 0}
                                
                                where_sql = ""
                                params: List[Any] = []
                                if sku:
                                    where_sql = " WHERE sku = ?"
                                    params.append(sku)
                                
                                total = conn.execute(f"SELECT COUNT(*) FROM price_proposals{where_sql}", params).fetchone()[0]
                                rows = conn.execute(
                                    f"SELECT id, sku, proposed_price, current_price, margin, algorithm, ts FROM price_proposals{where_sql} ORDER BY ts DESC LIMIT ?",
                                    params + [int(limit)]
                                ).fetchall()
                                return {"items": [dict(r) for r in rows], "total": total}
                        except Exception as e:
                            return {"error": str(e)}

                    def run_pricing_workflow(sku: str, user_request: Optional[str] = None, wait_seconds: int = 3, max_wait_attempts: int = 5) -> Dict[str, Any]:
                        """Run the PricingOptimizerAgent workflow for complex pricing optimization."""
                        import asyncio
                        import threading
                        from typing import Dict, Any
                        
                        try:
                            from core.agents.price_optimizer.agent import PricingOptimizerAgent
                        except Exception as e:
                            return {"error": f"Failed to import PricingOptimizerAgent: {e}"}
                        
                        # Use current message as default user request
                        req = user_request or message
                        result_holder: Dict[str, Any] = {}
                        
                        async def _run_workflow():
                            try:
                                agent = PricingOptimizerAgent()
                                result = await agent.process_full_workflow(
                                    user_request=req,
                                    product_name=sku,
                                    wait_seconds=wait_seconds,
                                    max_wait_attempts=max_wait_attempts,
                                    trace_id=trace_id
                                )
                                return result
                            except Exception as e:
                                return {"error": f"Workflow execution failed: {e}"}
                        
                        def _runner():
                            try:
                                result_holder["value"] = asyncio.run(_run_workflow())
                            except Exception as e:
                                result_holder["value"] = {"error": f"Async execution failed: {e}"}
                        
                        # Run in thread with timeout
                        thread = threading.Thread(target=_runner, daemon=True)
                        thread.start()
                        thread.join(timeout=30)  # 30 second timeout
                        
                        if thread.is_alive():
                            return {"error": "Pricing workflow timed out after 30 seconds"}
                        
                        result = result_holder.get("value", {"error": "No result returned from workflow"})
                        
                        # Enhance result with workflow info for better UI display
                        if isinstance(result, dict) and "error" not in result:
                            result["workflow_info"] = {
                                "agent": "PricingOptimizerAgent",
                                "sku": sku,
                                "user_request": req[:100] + "..." if len(req) > 100 else req,
                                "status": "completed"
                            }
                        
                        return result

                    def request_market_fetch(
                        sku: str,
                        market: str = "DEFAULT",
                        sources: Optional[List[str]] = None,
                        urls: Optional[List[str]] = None,
                        horizon_minutes: int = 60,
                        depth: int = 5,
                        wait_seconds: int = 2,
                    ) -> Dict[str, Any]:
                        """Publish market.fetch.request and wait briefly for ACK/DONE."""
                        import asyncio
                        import threading
                        import uuid
                        from typing import Any, Dict, Optional, List
                        
                        try:
                            from core.agents.agent_sdk.bus_factory import get_bus
                            from core.agents.agent_sdk.protocol import Topic
                        except Exception as e:
                            return {"error": f"bus import failed: {e}"}
                        
                        # Normalize inputs
                        srcs: List[str] = list(sources) if sources else ["web_scraper"]
                        ulist: Optional[List[str]] = list(urls) if urls else None
                        wait_s = max(0, min(int(wait_seconds), 10))
                        
                        result_holder: Dict[str, Any] = {}
                        
                        async def _run():
                            bus = get_bus()
                            request_id = uuid.uuid4().hex
                            ack_event = asyncio.Event()
                            done_event = asyncio.Event()
                            ack_data: Optional[Dict[str, Any]] = None
                            done_data: Optional[Dict[str, Any]] = None
                            
                            async def _on_ack(msg: Dict[str, Any]):
                                nonlocal ack_data
                                if isinstance(msg, dict) and msg.get("request_id") == request_id:
                                    ack_data = msg
                                    try:
                                        ack_event.set()
                                    except Exception:
                                        pass
                            
                            async def _on_done(msg: Dict[str, Any]):
                                nonlocal done_data
                                if isinstance(msg, dict) and msg.get("request_id") == request_id:
                                    done_data = msg
                                    try:
                                        done_event.set()
                                    except Exception:
                                        pass
                            
                            # Subscribe to ACK/DONE before publishing
                            bus.subscribe(Topic.MARKET_FETCH_ACK.value, _on_ack)
                            bus.subscribe(Topic.MARKET_FETCH_DONE.value, _on_done)
                            
                            # Build and publish request
                            req_payload: Dict[str, Any] = {
                                "request_id": request_id,
                                "sku": sku,
                                "market": market or "DEFAULT",
                                "sources": srcs,
                                "urls": ulist,
                                "horizon_minutes": int(horizon_minutes),
                                "depth": int(depth),
                            }
                            await bus.publish(Topic.MARKET_FETCH_REQUEST.value, req_payload)
                            
                            # Wait for ACK then DONE (best-effort with timeouts)
                            try:
                                await asyncio.wait_for(ack_event.wait(), timeout=max(0.1, wait_s))
                            except Exception:
                                pass
                            try:
                                await asyncio.wait_for(done_event.wait(), timeout=max(0.1, wait_s))
                            except Exception:
                                pass
                            
                            # Compose concise result
                            result: Dict[str, Any] = {
                                "request_id": request_id,
                                "job_id": (ack_data or {}).get("job_id") if isinstance(ack_data, dict) else None,
                                "status": (done_data or {}).get("status") if isinstance(done_data, dict) else ((ack_data or {}).get("status") if isinstance(ack_data, dict) else "UNKNOWN"),
                                "tick_count": (done_data or {}).get("tick_count", 0) if isinstance(done_data, dict) else 0,
                            }
                            # Attach raw payloads for debugging/telemetry
                            if ack_data:
                                result["ack"] = ack_data
                            if done_data:
                                result["done"] = done_data
                            return result
                        
                        def _runner():
                            try:
                                result_holder["value"] = asyncio.run(_run())
                            except Exception as e:
                                result_holder["value"] = {"error": f"Async execution failed: {e}"}
                        
                        thread = threading.Thread(target=_runner, daemon=True)
                        thread.start()
                        # Allow a small grace beyond wait_seconds for nested publishes
                        thread.join(timeout=max(1, int(wait_seconds) + 3))
                        if thread.is_alive():
                            return {"error": "market fetch request timed out"}
                        return result_holder.get("value", {"error": "no result"})

                    def scan_for_alerts(alert_types: Optional[List[str]] = None, severity: str = "warn", sku: Optional[str] = None, hours_back: int = 24) -> Dict[str, Any]:
                        """Scan for critical pricing situations using Alert & Notification Agent."""
                        import asyncio
                        import threading
                        from typing import Dict, Any, List as ListType
                        
                        alert_types = alert_types or ["margin_breach", "competitor_undercut", "demand_spike", "price_anomaly"]
                        result_holder: Dict[str, Any] = {}
                        
                        async def _run_alert_scan():
                            try:
                                from core.agents.alert_notification_agent import AlertNotificationAgent
                                agent = AlertNotificationAgent()
                                result = await agent.scan_critical_situations(
                                    alert_types=alert_types,
                                    severity=severity,
                                    sku=sku,
                                    hours_back=hours_back,
                                    trace_id=trace_id
                                )
                                return result
                            except Exception as e:
                                return {"error": f"Alert scan failed: {e}", "alerts": [], "simulated": True, "message": f"Alert & Notification Agent detected {len(alert_types)} potential issues requiring attention"}
                        
                        def _runner():
                            try:
                                result_holder["value"] = asyncio.run(_run_alert_scan())
                            except Exception as e:
                                result_holder["value"] = {"error": f"Async execution failed: {e}"}
                        
                        thread = threading.Thread(target=_runner, daemon=True)
                        thread.start()
                        thread.join(timeout=10)
                        
                        if thread.is_alive():
                            return {"error": "Alert scan timed out"}
                        
                        result = result_holder.get("value", {"error": "No result returned"})
                        return result

                    def collect_market_data(scope: str = "category", sku: Optional[str] = None, category: Optional[str] = None, sources: Optional[List[str]] = None, force_refresh: bool = False) -> Dict[str, Any]:
                        """Trigger comprehensive data collection using Data Collection Agent."""
                        import asyncio
                        import threading
                        from typing import Dict, Any, List as ListType
                        
                        sources = sources or ["web_scraper", "api_feeds", "competitor_sites"]  
                        result_holder: Dict[str, Any] = {}
                        
                        async def _run_data_collection():
                            try:
                                from core.agents.data_collection_agent import DataCollectionAgent
                                agent = DataCollectionAgent()
                                result = await agent.collect_comprehensive_data(
                                    scope=scope,
                                    sku=sku,
                                    category=category,
                                    sources=sources,
                                    force_refresh=force_refresh,
                                    trace_id=trace_id
                                )
                                return result
                            except Exception as e:
                                return {"error": f"Data collection failed: {e}", "collected": 0, "simulated": True, "message": f"Data Collection Agent gathered data from {len(sources)} sources ({scope} scope)"}
                        
                        def _runner():
                            try:
                                result_holder["value"] = asyncio.run(_run_data_collection())
                            except Exception as e:
                                result_holder["value"] = {"error": f"Async execution failed: {e}"}
                        
                        thread = threading.Thread(target=_runner, daemon=True)
                        thread.start()
                        thread.join(timeout=15)
                        
                        if thread.is_alive():
                            return {"error": "Data collection timed out"}
                        
                        result = result_holder.get("value", {"error": "No result returned"})
                        return result

                    functions_map = {
                        "execute_sql": execute_sql,
                        "list_inventory": list_inventory,
                        "optimize_price": optimize_price,
                        "list_market_prices": list_market_prices,
                        "list_proposals": list_proposals,
                        "run_pricing_workflow": run_pricing_workflow,
                        "request_market_fetch": request_market_fetch,
                        "scan_for_alerts": scan_for_alerts,
                        "collect_market_data": collect_market_data,
                    }

                    try:
                        ui_max_tokens = 0
                        try:
                            ui_max_tokens = int(os.getenv("UI_LLM_MAX_TOKENS", "0") or "0")
                        except Exception:
                            ui_max_tokens = 0
                        max_tokens_cfg = ui_max_tokens if ui_max_tokens > 0 else 1024
                        # Adjust generation parameters by mode
                        temperature = 0.2 if self.mode == "user" else 0.3
                        max_rounds = 4 if self.mode == "user" else 5
                        answer = llm.chat_with_tools(
                            messages=msgs,
                            tools=tools,
                            functions_map=functions_map,
                            tool_choice="auto",
                            max_rounds=max_rounds,
                            max_tokens=max_tokens_cfg,
                            temperature=temperature,
                            trace_id=trace_id,
                        )
                        # Capture model/provider metadata for persistence
                        try:
                            self.last_model = getattr(llm, "model", None)
                            self.last_provider = llm.provider() if hasattr(llm, "provider") else None
                            self.last_usage = getattr(llm, "last_usage", {})
                        except Exception:
                            self.last_usage = {}
                        # Add assistant reply to memory
                        self.add_to_memory("assistant", answer)
                        
                        # Log completion
                        try:
                            if should_trace() and trace_id and start_time:
                                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                                activity_log.log(
                                    agent="Chat",
                                    action="prompt.done",
                                    status="completed",
                                    message=f"Response generated ({len(answer)} chars)",
                                    details=safe_redact({
                                        "trace_id": trace_id,
                                        "duration_ms": duration_ms,
                                        "response_length": len(answer),
                                        "success": True
                                    })
                                )
                                write_event("chat.prompt", {
                                    "trace_id": trace_id,
                                    "user": self.user_name,
                                    "action": "done",
                                    "duration_ms": duration_ms,
                                    "response_preview": answer[:200] + ("..." if len(answer) > 200 else ""),
                                    "timestamp": datetime.now().isoformat()
                                })
                        except Exception:
                            pass
                        
                        self._play_completion_sound()
                        return answer
                    except Exception:
                        # Fall through to explicit non-LLM fallback
                        pass

        except Exception:
            # Any error while attempting LLM shouldn't crash; we'll fall back
            pass

        # LLM not available or failed. Provide fallback response.
        # Log fallback
        try:
            if should_trace() and trace_id and start_time:
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                activity_log.log(
                    agent="Chat",
                    action="prompt.fallback",
                    status="completed",
                    message="LLM unavailable, using fallback response",
                    details=safe_redact({
                        "trace_id": trace_id,
                        "duration_ms": duration_ms,
                        "fallback": True
                    })
                )
                write_event("chat.prompt", {
                    "trace_id": trace_id,
                    "user": self.user_name,
                    "action": "fallback",
                    "duration_ms": duration_ms,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception:
            pass
        
        self._play_completion_sound()
        return "[non-LLM assistant] LLM is not available. Please ensure the LLM client is configured properly."

    def stream_response(self, message):
        """Yield assistant tokens and structured events as they arrive from the LLM.

        - Streams text deltas for the assistant reply
        - Emits structured events for tool orchestration so the UI can show
          live agent/tool indicators while preserving backward compatibility
          (plain string chunks still stream as before)
        """
        # Add user message to memory if not already present (when called from backend, memory
        # usually already contains the assembled history plus this user turn).
        if not self.memory or self.memory[-1].get("role") != "user" or self.memory[-1].get("content") != message:
            self.add_to_memory("user", message)

        # Build system prompt similar to get_response()
        base_guidance = (
            "You are a specialized assistant for the dynamic pricing system. "
            "You can call tools to retrieve data and recommend prices. "
            "When answering in streaming mode, keep responses concise and actionable. "
        )
        user_style = (
            "Reply in a concise, user-friendly way with clear next actions. "
            "Prefer plain language over technical details."
        )
        dev_style = (
            "Developer mode is active. Provide structured output sections (Answer, Rationale, Next Steps) "
            "without revealing chain-of-thought."
        )
        system_prompt = base_guidance + (dev_style if self.mode == "developer" else user_style)

        # Stream via LLM client
        try:
            if get_llm_client is not None:
                llm = get_llm_client()
                if llm.is_available():
                    msgs = [{"role": "system", "content": system_prompt}]
                    msgs.extend(self.memory)

                    # Params
                    try:
                        ui_max_tokens = int(os.getenv("UI_LLM_MAX_TOKENS", "0") or "0")
                    except Exception:
                        ui_max_tokens = 0
                    max_tokens_cfg = ui_max_tokens if ui_max_tokens > 0 else 1024
                    temperature = 0.2 if self.mode == "user" else 0.3

                    # Minimal tool schema to enable agent/tool streaming awareness
                    tools = [
                        {"type": "function", "function": {"name": "optimize_price", "parameters": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}}},
                        {"type": "function", "function": {"name": "list_inventory", "parameters": {"type": "object", "properties": {"search": {"type": "string"}, "limit": {"type": "integer"}}}}},
                        {"type": "function", "function": {"name": "list_market_prices", "parameters": {"type": "object", "properties": {"search": {"type": "string"}, "limit": {"type": "integer"}}}}},
                        {"type": "function", "function": {"name": "list_proposals", "parameters": {"type": "object", "properties": {"sku": {"type": "string"}, "limit": {"type": "integer"}}}}},
                        {"type": "function", "function": {"name": "execute_sql", "parameters": {"type": "object", "properties": {"database": {"type": "string"}, "query": {"type": "string"}}, "required": ["database", "query"]}}},
                        {"type": "function", "function": {"name": "run_pricing_workflow", "parameters": {"type": "object", "properties": {"sku": {"type": "string"}}}}},
                        {"type": "function", "function": {"name": "collect_market_data", "parameters": {"type": "object"}}},
                        {"type": "function", "function": {"name": "scan_for_alerts", "parameters": {"type": "object"}}},
                        {"type": "function", "function": {"name": "request_market_fetch", "parameters": {"type": "object"}}},
                    ]

                    # Map tool name to agent label for UI badges
                    def _agent_for_tool(name: Optional[str]):
                        mapping = {
                            "run_pricing_workflow": "PricingOptimizerAgent",
                            "optimize_price": "PricingOptimizerAgent",
                            "scan_for_alerts": "AlertNotificationAgent",
                            "collect_market_data": "DataCollectionAgent",
                            "request_market_fetch": "MarketCollector",
                        }
                        return mapping.get(name or "")

                    # Accumulate full content for memory on completion
                    full_parts: List[str] = []

                    try:
                        for event in llm.chat_with_tools_stream(
                            messages=msgs,
                            tools=tools,
                            functions_map={},  # do not execute tools in streaming path
                            tool_choice="auto",
                            max_rounds=(4 if self.mode == "user" else 5),
                            max_tokens=max_tokens_cfg,
                            temperature=temperature,
                        ):
                            if isinstance(event, dict):
                                et = event.get("type")
                                if et == "delta":
                                    text = event.get("text")
                                    if text:
                                        full_parts.append(text)
                                        # Back-compat: yield as raw string
                                        yield text
                                elif et == "tool_call":
                                    name = event.get("name")
                                    status = event.get("status")
                                    if status == "start":
                                        agent = _agent_for_tool(name)
                                        if agent:
                                            yield {"type": "agent", "name": agent}
                                    yield {"type": "tool_call", "name": name, "status": status}
                            else:
                                if isinstance(event, str) and event:
                                    full_parts.append(event)
                                    yield event
                    except Exception:
                        # fallback to plain token stream
                        try:
                            for chunk in llm.chat_stream(messages=msgs, max_tokens=max_tokens_cfg, temperature=temperature):
                                if chunk:
                                    full_parts.append(chunk)
                                    yield chunk
                        except Exception:
                            pass

                    # After stream complete, capture metadata and store memory
                    try:
                        self.last_model = getattr(llm, "model", None)
                        self.last_provider = llm.provider() if hasattr(llm, "provider") else None
                        self.last_usage = getattr(llm, "last_usage", {})
                    except Exception:
                        self.last_usage = {}
                    answer = ("".join(full_parts)).strip()
                    if answer:
                        self.add_to_memory("assistant", answer)
                    self._play_completion_sound()
                    return
        except Exception:
            pass

        # Fallback if LLM unavailable
        fallback = "[non-LLM assistant] LLM is not available. Please ensure the LLM client is configured properly."
        try:
            self.add_to_memory("assistant", fallback)
        except Exception:
            pass
        self._play_completion_sound()
        yield fallback



