from __future__ import annotations

import os
import importlib
import logging
from pathlib import Path
from typing import Optional, Any, Dict, List, Callable
import json
from datetime import datetime

from .llm_provider_manager import (
    ProviderManager,
    _save_gemini_working_key,
)
from .base_chat_handler import BaseChatHandler


def _load_dotenv_if_present() -> None:
    """Minimal .env loader from project root if env vars not already present.

    Avoid loading `.env` during pytest runs so tests that monkeypatch environment
    control LLM configuration deterministically.
    """
    if os.getenv("PYTEST_CURRENT_TEST") is not None:
        return
    # If any of the keys are explicitly present in the environment (even empty),
    # respect the caller's intent and DO NOT load from .env. This is important
    # for tests that set keys to empty strings to simulate "no key".
    if any(k in os.environ for k in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY")):
        return
    root = Path(__file__).resolve().parents[2]
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
                if k and not os.getenv(k, "").strip():
                    os.environ[k] = v
    except Exception as e:
        logging.getLogger("core.agents.llm").debug("dotenv load skipped due to error: %s", e)
        pass



class LLMClient:

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self._log = logging.getLogger("core.agents.llm")
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
        self.last_usage: Dict[str, Any] = {}

        try:
            openai_mod = importlib.import_module("openai")
        except ModuleNotFoundError:
            self._unavailable_reason = "openai package not installed"
            self._log.debug("LLM unavailable: %s", self._unavailable_reason)
            return

        provider_manager = ProviderManager(self._log)
        provider_manager.load_providers_from_env(openai_mod, api_key, base_url, model)
        self._providers = provider_manager.get_providers()

        if not self._providers:
            self._unavailable_reason = "no API key configured"
            self._log.debug("LLM unavailable: %s", self._unavailable_reason)
            return

        self._set_active_provider(0)

    def _set_active_provider(self, index: int) -> None:
        if index < 0 or index >= len(self._providers):
            self._log.error("Invalid provider index: %d", index)
            return
        
        try:
            provider = self._providers[index]
            self._active_index = index
            self.model = provider["model"]
            self._provider = provider["name"]
            
            if self._provider.startswith("gemini"):
                api_key = provider.get("api_key")
                if api_key:
                    _save_gemini_working_key(api_key)
            
            prior = self.last_usage or {}
            self.last_usage = {**prior, "provider": self._provider, "model": self.model}
            self._log.debug("Active provider set to: %s (model: %s)", self._provider, self.model)
        except Exception as e:
            self._log.error("Failed to set active provider: %s", e)

    def _get_handler(self) -> BaseChatHandler:
        return BaseChatHandler(self._providers, self._active_index, self._log, self.last_usage)

    def is_available(self) -> bool:
        return bool(self._providers)

    def provider(self) -> str:
        return self._provider

    def unavailable_reason(self) -> Optional[str]:
        return self._unavailable_reason

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 256, temperature: float = 0.2) -> str:
        handler = self._get_handler()
        content, idx = handler.execute_chat(messages, max_tokens, temperature, "chat completion")
        self.last_usage = handler.last_usage
        self._set_active_provider(idx)
        return content

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 256,
        temperature: float = 0.2,
    ):
        if not self._providers:
            raise RuntimeError("LLM client unavailable (missing key or package)")

        handler = self._get_handler()
        last_error: Optional[Exception] = None
        for idx in handler.provider_indices():
            provider = self._providers[idx]
            try:
                try:
                    stream = provider["client"].chat.completions.create(
                        model=provider["model"],
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stream=True,
                        stream_options={"include_usage": True},
                    )
                    full: List[str] = []
                    for event in stream:
                        try:
                            usage = getattr(event, "usage", None)
                            if usage:
                                handler.capture_usage(event, provider["name"], provider["model"])
                            choices = getattr(event, "choices", None) or []
                            if choices:
                                delta = getattr(choices[0], "delta", None)
                                if delta is not None:
                                    text = getattr(delta, "content", None)
                                    if text:
                                        full.append(text)
                                        yield text
                        except Exception:
                            continue
                    self.last_usage = handler.last_usage
                    self._set_active_provider(idx)
                    return
                except Exception as se:
                    self._log.debug("Streaming not available for %s: %s", provider["name"], se)
                    content = self.chat(messages, max_tokens=max_tokens, temperature=temperature)
                    yield content
                    self._set_active_provider(idx)
                    return
            except Exception as exc:
                last_error = exc
                error_type = type(exc).__name__
                self._log.warning("Provider %s failed for stream (%s): %s", provider["name"], error_type, exc)
                continue

        error_msg = f"All LLM providers failed for streaming. Last error: {last_error or 'no provider succeeded'}"
        self._log.error(error_msg)
        raise RuntimeError(error_msg)

    def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        functions_map: Dict[str, Callable[..., Any]],
        tool_choice: Optional[str] = "auto",
        max_rounds: int = 3,
        max_tokens: int = 256,
        temperature: float = 0.2,
        trace_id: Optional[str] = None,
    ) -> str:
        handler = self._get_handler()
        content, idx, tools_used = handler.execute_chat_with_tools(
            messages, tools, functions_map, tool_choice, max_rounds, max_tokens, temperature, trace_id
        )
        if tools_used:
            handler.last_usage = {**(handler.last_usage or {}), "tools_used": tools_used}
        self.last_usage = handler.last_usage
        self._set_active_provider(idx)
        return content

    def chat_with_tools_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        functions_map: Dict[str, Callable[..., Any]],
        tool_choice: Optional[str] = "auto",
        max_rounds: int = 3,
        max_tokens: int = 256,
        temperature: float = 0.2,
        trace_id: Optional[str] = None,
    ):
        if not self._providers:
            raise RuntimeError("LLM client unavailable (missing key or package)")

        handler = self._get_handler()
        last_error: Optional[Exception] = None
        tools_used: List[str] = []

        for idx in handler.provider_indices():
            provider = self._providers[idx]
            try:
                local_msgs: List[Dict[str, Any]] = list(messages)
                for round_i in range(max_rounds):
                    self._log.debug(
                        "Tool-stream round %d | provider=%s model=%s msgs=%d tools=%d",
                        round_i + 1,
                        provider["name"],
                        provider["model"],
                        len(local_msgs),
                        len(tools),
                    )
                    try:
                        stream = provider["client"].chat.completions.create(
                            model=provider["model"],
                            messages=local_msgs,
                            tools=tools,
                            **({"tool_choice": tool_choice} if tool_choice else {}),
                            max_tokens=max_tokens,
                            temperature=temperature,
                            stream=True,
                            stream_options={"include_usage": True},
                        )
                    except Exception as se:
                        content = self.chat_with_tools(
                            messages=local_msgs,
                            tools=tools,
                            functions_map=functions_map,
                            tool_choice=tool_choice,
                            max_rounds=max_rounds - round_i,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            trace_id=trace_id,
                        )
                        if content:
                            yield {"type": "delta", "text": content}
                        return

                    round_text_parts: List[str] = []
                    call_order: List[str] = []
                    call_specs: Dict[str, Dict[str, Any]] = {}

                    for event in stream:
                        try:
                            usage = getattr(event, "usage", None)
                            if usage:
                                handler.capture_usage(event, provider["name"], provider["model"])
                            choices = getattr(event, "choices", None) or []
                            if not choices:
                                continue
                            delta = getattr(choices[0], "delta", None)
                            if not delta:
                                continue
                            text = getattr(delta, "content", None)
                            if text:
                                round_text_parts.append(text)
                                yield {"type": "delta", "text": text}
                            tcd_list = getattr(delta, "tool_calls", None) or []
                            for tcd in tcd_list:
                                try:
                                    cid = getattr(tcd, "id", None) or getattr(tcd, "index", None) or f"call_{len(call_order)}"
                                    fn = getattr(getattr(tcd, "function", None), "name", None)
                                    arg_delta = getattr(getattr(tcd, "function", None), "arguments", None) or ""
                                    spec = call_specs.get(cid) or {"id": cid, "function": {"name": None, "arguments": ""}}
                                    if fn and not spec["function"]["name"]:
                                        spec["function"]["name"] = fn
                                        yield {"type": "tool_call", "name": fn, "status": "start"}
                                        call_order.append(cid)
                                    if arg_delta:
                                        spec["function"]["arguments"] = spec["function"].get("arguments", "") + arg_delta
                                    call_specs[cid] = spec
                                except Exception:
                                    continue
                        except Exception:
                            continue

                    assistant_msg: Dict[str, Any] = {"role": "assistant"}
                    if round_text_parts:
                        assistant_msg["content"] = "".join(round_text_parts)

                    if call_order:
                        normalized_calls: List[Dict[str, Any]] = []
                        for cid in call_order:
                            spec = call_specs.get(cid) or {"id": cid, "function": {"name": None, "arguments": ""}}
                            fn_name = (spec.get("function") or {}).get("name")
                            raw_args = (spec.get("function") or {}).get("arguments") or "{}"
                            normalized_calls.append({"id": cid, "type": "function", "function": {"name": fn_name, "arguments": raw_args}})
                        assistant_msg["tool_calls"] = normalized_calls
                        local_msgs.append(assistant_msg)

                        for tc in normalized_calls:
                            fn_name = (tc.get("function") or {}).get("name")
                            raw_args = (tc.get("function") or {}).get("arguments") or "{}"
                            call_id = tc.get("id") or "tool_call"

                            result = handler.executor.execute_tool_call(fn_name, raw_args, functions_map, tools_used, trace_id)

                            try:
                                if fn_name:
                                    yield {"type": "tool_call", "name": fn_name, "status": "end"}
                            except Exception:
                                pass

                            content_str = handler.executor.serialize_tool_result(result)
                            local_msgs.append({
                                "role": "tool",
                                "tool_call_id": call_id,
                                "name": fn_name,
                                "content": content_str,
                            })
                        continue

                    try:
                        if tools_used:
                            handler.last_usage = {**(handler.last_usage or {}), "tools_used": tools_used}
                    except Exception:
                        pass
                    self.last_usage = handler.last_usage
                    self._set_active_provider(idx)
                    return

                try:
                    if tools_used:
                        handler.last_usage = {**(handler.last_usage or {}), "tools_used": tools_used}
                except Exception:
                    pass
                self.last_usage = handler.last_usage
                self._set_active_provider(idx)
                return
            except Exception as exc:
                last_error = exc
                error_type = type(exc).__name__
                self._log.warning("Provider %s failed for tool stream (%s): %s", provider["name"], error_type, exc)
                continue

        error_msg = f"All LLM providers failed for streaming tool calls. Last error: {last_error or 'no provider succeeded'}"
        self._log.error(error_msg)
        raise RuntimeError(error_msg)


