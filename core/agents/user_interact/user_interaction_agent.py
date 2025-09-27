import os
import sqlite3
from pathlib import Path
import requests
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
        # Add user message to memory
        self.add_to_memory("user", message)

        # Build system prompt focused on dynamic pricing
        system_prompt = (
            f"You are a specialized assistant for the dynamic pricing system. "
            f"You have access to SQL tools to query the databases directly. "
            f"Use the execute_sql tool to run SQL queries on the product catalog (app/data.db) "
            f"and market data (data/market.db) to answer questions about pricing, inventory, "
            f"competitors, trends, and other dynamic pricing related topics."
        )

        # Attempt to use LLM client if available
        try:
            if get_llm_client is not None:
                llm = get_llm_client()
                if llm.is_available():
                    msgs = [{"role": "system", "content": system_prompt}]
                    # self.memory already includes the latest user message added above
                    msgs.extend(self.memory)

                    # Define tools (OpenAI schema)
                    tools = [
                        {
                            "type": "function",
                            "function": {
                                "name": "execute_sql",
                                "description": "Execute SQL queries on the databases. Use 'app' for product catalog queries (app/data.db) or 'market' for market data queries (data/market.db).",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "database": {"type": "string", "enum": ["app", "market"], "description": "Which database to query: 'app' for product catalog, 'market' for market data"},
                                        "query": {"type": "string", "description": "SQL query to execute"},
                                    },
                                    "required": ["database", "query"],
                                    "additionalProperties": False,
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_inventory_items",
                                "description": "List items from the local product catalog (app/data.db). Use for inventory overviews.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "search": {"type": "string", "description": "Filter by substring in SKU or title."},
                                        "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                                    },
                                    "additionalProperties": False,
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "get_inventory_item",
                                "description": "Get a single inventory item by SKU from app/data.db/product_catalog.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "sku": {"type": "string", "description": "Item SKU (exact match)"},
                                    },
                                    "required": ["sku"],
                                    "additionalProperties": False,
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_pricing_list",
                                "description": "List current market pricing entries from market.db/pricing_list.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "search": {"type": "string", "description": "Filter by substring in product_name."},
                                        "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                                    },
                                    "additionalProperties": False,
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_price_proposals",
                                "description": "List recent price proposals from app/data.db/price_proposals.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "sku": {"type": "string", "description": "Optional filter by SKU"},
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
                        """Execute SQL query on specified database."""
                        if database == "app":
                            db_path = self.app_db
                        elif database == "market":
                            db_path = self.market_db
                        else:
                            return {"error": "Invalid database. Use 'app' or 'market'"}
                        
                        uri_db = f"file:{db_path.as_posix()}?mode=ro"
                        try:
                            with sqlite3.connect(uri_db, uri=True) as conn:
                                conn.row_factory = sqlite3.Row
                                # Only allow SELECT queries for safety
                                query_lower = query.strip().lower()
                                if not query_lower.startswith('select'):
                                    return {"error": "Only SELECT queries are allowed"}
                                
                                cursor = conn.execute(query)
                                rows = [dict(row) for row in cursor.fetchall()]
                                return {"rows": rows, "count": len(rows)}
                        except Exception as e:
                            return {"error": str(e)}

                    def list_inventory_items(search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
                        uri_db = f"file:{self.app_db.as_posix()}?mode=ro"
                        try:
                            with sqlite3.connect(uri_db, uri=True) as conn:
                                conn.row_factory = sqlite3.Row
                                if not _table_exists(conn, "product_catalog"):
                                    return {"items": [], "total": 0, "note": "product_catalog missing"}
                                q = "SELECT sku, title, currency, current_price, cost, stock, updated_at FROM product_catalog"
                                params: List[Any] = []
                                if search:
                                    q += " WHERE sku LIKE ? OR title LIKE ?"
                                    like = f"%{search}%"
                                    params.extend([like, like])
                                q += " ORDER BY updated_at DESC LIMIT ?"
                                params.append(int(limit))
                                rows = [dict(r) for r in conn.execute(q, params).fetchall()]
                                return {"items": rows, "total": len(rows)}
                        except Exception as e:
                            return {"error": str(e)}

                    def get_inventory_item(sku: str) -> Dict[str, Any]:
                        uri_db = f"file:{self.app_db.as_posix()}?mode=ro"
                        try:
                            with sqlite3.connect(uri_db, uri=True) as conn:
                                conn.row_factory = sqlite3.Row
                                if not _table_exists(conn, "product_catalog"):
                                    return {"item": None, "note": "product_catalog missing"}
                                row = conn.execute(
                                    "SELECT sku, title, currency, current_price, cost, stock, updated_at FROM product_catalog WHERE sku=? LIMIT 1",
                                    (sku,),
                                ).fetchone()
                                return {"item": dict(row) if row else None}
                        except Exception as e:
                            return {"error": str(e)}

                    def list_pricing_list(search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
                        uri_db = f"file:{self.market_db.as_posix()}?mode=ro"
                        try:
                            with sqlite3.connect(uri_db, uri=True) as conn:
                                conn.row_factory = sqlite3.Row
                                if not _table_exists(conn, "pricing_list"):
                                    return {"items": [], "total": 0, "note": "pricing_list missing"}
                                q = "SELECT product_name, optimized_price, last_update, reason FROM pricing_list"
                                params: List[Any] = []
                                if search:
                                    q += " WHERE product_name LIKE ?"
                                    params.append(f"%{search}%")
                                q += " ORDER BY last_update DESC LIMIT ?"
                                params.append(int(limit))
                                rows = [dict(r) for r in conn.execute(q, params).fetchall()]
                                return {"items": rows, "total": len(rows)}
                        except Exception as e:
                            return {"error": str(e)}

                    def list_price_proposals(sku: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
                        uri_db = f"file:{self.app_db.as_posix()}?mode=ro"
                        try:
                            with sqlite3.connect(uri_db, uri=True) as conn:
                                conn.row_factory = sqlite3.Row
                                if not _table_exists(conn, "price_proposals"):
                                    return {"items": [], "total": 0, "note": "price_proposals missing"}
                                q = (
                                    "SELECT id, sku, proposed_price, current_price, margin, algorithm, ts FROM price_proposals"
                                )
                                params: List[Any] = []
                                if sku:
                                    q += " WHERE sku = ?"
                                    params.append(sku)
                                q += " ORDER BY ts DESC LIMIT ?"
                                params.append(int(limit))
                                rows = [dict(r) for r in conn.execute(q, params).fetchall()]
                                return {"items": rows, "total": len(rows)}
                        except Exception as e:
                            return {"error": str(e)}

                    functions_map = {
                        "execute_sql": execute_sql,
                        "list_inventory_items": list_inventory_items,
                        "get_inventory_item": get_inventory_item,
                        "list_pricing_list": list_pricing_list,
                        "list_price_proposals": list_price_proposals,
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
                        )
                        # Add assistant reply to memory
                        self.add_to_memory("assistant", answer)
                        self._play_completion_sound()
                        return answer
                    except Exception:
                        # Fall through to explicit non-LLM fallback
                        pass

        except Exception:
            # Any error while attempting LLM shouldn't crash; we'll fall back
            pass

        # LLM not available or failed. Provide fallback response.
        self._play_completion_sound()
        return "[non-LLM assistant] LLM is not available. Please ensure the LLM client is configured properly."



