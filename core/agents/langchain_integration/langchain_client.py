from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Iterator
import logging
import json

try:
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except Exception:
    LANGCHAIN_AVAILABLE = False


class LangChainLLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self._log = logging.getLogger("core.agents.llm")
        self._provider = "langchain"
        self.model = model or "gpt-4o-mini"
        self._unavailable_reason: Optional[str] = None
        self.last_usage: Dict[str, Any] = {}
        self._clients: List[Dict[str, Any]] = []

        if not LANGCHAIN_AVAILABLE:
            self._unavailable_reason = "langchain packages not installed"
            return

        try:
            client = ChatOpenAI(
                model=self.model,
                api_key=api_key,
                base_url=base_url,
                streaming=False,
            )
            self._clients.append({"name": "openai", "client": client, "model": self.model})
        except Exception as e:
            self._unavailable_reason = f"failed to init LangChain client: {e}"

    def is_available(self) -> bool:
        return LANGCHAIN_AVAILABLE and bool(self._clients)

    def provider(self) -> str:
        return self._provider

    def unavailable_reason(self) -> Optional[str]:
        return self._unavailable_reason

    def _to_lc_messages(self, messages: List[Dict[str, Any]]):
        lc_msgs = []
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if role == "system":
                lc_msgs.append(SystemMessage(content=content or ""))
            elif role == "assistant":
                tool_calls = m.get("tool_calls")
                if tool_calls:
                    lc_msgs.append(AIMessage(content=content or "", additional_kwargs={"tool_calls": tool_calls}))
                else:
                    lc_msgs.append(AIMessage(content=content or ""))
            elif role == "tool":
                tool_call_id = m.get("tool_call_id") or m.get("id") or "tool_call"
                name = m.get("name")
                lc_msgs.append(ToolMessage(content=content or "", tool_call_id=tool_call_id, name=name))
            else:
                lc_msgs.append(HumanMessage(content=content or ""))
        return lc_msgs

    def _capture_usage(self, msg: Any, provider_name: str, model: str) -> None:
        try:
            usage = getattr(msg, "usage_metadata", None) or getattr(msg, "response_metadata", {}).get("token_usage")
            if not usage:
                return
            inp = usage.get("input_tokens") or usage.get("prompt_tokens")
            out = usage.get("output_tokens") or usage.get("completion_tokens")
            tot = usage.get("total_tokens") or (inp or 0) + (out or 0)
            self.last_usage = {"prompt_tokens": inp or 0, "completion_tokens": out or 0, "total_tokens": tot or 0, "provider": provider_name, "model": model}
        except Exception:
            pass

    def chat(self, messages: List[Dict[str, Any]], max_tokens: int = 256, temperature: float = 0.2) -> str:
        if not self.is_available():
            raise RuntimeError(f"LLM client unavailable: {self._unavailable_reason}")
        client = self._clients[0]["client"]
        lc_msgs = self._to_lc_messages(messages)
        try:
            resp = client.invoke(lc_msgs, config={"max_tokens": max_tokens, "temperature": temperature})
            self._capture_usage(resp, self._clients[0]["name"], self._clients[0]["model"])
        except Exception as e:
            raise RuntimeError(f"LangChain chat failed: {e}")
        text = getattr(resp, "content", "") or ""
        return text.strip()

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 256,
        temperature: float = 0.2,
    ) -> Iterator[str]:
        if not self.is_available():
            raise RuntimeError(f"LLM client unavailable: {self._unavailable_reason}")
        client = self._clients[0]["client"].bind(streaming=True)
        lc_msgs = self._to_lc_messages(messages)
        try:
            last_chunk = None
            for chunk in client.stream(lc_msgs, config={"max_tokens": max_tokens, "temperature": temperature}):
                try:
                    txt = getattr(chunk, "content", None)
                    if txt:
                        yield txt
                    last_chunk = chunk
                except Exception:
                    continue
            if last_chunk is not None:
                self._capture_usage(last_chunk, self._clients[0]["name"], self._clients[0]["model"])
        except Exception:
            yield self.chat(messages, max_tokens=max_tokens, temperature=temperature)

    def _normalize_tool_calls(self, tool_calls: Any) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        try:
            for tc in tool_calls or []:
                fid = getattr(tc, "id", None) or (tc.get("id") if isinstance(tc, dict) else None) or "call_0"
                fn = None
                args = None
                if isinstance(tc, dict):
                    f = tc.get("function") or {}
                    fn = f.get("name")
                    args = f.get("arguments")
                else:
                    f = getattr(tc, "function", None)
                    fn = getattr(f, "name", None)
                    args = getattr(f, "arguments", None)
                out.append({"id": fid, "type": "function", "function": {"name": fn, "arguments": args or "{}"}})
        except Exception:
            pass
        return out

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
        if not self.is_available():
            raise RuntimeError(f"LLM client unavailable: {self._unavailable_reason}")
        client = self._clients[0]["client"]
        local_msgs = list(messages)
        for _ in range(max_rounds):
            lc_msgs = self._to_lc_messages(local_msgs)
            try:
                runnable = client.bind(
                    extra_body={
                        "tools": tools or [],
                        **({"tool_choice": tool_choice} if tool_choice else {}),
                    }
                )
                resp = runnable.invoke(
                    lc_msgs,
                    config={"max_tokens": max_tokens, "temperature": temperature},
                )
                self._capture_usage(resp, self._clients[0]["name"], self._clients[0]["model"])
            except Exception as e:
                raise RuntimeError(f"LangChain tool chat failed: {e}")
            tool_calls = None
            try:
                tool_calls = getattr(resp, "additional_kwargs", {}).get("tool_calls")
            except Exception:
                tool_calls = None
            if not tool_calls:
                return (getattr(resp, "content", "") or "").strip()
            normalized = self._normalize_tool_calls(tool_calls)
            assistant_msg: Dict[str, Any] = {"role": "assistant", "content": getattr(resp, "content", None) or ""}
            if normalized:
                assistant_msg["tool_calls"] = normalized
            local_msgs.append(assistant_msg)
            for tc in normalized:
                fn_name = (tc.get("function") or {}).get("name")
                raw_args = (tc.get("function") or {}).get("arguments") or "{}"
                call_id = tc.get("id") or "tool_call"
                parsed_args: Dict[str, Any]
                try:
                    parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                except Exception:
                    parsed_args = {}
                func = functions_map.get(fn_name or "")
                result = None
                if callable(func):
                    try:
                        result = func(**parsed_args) if isinstance(parsed_args, dict) else func(parsed_args)
                    except Exception as e:
                        result = {"error": str(e)}
                content_str = json.dumps(result) if not isinstance(result, str) else result
                local_msgs.append({"role": "tool", "tool_call_id": call_id, "name": fn_name, "content": content_str})
        return ""

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
    ) -> Iterator[Dict[str, Any]]:
        if not self.is_available():
            raise RuntimeError(f"LLM client unavailable: {self._unavailable_reason}")
        client = self._clients[0]["client"].bind(streaming=True)
        local_msgs: List[Dict[str, Any]] = list(messages)
        for _ in range(max_rounds):
            lc_msgs = self._to_lc_messages(local_msgs)
            try:
                runnable = client.bind(
                    extra_body={
                        "tools": tools or [],
                        **({"tool_choice": tool_choice} if tool_choice else {}),
                    }
                )
                stream = runnable.stream(
                    lc_msgs,
                    config={"max_tokens": max_tokens, "temperature": temperature},
                )
            except Exception:
                content = self.chat_with_tools(
                    messages=local_msgs,
                    tools=tools,
                    functions_map=functions_map,
                    tool_choice=tool_choice,
                    max_rounds=1,
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
            last_chunk = None
            for chunk in stream:
                last_chunk = chunk
                try:
                    txt = getattr(chunk, "content", None)
                    if txt:
                        round_text_parts.append(txt)
                        yield {"type": "delta", "text": txt}
                    ak = getattr(chunk, "additional_kwargs", {}) or {}
                    tcd_list = ak.get("tool_calls") or []
                    for tcd in tcd_list:
                        try:
                            cid = getattr(tcd, "id", None) or (tcd.get("id") if isinstance(tcd, dict) else None) or f"call_{len(call_order)}"
                            fn = None
                            arg_delta = None
                            if isinstance(tcd, dict):
                                f = tcd.get("function") or {}
                                fn = f.get("name")
                                arg_delta = f.get("arguments")
                            else:
                                f = getattr(tcd, "function", None)
                                fn = getattr(f, "name", None)
                                arg_delta = getattr(f, "arguments", None)
                            spec = call_specs.get(cid) or {"id": cid, "function": {"name": None, "arguments": ""}}
                            if fn and not spec["function"]["name"]:
                                spec["function"]["name"] = fn
                                yield {"type": "tool_call", "name": fn, "status": "start"}
                                call_order.append(cid)
                            if arg_delta:
                                spec["function"]["arguments"] = (spec["function"].get("arguments", "") or "") + arg_delta
                            call_specs[cid] = spec
                        except Exception:
                            continue
                except Exception:
                    continue
            if last_chunk is not None:
                try:
                    self._capture_usage(last_chunk, self._clients[0]["name"], self._clients[0]["model"])
                except Exception:
                    pass
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
                    try:
                        parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                    except Exception:
                        parsed_args = {}
                    func = functions_map.get(fn_name or "")
                    result = None
                    if callable(func):
                        try:
                            result = func(**parsed_args) if isinstance(parsed_args, dict) else func(parsed_args)
                        except Exception as e:
                            result = {"error": str(e)}
                    try:
                        if fn_name:
                            yield {"type": "tool_call", "name": fn_name, "status": "end"}
                    except Exception:
                        pass
                    content_str = json.dumps(result) if not isinstance(result, str) else result
                    local_msgs.append({"role": "tool", "tool_call_id": call_id, "name": fn_name, "content": content_str})
                continue
            if assistant_msg.get("content"):
                yield {"type": "delta", "text": assistant_msg["content"]}
            return
        return
