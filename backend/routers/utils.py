from typing import Any, Dict, List, Optional
from core.chat_db import get_thread_messages, get_latest_summary, Message as ChatMessage


def default_price_map() -> Dict[str, Dict[str, float]]:
    return {
        "openai:gpt-4o-mini": {"in": 0.005, "out": 0.015},
        "openai:gpt-4o": {"in": 0.01, "out": 0.03},
        "gemini:gemini-2.0-flash": {"in": 0.0005, "out": 0.0015},
        "openrouter:deepseek/deepseek-r1-0528:free": {"in": 0.0, "out": 0.0},
        "openrouter:z-ai/glm-4.5-air:free": {"in": 0.0, "out": 0.0},
    }


def load_price_map() -> Dict[str, Dict[str, float]]:
    import os, json
    raw = os.getenv("LLM_PRICE_MAP")
    if not raw:
        return default_price_map()
    try:
        data = json.loads(raw)
        out: Dict[str, Dict[str, float]] = {}
        for k, v in (data.items() if isinstance(data, dict) else []):
            if isinstance(v, dict) and "in" in v and "out" in v:
                out[str(k)] = {"in": float(v["in"]), "out": float(v["out"])}
        return out or default_price_map()
    except Exception:
        return default_price_map()


def compute_cost_usd(provider: Optional[str], model: Optional[str], token_in: Optional[int], token_out: Optional[int]) -> Optional[str]:
    try:
        if not provider or not model or token_in is None or token_out is None:
            return None
        key = f"{provider}:{model}"
        pm = load_price_map()
        price = pm.get(key) or pm.get(model)
        if not price:
            return None
        cin = (token_in or 0) / 1000.0 * float(price.get("in", 0.0))
        cout = (token_out or 0) / 1000.0 * float(price.get("out", 0.0))
        return f"{cin + cout:.4f}"
    except Exception:
        return None


def derive_agents_from_tools(tools_used: Optional[List[str]]) -> List[str]:
    if not tools_used:
        return []
    mapping = {
        "list_inventory_items": "UserInteractionAgent",
        "get_inventory_item": "UserInteractionAgent",
        "list_pricing_list": "PriceOptimizationAgent",
        "list_price_proposals": "PriceOptimizationAgent",
        "list_market_data": "DataCollectorAgent",
        "run_pricing_workflow": "PriceOptimizationAgent",
        "optimize_price": "PriceOptimizationAgent",
        "scan_for_alerts": "AlertNotificationAgent",
        "collect_market_data": "DataCollectorAgent",
        "request_market_fetch": "DataCollectorAgent",
    }
    agents: List[str] = []
    for t in tools_used:
        name = mapping.get(t)
        if name and name not in agents:
            agents.append(name)
    return agents


def env_int(name: str, default: int) -> int:
    try:
        import os
        return int(os.getenv(name, str(default)) or default)
    except Exception:
        return default


def env_float(name: str, default: float) -> float:
    try:
        import os
        return float(os.getenv(name, str(default)) or default)
    except Exception:
        return default


def assemble_memory(thread_id: int) -> List[Dict[str, str]]:
    msgs = get_thread_messages(thread_id)
    mem: List[Dict[str, str]] = []

    max_msgs = env_int("UI_HISTORY_MAX_MSGS", 200)
    tail_after_summary = env_int("UI_HISTORY_TAIL_AFTER_SUMMARY", 12)

    latest = get_latest_summary(thread_id)
    cutoff_id = 0
    if latest and latest.content:
        mem.append({
            "role": "system",
            "content": f"Conversation summary up to message {latest.upto_message_id}:\n" + str(latest.content)
        })
        cutoff_id = int(latest.upto_message_id or 0)

    tail: List[ChatMessage] = [m for m in msgs if m.id > cutoff_id and m.role in ("system", "user", "assistant")]
    cap = max_msgs if cutoff_id == 0 else tail_after_summary
    for m in tail[-cap:]:
        mem.append({"role": m.role, "content": m.content})

    if not mem:
        for m in msgs[-max_msgs:]:
            if m.role in ("system", "user", "assistant"):
                mem.append({"role": m.role, "content": m.content})

    return mem


def should_summarize(thread_id: int, upto_message_id: int, token_in: Optional[int], token_out: Optional[int]) -> bool:
    import random
    msgs = get_thread_messages(thread_id)
    latest = get_latest_summary(thread_id)
    since = [m for m in msgs if m.id <= upto_message_id and (latest is None or m.id > int(latest.upto_message_id))]

    min_msgs = env_int("UI_SUMMARIZE_AFTER_MSGS", 12)
    long_thread = env_int("UI_LONG_THREAD_MSGS", 20)
    prob = env_float("UI_SUMMARIZE_PROB", 0.25)
    token_trigger = env_int("UI_SUMMARIZE_TOKEN_TRIGGER", 2000)

    if len(since) >= min_msgs:
        return True
    if (token_in or 0) + (token_out or 0) >= token_trigger:
        return True
    if len(msgs) >= long_thread and random.random() < prob:
        return True
    return False


def generate_summary(thread_id: int, upto_message_id: int) -> Optional[str]:
    try:
        from core.agents.llm_client import get_llm_client
    except Exception:
        get_llm_client = None

    msgs = get_thread_messages(thread_id)
    latest = get_latest_summary(thread_id)
    start_id = int(latest.upto_message_id) if latest else 0
    segment = [m for m in msgs if m.id > start_id and m.id <= upto_message_id]
    if len(segment) < 4:
        return None

    lines: List[str] = []
    for m in segment[-50:]:
        role = m.role
        text = m.content.replace("\n", " ")
        if len(text) > 400:
            text = text[:400] + "..."
        lines.append(f"{role}: {text}")
    transcript = "\n".join(lines)

    if get_llm_client is None:
        return None
    try:
        import os as _os
        summary_model = _os.getenv("SUMMARIZER_MODEL")
        llm = get_llm_client(model=summary_model) if summary_model else get_llm_client()
        if not llm.is_available():
            return None
        system = (
            "You are a helpful assistant creating a rolling, concise conversation summary. "
            "Write 5-8 bullet points capturing key decisions, requests, tool results, and context. "
            "Keep it factual and under 180 words."
        )
        prompt = (
            "Summarize the following chat segment to help future turns continue without full history.\n\n" + transcript
        )
        content = llm.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ], max_tokens=220, temperature=0.2)
        return content
    except Exception:
        return None