_llm_client_cache: Optional[LLMClient] = None
_llm_client_lock_: Any = None


def get_llm_client(model: Optional[str] = None) -> LLMClient:
    global _llm_client_cache
    try:
        use_langchain = (os.getenv("USE_LANGCHAIN") or "").strip().lower() in ("1", "true", "yes", "on")
        LangChainLLM = None
        if use_langchain:
            try:
                from .langchain_integration import LangChainLLMClient as _LCn                LangChainLLM = _LC
            except Exception as e:
                logging.getLogger("core.agents.llm").error("LangChain wrapper unavailable: %s", e)
                use_langchain = False

        if model:
            key = (os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
            if not key:
                logging.getLogger("core.agents.llm").error("No API key found for custom model: %s", model)
                raise RuntimeError("No API key configured for LLM client")
            base = None
            if key and (os.getenv("OPENROUTER_API_KEY") or "").strip() == key:
                base = (os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1").strip()
            elif key and (os.getenv("GEMINI_API_KEY") or "").strip() == key:
                base = (os.getenv("GEMINI_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta/openai/").strip()
            if use_langchain and LangChainLLM is not None:
                lc = LangChainLLM(api_key=key, base_url=base, model=model)
                if getattr(lc, "is_available", lambda: False)():
                    return lc
                logging.getLogger("core.agents.llm").error("LLM client unavailable: %s", getattr(lc, "unavailable_reason", lambda: None)())
            client = LLMClient(api_key=key, base_url=base, model=model)
            if not client.is_available():
                raise RuntimeError(f"LLM client initialization failed: {client.unavailable_reason()}")
            return client

        if os.getenv("PYTEST_CURRENT_TEST") is not None:
            if use_langchain and LangChainLLM is not None:
                lc = LangChainLLM()
                if getattr(lc, "is_available", lambda: False)():
                    return lc
                logging.getLogger("core.agents.llm").error("LLM client unavailable: %s", getattr(lc, "unavailable_reason", lambda: None)())
            client = LLMClient()
            if not client.is_available():
                logging.getLogger("core.agents.llm").error("LLM client unavailable: %s", client.unavailable_reason())
            return client

        if _llm_client_cache is None:
            if use_langchain and LangChainLLM is not None:
                lc = LangChainLLM()
                if getattr(lc, "is_available", lambda: False)():
                    _llm_client_cache = lc
                else:
                    logging.getLogger("core.agents.llm").error("LLM client unavailable: %s", getattr(lc, "unavailable_reason", lambda: None)())
                    _llm_client_cache = LLMClient()
            else:
                _llm_client_cache = LLMClient()
            if not getattr(_llm_client_cache, "is_available", lambda: False)():
                logging.getLogger("core.agents.llm").error("LLM client unavailable: %s", getattr(_llm_client_cache, "unavailable_reason", lambda: None)())
        return _llm_client_cache
    except Exception as e:
        logging.getLogger("core.agents.llm").error("Failed to get LLM client: %s", e)
        raise

