"""
Lightweight LLM client wrapper for the Streamlit app.

Supports:
- OpenRouter (preferred if OPENROUTER_API_KEY is set)
- OpenAI (fallback if OPENAI_API_KEY is set)

No external dotenv dependency; we do a small .env load like in core agents.
"""
from __future__ import annotations

import os
import importlib
import logging
from pathlib import Path
from typing import Optional, Any, Dict, List


def _load_dotenv_if_present() -> None:
    """Minimal .env loader from project root if env vars not already present."""
    # If either key already present, skip loading
    if os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"):
        return
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    if not env_path.exists():
        return
    try:
        with env_path.open("r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and not os.getenv(k):
                    os.environ[k] = v
    except Exception as e:
        # Best-effort; log and continue
        logging.getLogger("pricing_app.llm").debug("dotenv load skipped due to error: %s", e)
        pass


class LLMClient:
    """Tiny wrapper around OpenAI SDK compatible clients (OpenAI & OpenRouter)."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        # Logger for diagnostics
        self._log = logging.getLogger("pricing_app.llm")
        # Allow enabling debug via env var
        if os.getenv("DEBUG_LLM"):
            self._log.setLevel(logging.DEBUG)
            if not self._log.handlers:
                handler = logging.StreamHandler()
                fmt = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
                handler.setFormatter(fmt)
                self._log.addHandler(handler)

        _load_dotenv_if_present()
        # Detect provider
        or_key = os.getenv("OPENROUTER_API_KEY")
        oa_key = os.getenv("OPENAI_API_KEY")
        # Choose key priority: explicit > OpenRouter > OpenAI
        api_key = api_key or or_key or oa_key
        # Base URL: if using OpenRouter (key or explicit base url), default to OR URL; otherwise leave None for OpenAI
        if base_url:
            resolved_base = base_url
        elif os.getenv("OPENROUTER_BASE_URL") or or_key:
            resolved_base = os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"
        else:
            resolved_base = None
        # Model: prefer provider-specific defaults
        if model:
            resolved_model = model
        elif or_key or os.getenv("OPENROUTER_BASE_URL"):
            resolved_model = os.getenv("OPENROUTER_MODEL") or "z-ai/glm-4.5-air:free"
        else:
            resolved_model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
        self.model = resolved_model
        self._base_url = resolved_base
        self._provider = "openrouter" if (or_key or os.getenv("OPENROUTER_BASE_URL")) else ("openai" if oa_key else "none")
        self._client = None
        self._unavailable_reason: Optional[str] = None

        if not api_key:
            self._unavailable_reason = "no API key configured"
            self._log.debug("LLM unavailable: %s", self._unavailable_reason)
            return

        try:
            openai_mod = importlib.import_module("openai")
            try:
                # Newer SDK; pass base_url only if set. For OpenRouter, also send default headers.
                if resolved_base:
                    default_headers = None
                    if self._provider == "openrouter":
                        default_headers = {
                            # Optional but recommended by OpenRouter
                            "HTTP-Referer": os.getenv("OPENROUTER_REFERRER", "http://localhost:8501"),
                            "X-Title": os.getenv("OPENROUTER_TITLE", "FluxPricer AI"),
                        }
                    # Some SDK versions accept default_headers in constructor
                    try:
                        self._client = openai_mod.OpenAI(
                            api_key=api_key, base_url=resolved_base,
                            **({"default_headers": default_headers} if default_headers else {})
                        )
                    except TypeError:
                        # Constructor may not accept default_headers; build then set
                        self._client = openai_mod.OpenAI(api_key=api_key, base_url=resolved_base)
                        try:
                            if default_headers is not None:
                                self._client.default_headers = default_headers  # type: ignore[attr-defined]
                        except Exception:
                            pass
                else:
                    self._client = openai_mod.OpenAI(api_key=api_key)
            except Exception:
                # Fallback to module-level config
                try:
                    openai_mod.api_key = api_key
                except Exception:
                    pass
                if resolved_base:
                    try:
                        openai_mod.base_url = resolved_base
                    except Exception:
                        pass
                    # Cannot set default headers on module-level, ignore.
                self._client = openai_mod
            self._log.debug(
                "LLM client initialized | provider=%s model=%s base_url=%s",
                self._provider,
                self.model,
                self._base_url or "<default>",
            )
        except ModuleNotFoundError:
            # openai not installed; leave as None - caller can fallback
            self._client = None
            self._unavailable_reason = "openai package not installed"
            self._log.debug("LLM unavailable: %s", self._unavailable_reason)

    def is_available(self) -> bool:
        return self._client is not None

    def provider(self) -> str:
        return self._provider

    def unavailable_reason(self) -> Optional[str]:
        return self._unavailable_reason

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 256, temperature: float = 0.2) -> str:
        """Call chat completions; returns assistant content or raises on hard failure."""
        if not self._client:
            raise RuntimeError("LLM client unavailable (missing key or package)")
        try:
            self._log.debug(
                "Sending chat completion | provider=%s model=%s msgs=%d max_tokens=%d temp=%.2f",
                self._provider,
                self.model,
                len(messages),
                max_tokens,
                temperature,
            )
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = (resp.choices[0].message.content or "").strip()
            self._log.debug("LLM response chars=%d", len(content))
            return content
        except Exception as e:
            self._log.error("LLM error: %s", e)
            raise RuntimeError(f"LLM error: {e}")


def get_llm_client() -> LLMClient:
    return LLMClient()
