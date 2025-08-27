from langgraph.graph import StateGraph, END
from typing import Dict, Any
from pydantic import BaseModel, ValidationError
from core.agents.alert_service.schemas import RuleSpec
from core.agents.alert_service.tools import Tools
from core.agents.alert_service.repo import Repo

class GState(BaseModel):
    user_text: str
    draft_rule: Dict[str, Any] | None = None
    validated: bool = False
    result: Dict[str, Any] | None = None

tools = Tools(Repo())

def nl_to_draft(state: GState) -> GState:
    # very small deterministic parser; you can swap in an LLM with structured output
    txt = state.user_text.lower()
    spec = {
        "id": "auto-undercut",
        "source": "MARKET_TICK",
        "where": "tick.competitor_price and tick.competitor_price * 1.02 < tick.our_price",
        "hold_for": "5m",
        "severity": "warn",
        "notify": {"channels": ["ui"], "throttle": "15m"},
        "enabled": True
    }
    state.draft_rule = spec
    return state

def validate_rule(state: GState) -> GState:
    try:
        RuleSpec(**state.draft_rule)
        state.validated = True
    except ValidationError as e:
        state.result = {"ok": False, "error": e.errors()}
    return state

def persist_rule(state: GState) -> GState:
    if not state.validated: return state
    state.result = {"ok": True}
    # call tool directly (synchronous here; wrap async in your app)
    import asyncio
    asyncio.get_event_loop().run_until_complete(tools.create_rule(state.draft_rule))
    return state

graph = StateGraph(GState)
graph.add_node("parse", nl_to_draft)
graph.add_node("validate", validate_rule)
graph.add_node("persist", persist_rule)
graph.add_edge("parse","validate")
graph.add_edge("validate","persist")
graph.set_entry_point("parse")
graph.set_finish_point("persist")
app = graph.compile()
