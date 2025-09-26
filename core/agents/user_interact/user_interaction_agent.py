from __future__ import annotations

import os
import re
import sqlite3
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Bus event constants
USER_REQUEST = "user.request"
USER_REPLY = "user.reply"

try:
    from app.llm_client import get_llm_client  # Preferred LLM client with tool-calling
except Exception:
    get_llm_client = None  # Guarded usage below


class UserInteractionAgent:
    def __init__(self, user_name: str):
        self.user_name = user_name
        self.last_result: Optional[dict] = None  # remember last referenced product
        self.memory: List[Dict[str, str]] = []
        # Callback function for memory synchronization with UI
        self._memory_sync_callback: Optional[callable] = None
        # Feature flag for notification sound
        self.enable_sound = os.getenv("SOUND_NOTIFICATIONS", "0").strip().lower() in {"1", "true", "yes", "on"}
        # Feature flag for development mode (disables domain filtering)
        self.development_mode = os.getenv("DEVELOPMENT_MODE", "0").strip().lower() in {"1", "true", "yes", "on"}

        # Resolve DB paths from project root
        root = Path(__file__).resolve().parents[3]
        self.app_db = root / "app" / "data.db"
        self.market_db = root / "market.db"

        # Domain keywords for simple guard (expanded for better UX)
        self.keywords = [
            # Core pricing terms
            "price", "pricing", "discount", "margin", "demand",
            "competitor", "reprice", "optimize", "update",
            "trend", "trending", "mover", "cheapest", "expensive",
            "stats", "pressure", "proposal", "market", "product", "sku",
            # Conversational terms to allow basic interaction
            "hello", "hi", "hey", "claude", "assistant", "help", "thanks", "thank",
            "what", "how", "why", "when", "where", "can", "could", "would", "should",
            # General business terms
            "business", "sales", "revenue", "profit", "analysis", "data", "report"
        ]

        # Deterministic, local intent handlers
        self._intents = {
            "cheapest": self._intent_cheapest,
            "most_expensive": self._intent_most_expensive,
            "trending": self._intent_trending,
            "pressure": self._intent_price_pressure,
            "stats": self._intent_stats,
        }

    # ---------- helpers ----------
    def _play_completion_sound(self):
        if not getattr(self, "enable_sound", False):
            return
        try:
            if platform.system() == 'Windows':
                subprocess.call(['powershell', '-c', '[console]::beep(800, 300)'], shell=True)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['afplay', '/System/Library/Sounds/Glass.aiff'])
            elif platform.system() == 'Linux':
                subprocess.call(['beep', '-f', '800', '-l', '300'])
        except Exception:
            pass

    def _refer_last_product(self, message: str) -> Optional[dict]:
        if not self.last_result:
            return None
        pronouns = ("it", "that", "this", "the product")
        if any(p in (message or "").lower() for p in pronouns):
            return self.last_result
        return None

    def is_dynamic_pricing_related(self, message: str) -> bool:
        text = (message or "").lower()
        return any(k in text for k in self.keywords)

    def add_to_memory(self, role: str, content: str, sync_to_ui: bool = True) -> None:
        """Add a message to agent memory and optionally sync to UI storage"""
        message = {"role": role, "content": content}
        self.memory.append(message)
        
        # Trigger UI synchronization if callback is set and sync is enabled
        if sync_to_ui and self._memory_sync_callback:
            try:
                self._memory_sync_callback(role, content)
            except Exception:
                # Don't let sync failures break agent functionality
                pass

    def set_memory_sync_callback(self, callback: callable) -> None:
        """Set the callback function for synchronizing memory with UI storage"""
        self._memory_sync_callback = callback

    def clear_memory(self) -> None:
        """Clear agent memory (useful for testing or reset scenarios)"""
        self.memory = []

    def seed_memory_from_messages(self, messages: List[Dict[str, str]], sync_to_ui: bool = False) -> None:
        """Seed agent memory from a list of messages without triggering UI sync"""
        self.memory = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if role in ("user", "assistant") and isinstance(content, str):
                self.add_to_memory(role, content, sync_to_ui=sync_to_ui)

    def get_memory_info(self) -> Dict[str, Any]:
        """Get debugging information about current memory state"""
        return {
            "message_count": len(self.memory),
            "user_messages": len([m for m in self.memory if m.get("role") == "user"]),
            "assistant_messages": len([m for m in self.memory if m.get("role") == "assistant"]),
            "has_sync_callback": self._memory_sync_callback is not None,
            "last_message": self.memory[-1] if self.memory else None,
            "memory_size_bytes": sum(len(str(m.get("content", ""))) for m in self.memory)
        }

    def validate_memory_consistency(self, ui_messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Validate that agent memory is consistent with UI message storage"""
        agent_count = len(self.memory)
        ui_count = len(ui_messages)
        
        # Check message count consistency
        count_match = agent_count == ui_count
        
        # Check content consistency for last few messages
        content_match = True
        content_mismatches = []
        
        compare_count = min(agent_count, ui_count, 5)  # Check last 5 messages
        for i in range(compare_count):
            agent_msg = self.memory[-(i+1)]
            ui_msg = ui_messages[-(i+1)]
            
            if (agent_msg.get("role") != ui_msg.get("role") or 
                agent_msg.get("content") != ui_msg.get("content")):
                content_match = False
                content_mismatches.append({
                    "position": i,
                    "agent": agent_msg,
                    "ui": ui_msg
                })
        
        return {
            "is_consistent": count_match and content_match,
            "agent_message_count": agent_count,
            "ui_message_count": ui_count,
            "count_match": count_match,
            "content_match": content_match,
            "content_mismatches": content_mismatches,
            "sync_callback_set": self._memory_sync_callback is not None
        }

    # ---------- deterministic intents ----------
    def _handle_intents(self, message: str) -> Optional[str]:
        text = (message or "").lower()
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
                        self.last_result = {"sku": rows[0]["product_name"], "label": rows[0]["product_name"]}
                        return "Cheapest items by optimized price:\n" + "\n".join(lines)
        except Exception:
            pass
        # Fallback to products base_price
        try:
            with sqlite3.connect(str(self.app_db)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("products",),
                )
                if cur.fetchone():
                    rows = conn.execute(
                        "SELECT sku, name as title, base_price as current_price, updated_at FROM products WHERE base_price IS NOT NULL ORDER BY base_price ASC LIMIT 5"
                    ).fetchall()
                    if rows:
                        lines = [
                            f"- {r['sku']} ({r['title']}): {r['current_price']} (as of {r['updated_at']})"
                            for r in rows
                        ]
                        self.last_result = {"sku": rows[0]["sku"], "label": rows[0]["title"]}
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
        # Fallback to products base_price
        try:
            with sqlite3.connect(str(self.app_db)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("products",),
                )
                if cur.fetchone():
                    rows = conn.execute(
                        "SELECT sku, name as title, base_price as current_price, updated_at FROM products WHERE base_price IS NOT NULL ORDER BY base_price DESC LIMIT 5"
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
                        self.last_result = {"sku": rows[0]["product_name"], "label": rows[0]["product_name"]}
                        return "Trending by recent market updates:\n" + "\n".join(lines)
        except Exception:
            pass
        return "[non-LLM assistant] No recent market activity found."

    def _intent_price_pressure(self, _: str) -> str:
        # Identify SKUs where competitor prices undercut our current price by >1%
        try:
            current: Dict[str, float] = {}
            with sqlite3.connect(str(self.app_db)) as conn_a:
                conn_a.row_factory = sqlite3.Row
                cur = conn_a.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("products",),
                )
                if cur.fetchone():
                    for r in conn_a.execute(
                        "SELECT sku, base_price FROM products WHERE base_price IS NOT NULL"
                    ).fetchall():
                        current[str(r["sku"])] = float(r["base_price"])
            if not current:
                return "[non-LLM assistant] No products pricing available to assess pressure."
            undercuts: List[tuple[str, float, float, float]] = []  # sku, our, comp_min, gap
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
                    ("products",),
                )
                if cur.fetchone():
                    row = conn_a.execute("SELECT COUNT(*) FROM products").fetchone()
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
            f"- products items: {total_products}\n"
            f"- market_data rows: {market_rows}\n"
            f"- market_data distinct products: {distinct_products}\n"
            f"- last market_data update: {last_update or 'n/a'}"
        )

    # ---------- public entry ----------
    def get_response(self, message: str) -> str:
        # Add user message to memory
        self.add_to_memory("user", message)

        # Try deterministic intents first
        intent_answer = self._handle_intents(message)
        if intent_answer:
            self.add_to_memory("assistant", intent_answer)
            self._play_completion_sound()
            return intent_answer

        # Build system prompt focused on dynamic pricing
        system_prompt = (
            "You are a specialized assistant for the dynamic pricing system. "
            "Only provide responses related to pricing strategies, discounts, "
            "offers, demand/supply, market data, and related financial metrics."
        )

        # Attempt to use LLM client if available
        try:
            if get_llm_client is not None:
                llm = get_llm_client()
                if llm.is_available():
                    msgs: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
                    msgs.extend(self.memory)

                    # OpenAI-style tools for local data lookup
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
                                if not _table_exists(conn, "products"):
                                    return {"items": [], "total": 0, "note": "products table missing"}
                                q = "SELECT sku, name as title, currency, base_price as current_price, cost, NULL as stock, updated_at FROM products"
                                params: List[Any] = []
                                if search:
                                    q += " WHERE sku LIKE ? OR name LIKE ?"
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
                                if not _table_exists(conn, "products"):
                                    return {"item": None, "note": "products table missing"}
                                row = conn.execute(
                                    "SELECT sku, name as title, currency, base_price as current_price, cost, NULL as stock, updated_at FROM products WHERE sku=? LIMIT 1",
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

                    tools = [
                        {
                            "type": "function",
                            "function": {
                                "name": "list_inventory_items",
                                "description": "List items from the local products table (app/data.db). Use for inventory overviews.",
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
                        self.add_to_memory("assistant", answer)
                        self._play_completion_sound()
                        return answer
                    except Exception:
                        # Fall through to explicit non-LLM fallback / HTTP path
                        pass
        except Exception:
            # Any error while attempting LLM shouldn't crash; we'll fall back
            pass

        # Non-LLM path. First, enforce domain guard (unless in development mode).
        if not self.is_dynamic_pricing_related(message):
            if self.development_mode:
                # In development mode, allow off-topic queries but warn
                pass  # Continue to HTTP fallback
            else:
                self._play_completion_sound()
                return "[non-LLM assistant] I'm only able to respond to queries related to the dynamic pricing system."

        # Optional HTTP fallback (if environment provides base URL and key)
        try:
            base_url = os.getenv("OPENROUTER_BASE_URL") or os.getenv("LLM_BASE_URL")
            api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
            model_name = os.getenv("OPENROUTER_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
            if base_url and api_key:
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(self.memory)
                data = {"model": model_name, "messages": messages}
                response = requests.post(f"{base_url}/chat/completions", headers=headers, json=data, timeout=30)
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

        # Final non-LLM fallback
        self._play_completion_sound()
        return (
            "[non-LLM assistant] I can help with pricing, products, trends, "
            "competitors, proposals, or stats. Try e.g. 'cheapest items', 'trending', 'price pressure', or 'show proposals'."
        )
