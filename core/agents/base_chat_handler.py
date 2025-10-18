from __future__ import annotations

from typing import Any, Dict, List, Optional, Callable
from .chat_executor import ChatExecutor


class BaseChatHandler:
    def __init__(self, providers: List[Dict[str, Any]], active_index: Optional[int], log, last_usage: Dict[str, Any]):
        self._providers = providers
        self._active_index = active_index
        self._log = log
        self.last_usage = last_usage
        self.executor = ChatExecutor(log)

    def provider_indices(self) -> List[int]:
        if not self._providers:
            return []
        order: List[int] = []
        if self._active_index is not None:
            order.append(self._active_index)
        order.extend(idx for idx in range(len(self._providers)) if idx != self._active_index)
        return order

    def capture_usage(self, resp: Any, provider_name: str, provider_model: str) -> None:
        try:
            usage = getattr(resp, "usage", None)
            if usage:
                self.last_usage = {
                    "provider": provider_name,
                    "model": provider_model,
                    "prompt_tokens": getattr(usage, "prompt_tokens", None),
                    "completion_tokens": getattr(usage, "completion_tokens", None),
                    "total_tokens": getattr(usage, "total_tokens", None),
                }
        except Exception:
            pass

    def execute_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        operation_name: str
    ) -> tuple[str, int]:
        if not self._providers:
            raise RuntimeError("LLM client unavailable (missing key or package)")

        last_error: Optional[Exception] = None
        for idx in self.provider_indices():
            provider = self._providers[idx]
            try:
                self._log.debug(
                    "Sending %s | provider=%s model=%s msgs=%d max_tokens=%d temp=%.2f",
                    operation_name,
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
                if not resp or not resp.choices:
                    raise RuntimeError("Empty response from LLM")

                choice = resp.choices[0]
                raw_content = choice.message.content
                finish_reason = getattr(choice, "finish_reason", None)

                self._log.debug(
                    "Raw response content: %r (type=%s, finish_reason=%s)",
                    raw_content,
                    type(raw_content).__name__,
                    finish_reason
                )

                content = (raw_content or "").strip()
                if not content:
                    self._log.warning(
                        "LLM returned empty content for provider %s (finish_reason=%s)",
                        provider["name"],
                        finish_reason
                    )

                self.capture_usage(resp, provider["name"], provider["model"])
                return content, idx
            except Exception as exc:
                last_error = exc
                error_type = type(exc).__name__
                self._log.warning("Provider %s failed for %s (%s): %s", provider["name"], operation_name, error_type, exc)
                continue

        error_msg = f"All LLM providers failed for {operation_name}. Last error: {last_error or 'no provider succeeded'}"
        self._log.error(error_msg)
        raise RuntimeError(error_msg)

    def execute_chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        functions_map: Dict[str, Callable[..., Any]],
        tool_choice: Optional[str],
        max_rounds: int,
        max_tokens: int,
        temperature: float,
        trace_id: Optional[str],
    ) -> tuple[str, int, List[str]]:
        if not self._providers:
            raise RuntimeError("LLM client unavailable (missing key or package)")

        last_error: Optional[Exception] = None
        for idx in self.provider_indices():
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
                    self.capture_usage(resp, provider["name"], provider["model"])

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
                        return (content or "").strip(), idx, tools_used

                    for tc in assistant_msg["tool_calls"]:
                        fn_name = tc.get("function", {}).get("name")
                        raw_args = tc.get("function", {}).get("arguments") or "{}"
                        call_id = tc.get("id") or "tool_call"

                        result = self.executor.execute_tool_call(fn_name, raw_args, functions_map, tools_used, trace_id)
                        content_str = self.executor.serialize_tool_result(result)

                        local_msgs.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": fn_name,
                            "content": content_str,
                        })

                return (assistant_msg.get("content") or "").strip(), idx, tools_used
            except Exception as exc:
                last_error = exc
                error_type = type(exc).__name__
                self._log.warning("Provider %s failed for tool call (%s): %s", provider["name"], error_type, exc)
                continue

        error_msg = f"All LLM providers failed for tool calling. Last error: {last_error or 'no provider succeeded'}"
        self._log.error(error_msg)
        raise RuntimeError(error_msg)
