import os
import sqlite3
from pathlib import Path
import requests
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
    from app.llm_client import get_llm_client
except Exception:
    get_llm_client = None

class UserInteractionAgent:
    def __init__(self, user_name):
        self.user_name = user_name
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

        # Build system prompt focused on dynamic pricing
        system_prompt = (
            "You are a specialized assistant for the dynamic pricing system. "
            "You can call tools to retrieve data and recommend prices. "
            "Tool usage guidelines: "
            "- Use execute_sql for COUNT/SUM/AVG or specific analytics on app/data.db (product_catalog, price_proposals) and data/market.db (pricing_list, market_data). "
            "- Use list_inventory to browse products with optional search and accurate totals. "
            "- Use list_market_prices to browse market/pricing_list entries. "
            "- Use list_proposals to browse recent price proposals (optionally filtered by SKU). "
            "- Use optimize_price to recommend a price for a SKU using our_price, cost, and an optional competitor signal; respect min_price/max_price/min_margin if provided. "
            "Prefer tools over guessing; respond with concise, direct answers."
        )

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
                    ]

                    # Python implementations
                    def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
                        try:
                            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
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

                    functions_map = {
                        "execute_sql": execute_sql,
                        "list_inventory": list_inventory,
                        "optimize_price": optimize_price,
                        "list_market_prices": list_market_prices,
                        "list_proposals": list_proposals,
                    }

                    try:
                        ui_max_tokens = 0
                        try:
                            ui_max_tokens = int(os.getenv("UI_LLM_MAX_TOKENS", "0") or "0")
                        except Exception:
                            ui_max_tokens = 0
                        max_tokens_cfg = ui_max_tokens if ui_max_tokens > 0 else 1024
                        answer = llm.chat_with_tools(
                            messages=msgs,
                            tools=tools,
                            functions_map=functions_map,
                            tool_choice="auto",
                            max_rounds=4,
                            max_tokens=max_tokens_cfg,
                            temperature=0.2,
                            trace_id=trace_id,
                        )
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



