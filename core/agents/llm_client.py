"""
Lightweight LLM client wrapper for the Dynamic Pricing AI agents.

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
from datetime import datetime


_GEMINI_WORKING_KEY_CACHE: Optional[str] = None


def _get_gemini_working_key_file() -> Path:
    """Return path to cache file for the last working Gemini key."""
    root = Path(__file__).resolve().parents[2]
    cache_dir = root / ".llm_cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / "gemini_working_key.txt"


def _load_gemini_working_key() -> Optional[str]:
    """Load the last working Gemini key from cache."""
    try:
        cache_file = _get_gemini_working_key_file()
        if cache_file.exists():
            key = cache_file.read_text(encoding="utf-8").strip()
            return key if key else None
    except Exception:
        pass
    return None


def _save_gemini_working_key(key: str) -> None:
    """Save the working Gemini key to cache."""
    try:
        cache_file = _get_gemini_working_key_file()
        cache_file.write_text(key, encoding="utf-8")
    except Exception:
        pass


def _load_dotenv_if_present() -> None:
    """Minimal .env loader from project root if env vars not already present."""
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
                if k and not os.getenv(k):
                    os.environ[k] = v
    except Exception as e:
        # Best-effort; log and continue
        logging.getLogger("core.agents.llm").debug("dotenv load skipped due to error: %s", e)
        pass


class LLMClient:
    """Tiny wrapper around OpenAI-compatible SDKs with multi-provider fallback."""

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

        def _prepare_headers(provider_name: str, key: str) -> Dict[str, str]:
            if provider_name == "openrouter":
                return {
                    "HTTP-Referer": os.getenv("OPENROUTER_REFERRER", "https://dynamic-pricing-ai.local"),
                    "X-Title": os.getenv("OPENROUTER_TITLE", "Dynamic Pricing AI"),
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
                    "api_key": provider_api_key,
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

         gemini_base = os.getenv("GEMINI_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta/openai/"
        if gemini_base and not gemini_base.endswith("/"):
            gemini_base = gemini_base + "/"
        gemini_model = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        
        gemini_keys = []
        gemini_key_1 = os.getenv("GEMINI_API_KEY")
        if gemini_key_1:
            gemini_keys.append(("gemini", gemini_key_1))
        gemini_key_2 = os.getenv("GEMINI_API_KEY_2")
        if gemini_key_2:
            gemini_keys.append(("gemini_2", gemini_key_2))
        gemini_key_3 = os.getenv("GEMINI_API_KEY_3")
        if gemini_key_3:
            gemini_keys.append(("gemini_3", gemini_key_3))
        
        working_gemini_key = _load_gemini_working_key()
        if working_gemini_key and any(key == working_gemini_key for _, key in gemini_keys):
            gemini_keys.sort(key=lambda x: (x[1] != working_gemini_key, gemini_keys.index(x)))

        # Registration priority: explicit args > OpenRouter > OpenAI > Gemini(s)
        if explicit_key:
            custom_model = explicit_model or or_model or oa_model or gemini_model
            _register_provider("custom", explicit_key, custom_model, explicit_base)
        else:
            _register_provider("openrouter", or_key, or_model, or_base)
            _register_provider("openai", oa_key, oa_model, None)
            for gemini_name, gemini_key in gemini_keys:
                _register_provider(gemini_name, gemini_key, gemini_model, gemini_base)

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
        
        if self._provider.startswith("gemini"):
            api_key = provider.get("api_key")
            if api_key:
                _save_gemini_working_key(api_key)
        
        prior = self.last_usage or {}
        self.last_usage = {**prior, "provider": self._provider, "model": self.model}

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
                # capture usage metadata if available
                try:
                    usage = getattr(resp, "usage", None)
                    if usage:
                        self.last_usage = {
                            "provider": provider["name"],
                            "model": provider["model"],
                            "prompt_tokens": getattr(usage, "prompt_tokens", None),
                            "completion_tokens": getattr(usage, "completion_tokens", None),
                            "total_tokens": getattr(usage, "total_tokens", None),
                        }
                except Exception:
                    pass
                self._set_active_provider(idx)
                self._log.debug("LLM response chars=%d", len(content))
                return content
            except Exception as exc:
                last_error = exc
                self._log.warning("Provider %s failed for chat: %s", provider["name"], exc)
                continue

        raise RuntimeError(f"LLM error: {last_error or 'no provider succeeded'}")

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 256,
        temperature: float = 0.2,
    ):
        """Yield content chunks from a streaming chat completion.
        Falls back to non-streaming single-shot if streaming fails.
        Updates self.last_usage at the end if usage is provided by the SDK.
        """
        if not self._providers:
            raise RuntimeError("LLM client unavailable (missing key or package)")

        last_error: Optional[Exception] = None
        for idx in self._provider_indices():
            provider = self._providers[idx]
            try:
                # Try streaming first
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
                            # usage (final chunk)
                            usage = getattr(event, "usage", None)
                            if usage:
                                try:
                                    self.last_usage = {
                                        "provider": provider["name"],
                                        "model": provider["model"],
                                        "prompt_tokens": getattr(usage, "prompt_tokens", None),
                                        "completion_tokens": getattr(usage, "completion_tokens", None),
                                        "total_tokens": getattr(usage, "total_tokens", None),
                                    }
                                except Exception:
                                    pass
                            # token delta
                            choices = getattr(event, "choices", None) or []
                            if choices:
                                delta = getattr(choices[0], "delta", None)
                                if delta is not None:
                                    text = getattr(delta, "content", None)
                                    if text:
                                        full.append(text)
                                        yield text
                        except Exception:
                            # Ignore malformed events
                            continue
                    # finalize provider
                    self._set_active_provider(idx)
                    return
                except Exception as se:
                    self._log.debug("Streaming not available for %s: %s", provider["name"], se)
                    # Fallback to non-streaming
                    content = self.chat(messages, max_tokens=max_tokens, temperature=temperature)
                    yield content
                    self._set_active_provider(idx)
                    return
            except Exception as exc:
                last_error = exc
                self._log.warning("Provider %s failed for stream: %s", provider["name"], exc)
                continue
        raise RuntimeError(f"LLM stream error: {last_error or 'no provider succeeded'}")

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
                tools_used: List[str] = []
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
                    # capture usage per round if available
                    try:
                        usage = getattr(resp, "usage", None)
                        if usage:
                            self.last_usage = {
                                "provider": provider["name"],
                                "model": provider["model"],
                                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                                "completion_tokens": getattr(usage, "completion_tokens", None),
                                "total_tokens": getattr(usage, "total_tokens", None),
                            }
                    except Exception:
                        pass

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
                        # record tools_used if present
                        try:
                            tools_used = []
                            try:
                                if assistant_msg.get("tool_calls"):
                                    for tc in assistant_msg["tool_calls"]:
                                        fn = (tc.get("function") or {}).get("name")
                                        if fn and fn not in tools_used:
                                            tools_used.append(fn)
                            except Exception:
                                pass
                            if tools_used:
                                self.last_usage = {**(self.last_usage or {}), "tools_used": tools_used}
                        except Exception:
                            pass
                        self._set_active_provider(idx)
                        return (content or "").strip()

                    for tc in assistant_msg["tool_calls"]:
                        fn_name = tc.get("function", {}).get("name")
                        raw_args = tc.get("function", {}).get("arguments") or "{}"
                        call_id = tc.get("id") or "tool_call"
                        try:
                            if fn_name and fn_name not in tools_used:
                                tools_used.append(fn_name)
                        except Exception:
                            pass
                        try:
                            args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                        except Exception:
                            args = {}
                        
                        # Log tool call start
                        tool_start_time = datetime.now()
                        try:
                            if trace_id:
                                self._log.debug(f"Tool call start: {fn_name} with trace_id {trace_id}")
                        except Exception:
                            pass
                        
                        result: Any
                        error_occurred = False
                        if fn_name in functions_map:
                            try:
                                result = functions_map[fn_name](**args)
                            except TypeError:
                                result = functions_map[fn_name](args)
                            except Exception as tool_exc:
                                result = {"error": str(tool_exc)}
                                error_occurred = True
                        else:
                            result = {"error": f"unknown tool: {fn_name}"}
                            error_occurred = True

                        # Log tool call completion
                        try:
                            if trace_id:
                                duration_ms = int((datetime.now() - tool_start_time).total_seconds() * 1000)
                                status = "failed" if error_occurred else "completed"
                                self._log.debug(f"Tool call {status}: {fn_name} duration={duration_ms}ms")
                        except Exception:
                            pass

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
                # record tools_used
                try:
                    self.last_usage = {**(self.last_usage or {}), "tools_used": tools_used}
                except Exception:
                    pass
                return (assistant_msg.get("content") or "").strip()
            except Exception as exc:
                last_error = exc
                self._log.warning("Provider %s failed for tool call: %s", provider["name"], exc)
                continue

        raise RuntimeError(f"LLM tools error: {last_error or 'no provider succeeded'}")

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
        """Streaming tool-calling loop.

        Yields dict events and text deltas interleaved:
        - {"type":"delta", "text": str}
        - {"type":"tool_call", "name": str, "status": "start"|"end"}

        Strategy per round:
        1) Stream assistant message with potential tool_calls; emit content deltas + capture tool call specs.
        2) If tool_calls present, execute mapped Python functions, emit tool_call end, append tool outputs, then continue to next round.
        3) If no tool_calls, finish.
        """
        if not self._providers:
            raise RuntimeError("LLM client unavailable (missing key or package)")

        last_error: Optional[Exception] = None
        tools_used: List[str] = []

        for idx in self._provider_indices():
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
                        # Fallback to non-streaming tool loop
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
                        self._set_active_provider(idx)
                        return

                    # Accumulate per-round deltas and tool call specs
                    round_text_parts: List[str] = []
                    call_order: List[str] = []
                    call_specs: Dict[str, Dict[str, Any]] = {}

                    for event in stream:
                        try:
                            # usage (final chunk)
                            usage = getattr(event, "usage", None)
                            if usage:
                                try:
                                    self.last_usage = {
                                        "provider": provider["name"],
                                        "model": provider["model"],
                                        "prompt_tokens": getattr(usage, "prompt_tokens", None),
                                        "completion_tokens": getattr(usage, "completion_tokens", None),
                                        "total_tokens": getattr(usage, "total_tokens", None),
                                    }
                                except Exception:
                                    pass
                            choices = getattr(event, "choices", None) or []
                            if not choices:
                                continue
                            delta = getattr(choices[0], "delta", None)
                            if not delta:
                                continue
                            # content delta
                            text = getattr(delta, "content", None)
                            if text:
                                round_text_parts.append(text)
                                yield {"type": "delta", "text": text}
                            # tool call deltas
                            tcd_list = getattr(delta, "tool_calls", None) or []
                            for tcd in tcd_list:
                                try:
                                    cid = getattr(tcd, "id", None) or getattr(tcd, "index", None) or f"call_{len(call_order)}"
                                    fn = getattr(getattr(tcd, "function", None), "name", None)
                                    arg_delta = getattr(getattr(tcd, "function", None), "arguments", None) or ""
                                    spec = call_specs.get(cid) or {"id": cid, "function": {"name": None, "arguments": ""}}
                                    if fn and not spec["function"]["name"]:
                                        spec["function"]["name"] = fn
                                        # first time we see this tool name => emit start
                                        yield {"type": "tool_call", "name": fn, "status": "start"}
                                        call_order.append(cid)
                                    if arg_delta:
                                        spec["function"]["arguments"] = spec["function"].get("arguments", "") + arg_delta
                                    call_specs[cid] = spec
                                except Exception:
                                    continue
                        except Exception:
                            continue

                    # Build assistant message for this round
                    assistant_msg: Dict[str, Any] = {"role": "assistant"}
                    if round_text_parts:
                        assistant_msg["content"] = "".join(round_text_parts)

                    # If tool calls present, execute and continue
                    if call_order:
                        normalized_calls: List[Dict[str, Any]] = []
                        for cid in call_order:
                            spec = call_specs.get(cid) or {"id": cid, "function": {"name": None, "arguments": ""}}
                            fn_name = (spec.get("function") or {}).get("name")
                            raw_args = (spec.get("function") or {}).get("arguments") or "{}"
                            normalized_calls.append({"id": cid, "type": "function", "function": {"name": fn_name, "arguments": raw_args}})
                        assistant_msg["tool_calls"] = normalized_calls
                        local_msgs.append(assistant_msg)

                        # Execute each call
                        for tc in normalized_calls:
                            fn_name = (tc.get("function") or {}).get("name")
                            raw_args = (tc.get("function") or {}).get("arguments") or "{}"
                            call_id = tc.get("id") or "tool_call"
                            try:
                                if fn_name and fn_name not in tools_used:
                                    tools_used.append(fn_name)
                            except Exception:
                                pass
                            try:
                                args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                            except Exception:
                                args = {}

                            tool_start_time = datetime.now()
                            result: Any
                            error_occurred = False
                            if fn_name in functions_map:
                                try:
                                    result = functions_map[fn_name](**args)
                                except TypeError:
                                    result = functions_map[fn_name](args)
                                except Exception as tool_exc:
                                    result = {"error": str(tool_exc)}
                                    error_occurred = True
                            else:
                                result = {"error": f"unknown tool: {fn_name}"}
                                error_occurred = True

                            try:
                                duration_ms = int((datetime.now() - tool_start_time).total_seconds() * 1000)
                                self._log.debug("tool %s finished in %dms (error=%s)", fn_name, duration_ms, error_occurred)
                            except Exception:
                                pass

                            # Emit end event for tool
                            try:
                                if fn_name:
                                    yield {"type": "tool_call", "name": fn_name, "status": "end"}
                            except Exception:
                                pass

                            try:
                                content_str = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
                            except Exception:
                                content_str = str(result)

                            local_msgs.append({
                                "role": "tool",
                                "tool_call_id": call_id,
                                "name": fn_name,
                                "content": content_str,
                            })
                        # continue to next round
                        continue

                    # No tool calls => finalize
                    try:
                        if tools_used:
                            self.last_usage = {**(self.last_usage or {}), "tools_used": tools_used}
                    except Exception:
                        pass
                    self._set_active_provider(idx)
                    return

                # max rounds exhausted
                try:
                    if tools_used:
                        self.last_usage = {**(self.last_usage or {}), "tools_used": tools_used}
                except Exception:
                    pass
                self._set_active_provider(idx)
                return
            except Exception as exc:
                last_error = exc
                self._log.warning("Provider %s failed for tool stream: %s", provider["name"], exc)
                continue

        raise RuntimeError(f"LLM tools stream error: {last_error or 'no provider succeeded'}")


def get_llm_client(model: Optional[str] = None) -> LLMClient:
    """Return an LLM client. If `model` is provided, prefer it as the default
    model for the first available provider by inserting a higher-priority
    provider entry with the same credentials when possible.

    Notes:
    - This lightweight override leverages OPENAI_API_KEY if set; otherwise falls back
      to existing provider resolution. It avoids duplicating full provider routing
      logic elsewhere.
    """
    # If a specific model is requested, try constructing a client with the same
    # keys but preferring that model by passing it through the constructor.
    # The constructor already respects explicit args as highest priority.
    if model:
        # Try OpenAI explicit if key present; else default flow
        key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY")
        base = None
        if key and os.getenv("OPENROUTER_API_KEY") == key:
            base = os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"
        elif key and os.getenv("GEMINI_API_KEY") == key:
            base = os.getenv("GEMINI_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta/openai/"
        return LLMClient(api_key=key, base_url=base, model=model)
    return LLMClient()
