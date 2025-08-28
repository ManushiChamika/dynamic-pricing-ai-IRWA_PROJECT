from langgraph.graph import StateGraph
from pydantic import BaseModel
from core.agents.alert_service.tools import Tools
from core.agents.alert_service.repo import Repo

class TriageState(BaseModel):
    command: str
    incident_id: str | None = None
    action: str | None = None
    result: dict | None = None

tools = Tools(Repo())

def parse_cmd(s: TriageState) -> TriageState:
    t = s.command.lower()
    if t.startswith("ack "): s.action, s.incident_id = "ACK", t.split()[1]
    elif t.startswith("resolve "): s.action, s.incident_id = "RESOLVE", t.split()[1]
    else: s.action = "LIST"
    return s

def act(s: TriageState) -> TriageState:
    import asyncio
    if s.action == "ACK": s.result = asyncio.get_event_loop().run_until_complete(tools.ack_incident(s.incident_id))
    elif s.action == "RESOLVE": s.result = asyncio.get_event_loop().run_until_complete(tools.resolve_incident(s.incident_id))
    else: s.result = asyncio.get_event_loop().run_until_complete(tools.list_incidents("OPEN"))
    return s

graph = StateGraph(TriageState)
graph.add_node("parse", parse_cmd)
graph.add_node("act", act)
graph.add_edge("parse","act")
graph.set_entry_point("parse")
app = graph.compile()
