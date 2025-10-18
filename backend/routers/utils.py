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
    import hashlib
    msgs = get_thread_messages(thread_id)
    latest = get_latest_summary(thread_id)
    since = [m for m in msgs if m.id <= upto_message_id and (latest is None or m.id > int(latest.upto_message_id))]

    min_msgs = env_int("UI_SUMMARIZE_AFTER_MSGS", 12)
    long_thread = env_int("UI_LONG_THREAD_MSGS", 20)
    prob = env_float("UI_SUMMARIZE_PROB", 0.25)
    token_trigger = env_int("UI_SUMMARIZE_TOKEN_TRIGGER", 2000)

    if len(since) >= min_msgs:
        return True
    
    accumulated_tokens = sum((m.token_in or 0) + (m.token_out or 0) for m in since)
    if accumulated_tokens >= token_trigger:
        return True
    
    if len(msgs) >= long_thread:
        seed = int(hashlib.md5(f"{thread_id}:{upto_message_id}".encode()).hexdigest()[:8], 16)
        if (seed % 10000) / 10000.0 < prob:
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


def safe_add_summary(thread_id: int, upto_message_id: int, content: str) -> bool:
    from core.chat_db import add_summary, get_message, get_latest_summary
    from sqlalchemy.exc import IntegrityError
    import logging
    
    logger = logging.getLogger(__name__)
    
    msg = get_message(upto_message_id)
    if not msg or msg.thread_id != thread_id:
        logger.warning(f"Invalid upto_message_id {upto_message_id} for thread {thread_id}")
        return False
    
    latest = get_latest_summary(thread_id)
    if latest and int(latest.upto_message_id) >= upto_message_id:
        logger.warning(f"Summary {upto_message_id} <= latest {latest.upto_message_id} for thread {thread_id}")
        return False
    
    try:
        add_summary(thread_id, upto_message_id, content)
        return True
    except IntegrityError as e:
        logger.warning(f"Duplicate summary prevented for thread {thread_id}, message {upto_message_id}: {e}")
        return False


def count_user_messages_since(thread_id: int, since_message_id: Optional[int] = None) -> int:
    msgs = get_thread_messages(thread_id)
    if since_message_id is not None:
        msgs = [m for m in msgs if m.id > since_message_id]
    return len([m for m in msgs if m.role == "user"])


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) // 0.75)


def should_auto_rename_thread(thread_id: int) -> bool:
    msgs = get_thread_messages(thread_id)
    user_count = len([m for m in msgs if m.role == "user"])
    rename_threshold = env_int("UI_THREAD_RENAME_THRESHOLD", 5)
    return user_count >= rename_threshold


def get_last_rename_message_id(thread_id: int) -> Optional[int]:
    try:
        from core.agents.llm_client import get_llm_client
        msgs = get_thread_messages(thread_id)
        if len(msgs) < 2:
            return None
        latest_msg = max((m.id for m in msgs if m.role == "assistant"), default=None)
        return latest_msg
    except Exception:
        return None


def summarize_assistant_response(content: str) -> str:
    lines = content.split("\n")
    summary_lines = []
    for line in lines:
        line = line.strip()
        if len(line) > 150:
            line = line[:150] + "..."
        if line:
            summary_lines.append(line)
    return "\n".join(summary_lines[:8])


def generate_thread_title(thread_id: int) -> Optional[str]:
    try:
        from core.agents.llm_client import get_llm_client
    except Exception:
        return None

    msgs = get_thread_messages(thread_id)
    if len(msgs) < 2:
        return None

    user_msgs = [m for m in msgs if m.role == "user"]
    assistant_msgs = [m for m in msgs if m.role == "assistant"]

    if not user_msgs:
        return None

    context_parts: List[str] = []
    context_parts.append("User queries:")
    for um in user_msgs[-5:]:
        text = um.content.replace("\n", " ").strip()
        if len(text) > 200:
            text = text[:200] + "..."
        context_parts.append(f"- {text}")

    context_parts.append("\nAssistant responses (summarized):")
    for am in assistant_msgs[-5:]:
        summary = summarize_assistant_response(am.content)
        if summary:
            summary_preview = summary.split("\n")[0][:150]
            context_parts.append(f"- {summary_preview}")

    transcript = "\n".join(context_parts)

    max_context_tokens = 8000
    estimated_tokens = estimate_tokens(transcript)
    if estimated_tokens > max_context_tokens:
        lines = context_parts[::2] if len(context_parts) > 10 else context_parts
        transcript = "\n".join(lines)

    try:
        llm = get_llm_client()
        if not llm.is_available():
            return None

        system = (
            "You are a helpful assistant that creates concise, meaningful thread titles. "
            "Analyze the conversation and generate a 4-6 word title that captures the main topic or goal. "
            "Return ONLY the title text, nothing else."
        )
        prompt = f"Generate a thread title based on this conversation:\n\n{transcript}"
        title = llm.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ], max_tokens=50, temperature=0.3)

        title = title.strip()
        if title:
            word_count = len(title.split())
            if word_count <= 10:
                return title
        return None
    except Exception:
        return None
