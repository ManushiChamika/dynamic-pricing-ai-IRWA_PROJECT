from __future__ import annotations

from typing import Optional, List, Dict

try:
    # Reuse app's lightweight LLM client if available
    from app.llm_client import get_llm_client
except Exception:
    get_llm_client = None  # type: ignore


class UserInteractionAgent:
    """Simple wrapper around an LLM to handle dashboard chat.

    If no LLM is configured/installed, falls back to a polite stub response.
    """

    def __init__(self, user_name: str = "User", model_name: str = "gpt-4o-mini"):
        self.user_name = user_name
        self.model_name = model_name
        self._llm = None
        if get_llm_client:
            try:
                self._llm = get_llm_client()
            except Exception:
                self._llm = None

    def get_response(self, text: str) -> str:
        if self._llm and self._llm.is_available():
            try:
                msgs: List[Dict[str, str]] = [
                    {"role": "system", "content": (
                        "You are a concise pricing assistant. Answer briefly, "
                        "with 1-2 actionable insights about dynamic pricing, demand, or sales."
                    )},
                    {"role": "user", "content": f"{self.user_name} asks: {text}"},
                ]
                return self._llm.chat(msgs, max_tokens=180, temperature=0.2)
            except Exception:
                pass

        # Fallback stub
        return (
            f"Hi {self.user_name}, you asked: '{text}'. "
            f"The core LLM isn't configured; please set OPENROUTER_API_KEY or OPENAI_API_KEY in .env to enable AI answers."
        )
