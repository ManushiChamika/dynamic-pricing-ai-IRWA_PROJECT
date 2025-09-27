"""
Lightweight LLM client wrapper for the Streamlit app.

Supports:
- OpenRouter (preferred if OPENROUTER_API_KEY is set)
- OpenAI (fallback if OPENAI_API_KEY is set)
- Gemini via Google OpenAI-compatible endpoint (fallback if GEMINI_API_KEY is set)

No external dotenv dependency; we do a small .env load like in core agents.
"""
from __future__ import annotations

import os
import importlib
import logging
from pathlib import Path
from typing import Optional, Any, Dict, List, Callable
import json


def _load_dotenv_if_present() -> None:
    """Minimal .env loader from project root if env vars not already present."""
    # If either key already present, skip loading
    if any(os.getenv(k) for k in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY")):
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
    """Tiny wrapper around OpenAI-compatible SDKs with multi-provider fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self._log = logging.getLogger("pricing_app.llm")
        if os.getenv("DEBUG_LLM"):
            self._log.setLevel(logging.DEBUG)
            if not self._log.handlers:
                handler = logging.StreamHandler()
                fmt = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
                handler.setFormatter(fmt)
                self._log.addHandler(handler)

        _load_dotenv_if_present()

        self._providers: List[Dict[str, Any]] = []
        self._active_index: Optional[int] = None
        self.model: Optional[str] = None
        self._provider: str = "none"
        self._unavailable_reason: Optional[str] = None

        try:
            openai_mod = importlib.import_module("openai")
        except ModuleNotFoundError:
            self._unavailable_reason = "openai package not installed"
            self._log.debug("LLM unavailable: %s", self._unavailable_reason)
            return

        def _prepare_headers(provider_name: str, key: str) -> Dict[str, str]:
            if provider_name == "openrouter":
                return {
                    "HTTP-Referer": os.getenv("OPENROUTER_REFERRER", "http://localhost:8501"),
                    "X-Title": os.getenv("OPENROUTER_TITLE", "FluxPricer AI"),
                }
            if provider_name == "gemini":
                # Google accepts bearer token auth, but including API key header avoids conflicts.
                return {"x-goog-api-key": key}
            return {}

        def _register_provider(
            provider_name: str,
            provider_api_key: Optional[str],
            provider_model: Optional[str],
            provider_base_url: Optional[str],
        ) -> None:
            if not provider_api_key:
                return

            model_name = provider_model or "gpt-4o-mini"
            headers = _prepare_headers(provider_name, provider_api_key)
            kwargs: Dict[str, Any] = {"api_key": provider_api_key}
            if provider_base_url:
                kwargs["base_url"] = provider_base_url
            if headers:
                kwargs["default_headers"] = headers

            try:
                client = openai_mod.OpenAI(**kwargs)
            except TypeError:
                # Older SDKs may not accept default_headers in constructor.
                headers_payload = kwargs.pop("default_headers", None)
                client = openai_mod.OpenAI(**kwargs)
                if headers_payload:
                    try:
                        client.default_headers = headers_payload  # type: ignore[attr-defined]
                    except Exception:
                        pass
            except Exception as exc:
                self._log.error("Failed to initialize %s client: %s", provider_name, exc)
                return

            self._providers.append(
                {
                    "name": provider_name,
                    "client": client,
                    "model": model_name,
                    "base_url": provider_base_url,
                }
            )
            self._log.debug(
                "Registered provider %s | model=%s base_url=%s",
                provider_name,
                model_name,
                provider_base_url or "<default>",
            )

        # Resolve environment defaults
        explicit_key = api_key
        explicit_base = base_url
        explicit_model = model

        or_key = os.getenv("OPENROUTER_API_KEY")
        or_base = base_url if (explicit_key and explicit_base) else os.getenv("OPENROUTER_BASE_URL")
        if not or_base and or_key:
            or_base = "https://openrouter.ai/api/v1"
        or_model = os.getenv("OPENROUTER_MODEL") or "z-ai/glm-4.5-air:free"

        oa_key = os.getenv("OPENAI_API_KEY")
        oa_model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

        gemini_key = os.getenv("GEMINI_API_KEY")
        gemini_base = os.getenv("GEMINI_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta/openai/"
        if gemini_base and not gemini_base.endswith("/"):
            gemini_base = gemini_base + "/"
        gemini_model = os.getenv("GEMINI_MODEL") or "gemini-2.0-flash"

        # Registration priority: explicit args > OpenRouter > OpenAI > Gemini
        if explicit_key:
            custom_model = explicit_model or or_model or oa_model or gemini_model
            _register_provider("custom", explicit_key, custom_model, explicit_base)
        else:
            _register_provider("openrouter", or_key, or_model, or_base)
            _register_provider("openai", oa_key, oa_model, None)
            _register_provider("gemini", gemini_key, gemini_model, gemini_base if gemini_key else None)

        if not self._providers:
            self._unavailable_reason = "no API key configured"
            self._log.debug("LLM unavailable: %s", self._unavailable_reason)
            return

        self._set_active_provider(0)

    def _set_active_provider(self, index: int) -> None:
        provider = self._providers[index]
        self._active_index = index
        self.model = provider["model"]
        self._provider = provider["name"]

    def _provider_indices(self) -> List[int]:
        if not self._providers:
            return []
        order: List[int] = []
        if self._active_index is not None:
            order.append(self._active_index)
        order.extend(idx for idx in range(len(self._providers)) if idx != self._active_index)
        return order

    def is_available(self) -> bool:
        return bool(self._providers)

    def provider(self) -> str:
        return self._provider

    def unavailable_reason(self) -> Optional[str]:
        return self._unavailable_reason

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 256, temperature: float = 0.2) -> str:
        """Call chat completions; returns assistant content or raises on hard failure."""
        if not self._providers:
            raise RuntimeError("LLM client unavailable (missing key or package)")

        last_error: Optional[Exception] = None
        for idx in self._provider_indices():
            provider = self._providers[idx]
            try:
                self._log.debug(
                    "Sending chat completion | provider=%s model=%s msgs=%d max_tokens=%d temp=%.2f",
                    provider["name"],
                    provider["model"],
                    len(messages),
                    max_tokens,
                    temperature,
                )
                resp = provider["client"].chat.completions.create(
                    model=provider["model"],
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                content = (resp.choices[0].message.content or "").strip()
                self._set_active_provider(idx)
                self._log.debug("LLM response chars=%d", len(content))
                return content
            except Exception as exc:
                last_error = exc
                self._log.warning("Provider %s failed for chat: %s", provider["name"], exc)
                continue

        raise RuntimeError(f"LLM error: {last_error or 'no provider succeeded'}")

    def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        functions_map: Dict[str, Callable[..., Any]],
        tool_choice: Optional[str] = "auto",
        max_rounds: int = 3,
        max_tokens: int = 256,
        temperature: float = 0.2,
    ) -> str:
        """OpenAI-style tool calling loop.

        - Sends tools schema to the model.
        - If the model returns tool_calls, executes mapped Python functions.
        - Appends tool outputs as messages with role="tool" and continues.
        - Returns final assistant content when no further tool_calls are present.
        """
        if not self._providers:
            raise RuntimeError("LLM client unavailable (missing key or package)")

        last_error: Optional[Exception] = None
        for idx in self._provider_indices():
            provider = self._providers[idx]
            try:
                local_msgs: List[Dict[str, Any]] = list(messages)
                assistant_msg: Dict[str, Any] = {}
                for round_i in range(max_rounds):
                    self._log.debug(
                        "Tool round %d | provider=%s model=%s msgs=%d tools=%d",
                        round_i + 1,
                        provider["name"],
                        provider["model"],
                        len(local_msgs),
                        len(tools),
                    )
                    resp = provider["client"].chat.completions.create(
                        model=provider["model"],
                        messages=local_msgs,
                        tools=tools,
                        **({"tool_choice": tool_choice} if tool_choice else {}),
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )

                    choice = resp.choices[0]
                    msg = choice.message
                    content = getattr(msg, "content", None)
                    tool_calls = getattr(msg, "tool_calls", None) or []

                    assistant_msg = {"role": "assistant"}
                    if content is not None:
                        assistant_msg["content"] = content
                    if tool_calls:
                        normalized_calls = []
                        for tc in tool_calls:
                            try:
                                normalized_calls.append({
                                    "id": tc.id,
                                    "type": getattr(tc, "type", "function"),
                                    "function": {
                                        "name": tc.function.name,
                                        "arguments": tc.function.arguments,
                                    },
                                })
                            except Exception:
                                normalized_calls.append(json.loads(json.dumps(tc)))
                        assistant_msg["tool_calls"] = normalized_calls

                    local_msgs.append(assistant_msg)

                    if not tool_calls:
                        self._set_active_provider(idx)
                        return (content or "").strip()

                    for tc in assistant_msg["tool_calls"]:
                        fn_name = tc.get("function", {}).get("name")
                        raw_args = tc.get("function", {}).get("arguments") or "{}"
                        call_id = tc.get("id") or "tool_call"
                        try:
                            args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                        except Exception:
                            args = {}
                        result: Any
                        if fn_name in functions_map:
                            try:
                                result = functions_map[fn_name](**args)
                            except TypeError:
                                result = functions_map[fn_name](args)
                            except Exception as tool_exc:
                                result = {"error": str(tool_exc)}
                        else:
                            result = {"error": f"unknown tool: {fn_name}"}

                        try:
                            content_str = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
                        except Exception:
                            content_str = str(result)

                        local_msgs.append(
                            {
                                "role": "tool",
                                "tool_call_id": call_id,
                                "name": fn_name,
                                "content": content_str,
                            }
                        )

                # max rounds exhausted
                self._set_active_provider(idx)
                return (assistant_msg.get("content") or "").strip()
            except Exception as exc:
                last_error = exc
                self._log.warning("Provider %s failed for tool call: %s", provider["name"], exc)
                continue

        raise RuntimeError(f"LLM tools error: {last_error or 'no provider succeeded'}")


def get_llm_client() -> LLMClient:
    return LLMClient()
