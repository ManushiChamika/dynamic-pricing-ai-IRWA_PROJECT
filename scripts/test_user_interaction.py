# core/agents/user_interaction.py
from __future__ import annotations

import json, http.client
from typing import List, Dict
from core.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

class UserInteractionAgent:
    """
    Lightweight chat/front-door agent for the dynamic pricing system.
    - Keeps a short-turn memory
    - Filters to pricing topics
    - Calls an LLM to answer pricing questions
    """
    def __init__(self, user_name: str = "user", max_turns: int = 20):
        self.user_name = user_name
        self.max_turns = max_turns
        self.memory: List[Dict[str, str]] = []

    # --- helpers ---
    def add_to_memory(self, role: str, content: str) -> None:
        self.memory.append({"role": role, "content": content})
        if len(self.memory) > self.max_turns:
            self.memory = self.memory[-self.max_turns:]

    def is_dynamic_pricing_related(self, message: str) -> bool:
        keys = ["price", "pricing", "discount", "margin", "demand", "competitor", "optimize"]
        m = (message or "").lower()
        return any(k in m for k in keys)

    def _llm_chat(self, messages: List[Dict[str, str]]) -> str:
        if not LLM_API_KEY:
            return "LLM_API_KEY not set. Set it to enable chat responses."

        # Parse host/path from LLM_BASE_URL
        # e.g. https://openrouter.ai/api/v1/chat/completions
        try:
            parts = LLM_BASE_URL.split("/")
            host = parts[2]
            path = "/" + "/".join(parts[3:])
        except Exception:
            return "Invalid LLM_BASE_URL configuration."

        payload = json.dumps({"model": LLM_MODEL, "messages": messages})
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LLM_API_KEY}"}

        conn = http.client.HTTPSConnection(host, timeout=20)
        try:
            conn.request("POST", path, payload, headers)
            resp = conn.getresponse()
            data = resp.read()
        finally:
            conn.close()

        if resp.status >= 400:
            return f"LLM error {resp.status}: {data[:200]!r}"
        try:
            j = json.loads(data.decode("utf-8"))
            return j["choices"][0]["message"]["content"]
        except Exception:
            return "LLM response parsing error."

    # --- public API expected by your UI ---
    def get_response(self, message: str) -> str:
        """
        Main UI entry: returns an assistant reply string.
        """
        if not self.is_dynamic_pricing_related(message):
            return "I can only answer questions related to the dynamic pricing system."

        self.add_to_memory("user", message)

        sys_msg = {
            "role": "system",
            "content": (
                "You are a specialized assistant for the dynamic pricing system. "
                "Answer ONLY questions about pricing strategies, discounts, margin/markup, "
                "demand and competitor dynamics, alerts, proposals and how this system works. "
                "Decline anything else briefly."
            ),
        }
        messages = [sys_msg] + self.memory
        reply = self._llm_chat(messages)

        # Remember assistant reply for short history continuity
        self.add_to_memory("assistant", reply)
        return reply
