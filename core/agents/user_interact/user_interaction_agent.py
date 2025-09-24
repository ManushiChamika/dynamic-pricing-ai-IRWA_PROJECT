import os
import sqlite3
from pathlib import Path
import re
import requests
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional
import subprocess
import platform

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
        # Lightweight intent handlers (deterministic) for common queries
        self._intents = {
            "cheapest": self._intent_cheapest,
            "most_expensive": self._intent_most_expensive,
            "trending": self._intent_trending,
            "pressure": self._intent_price_pressure,
            "stats": self._intent_stats,
        }

    def _play_completion_sound(self):
        """Play a sound to indicate task completion."""
        try:
            if platform.system() == 'Windows':
                subprocess.call(['powershell', '-c', '[console]::beep(800, 1200)'], shell=True)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['afplay', '/System/Library/Sounds/Glass.aiff'])
            elif platform.system() == 'Linux':
                subprocess.call(['beep', '-f', '800', '-l', '1200'])
        except Exception:
            pass  # Silent failure if sound not available

    # ---------- Deterministic intent helpers ----------
    def _handle_intents(self, message: str) -> Optional[str]:
        text = (message or "").lower()
        # Map patterns to intent keys; simple heuristic routing
        patterns = [
            (r"\bcheapest\b|\blow(est)? price\b|\bmin(imum)? price\b", "cheapest"),
            (r"\bmost\s+expensive\b|\bhighest\b|\bmax(imum)? price\b", "most_expensive"),
            (r"\btrend(ing)?\b|\brecent\b|\blatest\b", "trending"),
            (r"\bpressure\b|\bundercut\b|\bdemand spike\b|\bbreach\b", "pressure"),
            (r"\bstats?\b|\boverview\b|\bsummary\b", "stats"),
        ]
        for pat, key in patterns:
            if re.search(pat, text):
                handler = self._intents.get(key)
                if handler:
                    try:
                        return handler(text)
                    except Exception as e:
                        return f"[non-LLM assistant] intent '{key}' failed: {e}"
        return None

    def _intent_cheapest(self, _: str) -> str:
        # Try market.pricing_list first
        try:
            with sqlite3.connect(str(self.market_db)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("pricing_list",),
                )
                if cur.fetchone():
                    rows = conn.execute(
                        "SELECT product_name, optimized_price, last_update FROM pricing_list ORDER BY optimized_price ASC LIMIT 5"
                    ).fetchall()
                    if rows:
                        lines = [
                            f"- {r['product_name']}: {r['optimized_price']} (as of {r['last_update']})"
                            for r in rows
                        ]
                        return "Cheapest items by optimized price:\n" + "\n".join(lines)
        except Exception:
            pass
        # Fallback to product_catalog current_price
        try:
            with sqlite3.connect(str(self.app_db)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("product_catalog",),
                )
                if cur.fetchone():
                    rows = conn.execute(
                        "SELECT sku, title, current_price, updated_at FROM product_catalog WHERE current_price IS NOT NULL ORDER BY current_price ASC LIMIT 5"
                    ).fetchall()
                    if rows:
                        lines = [
                            f"- {r['sku']} ({r['title']}): {r['current_price']} (as of {r['updated_at']})"
                            for r in rows
                        ]
                        return "Cheapest items by current price:\n" + "\n".join(lines)
        except Exception:
            pass
        return "[non-LLM assistant] No pricing data available yet."

    def _intent_most_expensive(self, _: str) -> str:
        # Try market.pricing_list first
        try:
            with sqlite3.connect(str(self.market_db)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("pricing_list",),
                )
                if cur.fetchone():
                    rows = conn.execute(
                        "SELECT product_name, optimized_price, last_update FROM pricing_list ORDER BY optimized_price DESC LIMIT 5"
                    ).fetchall()
                    if rows:
                        lines = [
                            f"- {r['product_name']}: {r['optimized_price']} (as of {r['last_update']})"
                            for r in rows
                        ]
                        return "Most expensive items by optimized price:\n" + "\n".join(lines)
        except Exception:
            pass
        # Fallback to product_catalog current_price
        try:
            with sqlite3.connect(str(self.app_db)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("product_catalog",),
                )
                if cur.fetchone():
                    rows = conn.execute(
                        "SELECT sku, title, current_price, updated_at FROM product_catalog WHERE current_price IS NOT NULL ORDER BY current_price DESC LIMIT 5"
                    ).fetchall()
                    if rows:
                        lines = [
                            f"- {r['sku']} ({r['title']}): {r['current_price']} (as of {r['updated_at']})"
                            for r in rows
                        ]
                        return "Most expensive items by current price:\n" + "\n".join(lines)
        except Exception:
            pass
        return "[non-LLM assistant] No pricing data available yet."

    def _intent_trending(self, _: str) -> str:
        try:
            with sqlite3.connect(str(self.market_db)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("market_data",),
                )
                if cur.fetchone():
                    rows = conn.execute(
                        "SELECT product_name, COUNT(*) as cnt, MAX(update_time) as last_update FROM market_data GROUP BY product_name ORDER BY last_update DESC LIMIT 5"
                    ).fetchall()
                    if rows:
                        lines = [
                            f"- {r['product_name']}: {r['cnt']} updates (last {r['last_update']})"
                            for r in rows
                        ]
                        return "Trending by recent market updates:\n" + "\n".join(lines)
        except Exception:
            pass
        return "[non-LLM assistant] No recent market activity found."

    def _intent_price_pressure(self, _: str) -> str:
        # Identify SKUs where competitor prices undercut our current price by >1%
        try:
            current: dict[str, float] = {}
            with sqlite3.connect(str(self.app_db)) as conn_a:
                conn_a.row_factory = sqlite3.Row
                cur = conn_a.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("product_catalog",),
                )
                if cur.fetchone():
                    for r in conn_a.execute(
                        "SELECT sku, current_price FROM product_catalog WHERE current_price IS NOT NULL"
                    ).fetchall():
                        current[r["sku"]] = float(r["current_price"])
            if not current:
                return "[non-LLM assistant] No product catalog pricing available to assess pressure."
            undercuts: list[tuple[str, float, float, float]] = []  # sku, our, comp_min, gap
            with sqlite3.connect(str(self.market_db)) as conn_m:
                conn_m.row_factory = sqlite3.Row
                cur2 = conn_m.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("market_data",),
                )
                if cur2.fetchone():
                    for sku, our in current.items():
                        row = conn_m.execute(
                            "SELECT MIN(price) as minp FROM market_data WHERE product_name=?",
                            (sku,),
                        ).fetchone()
                        if row and row["minp"] is not None and our:
                            comp = float(row["minp"])  # best competitor
                            if comp * 1.01 < our:
                                gap = (our - comp) / our
                                undercuts.append((sku, our, comp, gap))
            if undercuts:
                undercuts.sort(key=lambda x: x[3], reverse=True)
                top = undercuts[:5]
                lines = [
                    f"- {sku}: our={our:.2f}, best_comp={comp:.2f}, gap={gap:.1%}"
                    for sku, our, comp, gap in top
                ]
                return "Price pressure (competitors undercut us):\n" + "\n".join(lines)
        except Exception:
            pass
        return "[non-LLM assistant] No price pressure detected or insufficient data."

    def _intent_stats(self, _: str) -> str:
        total_products = 0
        market_rows = 0
        distinct_products = 0
        last_update = None
        try:
            with sqlite3.connect(str(self.app_db)) as conn_a:
                cur = conn_a.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("product_catalog",),
                )
                if cur.fetchone():
                    row = conn_a.execute("SELECT COUNT(*) FROM product_catalog").fetchone()
                    total_products = int(row[0]) if row else 0
        except Exception:
            pass
        try:
            with sqlite3.connect(str(self.market_db)) as conn_m:
                cur = conn_m.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("market_data",),
                )
                if cur.fetchone():
                    row = conn_m.execute("SELECT COUNT(*) FROM market_data").fetchone()
                    market_rows = int(row[0]) if row else 0
                    row2 = conn_m.execute("SELECT COUNT(DISTINCT product_name) FROM market_data").fetchone()
                    distinct_products = int(row2[0]) if row2 else 0
                    row3 = conn_m.execute("SELECT MAX(update_time) FROM market_data").fetchone()
                    last_update = row3[0] if row3 else None
        except Exception:
            pass
        return (
            "Stats summary:\n"
            f"- product_catalog items: {total_products}\n"
            f"- market_data rows: {market_rows}\n"
            f"- market_data distinct products: {distinct_products}\n"
            f"- last market_data update: {last_update or 'n/a'}"
        )

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

        # Fast-path deterministic intents before invoking LLM
        intent_answer = self._handle_intents(message)
        if intent_answer:
            self.add_to_memory("assistant", intent_answer)
            self._play_completion_sound()
            return intent_answer

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
                        self._play_completion_sound()
                        return answer
                    except Exception:
                        # Fall through to explicit non-LLM fallback
                        pass

        except Exception:
            # Any error while attempting LLM shouldn't crash; we'll fall back
            pass

        # LLM not available or failed. Use keyword guard to determine messaging; but mark as non-LLM.
        if not self.is_dynamic_pricing_related(message):
            self._play_completion_sound()
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
                self._play_completion_sound()
                return answer
            else:
                self._play_completion_sound()
                return f"[non-LLM assistant] Error {response.status_code}: {response.text}"

        except Exception as e:
            self._play_completion_sound()
            return f"[non-LLM assistant] Exception: {str(e)}"
