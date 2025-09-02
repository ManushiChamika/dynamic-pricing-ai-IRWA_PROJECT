# core/agents/user_interact/user_interaction_agent.py
from __future__ import annotations

import asyncio
import http.client
import json
import os
import re
from typing import Any, Dict, Optional

from core.bus import bus
from core.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

# Topics used to talk to the OptimizerHub
USER_REQUEST = "USER_REQUEST"   # payload: {intent, sku, market?}
USER_REPLY   = "USER_REPLY"     # payload: {status, sku, price?, algorithm?, message?}

# Phrases that indicate the user wants to take an action (not just Q&A)
ACTION_HINTS = (
    "optimize", "optimize price", "update price", "reprice", "apply price",
    "set price", "run optimizer", "maximize profit", "increase price", "decrease price"
)

class UserInteractionAgent:
    def __init__(self, user_name: str, max_turns: int = 20, default_market: str = "DEFAULT"):
        self.user_name = user_name
        self.max_turns = max_turns
        self.default_market = default_market
        self.memory: list[Dict[str, str]] = []

    # ---------- memory ----------
    def _add_to_memory(self, role: str, content: str) -> None:
        self.memory.append({"role": role, "content": content})
        if len(self.memory) > self.max_turns:
            self.memory = self.memory[-self.max_turns:]

    # ---------- intent helpers ----------
    def is_dynamic_pricing_related(self, message: str) -> bool:
        keys = ["price", "pricing", "discount", "margin", "demand", "competitor", "reprice", "optimize"]
        msg = (message or "").lower()
        return any(k in msg for k in keys)

    def _looks_actionable(self, message: str) -> bool:
        m = (message or "").lower()
        return any(h in m for h in ACTION_HINTS)

    def _extract_sku(self, message: str) -> Optional[str]:
        # accepts “SKU-123”, “sku-123”, etc.
        m = re.search(r"\bSKU-[A-Za-z0-9_-]+\b", message or "", flags=re.IGNORECASE)
        return m.group(0).upper() if m else None

    # ---------- LLM chat (pure Q&A) ----------
    def _llm_chat(self, user_message: str) -> str:
        sys_msg = {
            "role": "system",
            "content": (
                "You are a specialized assistant for the dynamic pricing system. "
                "Answer ONLY questions about pricing strategies, discounts, demand/supply, "
                "margins and metrics. Decline anything else briefly."
            ),
        }
        messages = [sys_msg] + self.memory + [{"role": "user", "content": user_message}]

        if not LLM_API_KEY:
            return "LLM_API_KEY not set. Set it to enable chat responses."

        # Normalize URL pieces
        base = (LLM_BASE_URL or "").strip().rstrip("/")
        if not base.startswith(("http://", "https://")):
            base = "https://" + base
        try:
            scheme, rest = base.split("://", 1)
            parts = rest.split("/", 1)
            host = parts[0]
            path = "/" + parts[1] if len(parts) > 1 else "/v1/chat/completions"
        except Exception:
            return "Invalid LLM_BASE_URL."

        payload = json.dumps({
            "model": LLM_MODEL or "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 400,
        })
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
        }

        conn_cls = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
        try:
            conn = conn_cls(host, timeout=20)
            conn.request("POST", path, payload, headers)
            resp = conn.getresponse()
            data = resp.read()
            conn.close()
        except Exception as e:
            return f"LLM network error: {e}"

        if resp.status >= 400:
            return f"LLM error {resp.status}: {data[:200]!r}"

        try:
            j = json.loads(data.decode("utf-8", errors="ignore"))
            content = j["choices"][0]["message"]["content"]
        except Exception:
            return "LLM response parsing error."

        self._add_to_memory("user", user_message)
        self._add_to_memory("assistant", content)
        return content

    # ---------- bus round-trip (await a reply) ----------
    async def _await_user_reply(self, timeout_s: float = 20.0) -> Dict[str, Any]:
        """Wait for a single USER_REPLY message (with timeout)."""
        result: Dict[str, Any] = {}
        done = asyncio.Event()

        async def _handler(msg: Dict[str, Any]):
            nonlocal result
            result = msg or {}
            done.set()

        bus.subscribe(USER_REPLY, _handler)
        try:
            try:
                await asyncio.wait_for(done.wait(), timeout=timeout_s)
            except asyncio.TimeoutError:
                return {"status": "timeout", "message": "No reply from optimizer in time."}
            return result
        finally:
            if hasattr(bus, "unsubscribe"):
                try:
                    bus.unsubscribe(USER_REPLY, _handler)
                except Exception:
                    pass

    # ---------- action path (publish + wait) ----------
    async def _route_action(self, message: str) -> str:
        sku = self._extract_sku(message)
        if not sku:
            return "Please include a SKU (e.g., 'optimize price for SKU-123')."

        intent = message.strip()

        # Subscribe FIRST so a very fast reply isn’t missed
        result: Dict[str, Any] = {}
        done = asyncio.Event()

        async def _handler(msg: Dict[str, Any]):
            nonlocal result
            result = msg or {}
            done.set()

        bus.subscribe(USER_REPLY, _handler)
        try:
            # Now publish the request for the hub to handle
            await bus.publish(USER_REQUEST, {
                "intent": intent,
                "sku": sku,
                "market": self.default_market,
            })

            try:
                # wait a bit more than the dashboard default
                await asyncio.wait_for(done.wait(), timeout=12.0)
            except asyncio.TimeoutError:
                return "The optimizer is taking longer than expected. I’ll keep listening and update you once it finishes."

            status = result.get("status")
            if status == "success":
                price = result.get("price")
                algo = result.get("algorithm")
                return f"✅ Optimizer ran for {sku}. Proposed price: {price} (algo: {algo})."
            return f"❌ Couldn’t complete optimization for {sku}: {result.get('message', 'unknown error')}"

        finally:
            if hasattr(bus, "unsubscribe"):
                try:
                    bus.unsubscribe(USER_REPLY, _handler)
                except Exception:
                    pass

    # ---------- public entrypoint ----------
    async def handle(self, message: str) -> str:
        if not self.is_dynamic_pricing_related(message):
            return "I can only answer questions related to the dynamic pricing system."
        if self._looks_actionable(message):
            return await self._route_action(message)
        return self._llm_chat(message)

    # ---------- sync shim for legacy callers ----------
    def get_response(self, message: str) -> str:
        if not self.is_dynamic_pricing_related(message):
            return "I can only answer questions related to the dynamic pricing system."
        if self._looks_actionable(message):
            try:
                return asyncio.run(self._route_action(message))
            except RuntimeError:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(self._route_action(message))
        return self._llm_chat(message)
