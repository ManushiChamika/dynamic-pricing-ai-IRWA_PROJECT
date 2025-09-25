# core/agents/alert_service/sinks/ui.py
from core.agents.agent_sdk import Topic, get_bus

_bus = get_bus()

class UiSink:
    async def send(self, incident, rule):
        obj = incident if isinstance(incident, dict) else getattr(incident, "__dict__", incident)
        await _bus.publish(Topic.ALERT.value, obj)
