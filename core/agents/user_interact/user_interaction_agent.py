import os
import sqlite3
from pathlib import Path
import requests
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional

# Load .env variables
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
        # Memory to store conversation history
        self.memory = []
        # Resolve DB paths
        root = Path(__file__).resolve().parents[3]
        self.app_db = root / "app" / "data.db"
        self.market_db = root / "market.db"

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
            f"Only provide responses related to pricing strategies, discounts, "
            f"offers, demand/supply, and related financial metrics."
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

                    def list_inventory_items(search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
                        db_path = str(self.app_db)
                        try:
                            with sqlite3.connect(db_path) as conn:
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
                        db_path = str(self.app_db)
                        try:
                            with sqlite3.connect(db_path) as conn:
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
                        db_path = str(self.market_db)
                        try:
                            with sqlite3.connect(db_path) as conn:
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
                        db_path = str(self.app_db)
                        try:
                            with sqlite3.connect(db_path) as conn:
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
                        "list_inventory_items": list_inventory_items,
                        "get_inventory_item": get_inventory_item,
                        "list_pricing_list": list_pricing_list,
                        "list_price_proposals": list_price_proposals,
                    }

                    try:
                        answer = llm.chat_with_tools(
                            messages=msgs,
                            tools=tools,
                            functions_map=functions_map,
                            tool_choice="auto",
                            max_rounds=4,
                            max_tokens=384,
                            temperature=0.2,
                        )
                        # Add assistant reply to memory
                        self.add_to_memory("assistant", answer)
                        return answer
                    except Exception:
                        # Fall through to explicit non-LLM fallback
                        pass

        except Exception:
            # Any error while attempting LLM shouldn't crash; we'll fall back
            pass

        # LLM not available or failed. Use keyword guard to determine messaging; but mark as non-LLM.
        if not self.is_dynamic_pricing_related(message):
            return "[non-LLM assistant] I'm only able to respond to queries related to the dynamic pricing system."

        # As a last resort, attempt the previous direct HTTP OpenRouter path (preserves compatibility)
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            messages = [{"role": "system", "content": system_prompt}]
            # self.memory already includes the latest user message added above
            messages.extend(self.memory)

            data = {
                "model": self.model_name,
                "messages": messages
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                answer = response.json()["choices"][0]["message"]["content"]
                self.add_to_memory("assistant", answer)
                return answer
            else:
                return f"[non-LLM assistant] Error {response.status_code}: {response.text}"

        except Exception as e:
            return f"[non-LLM assistant] Exception: {str(e)}"
