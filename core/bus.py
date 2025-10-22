from __future__ import annotations

from core.agents.agent_sdk.bus_factory import get_bus

# Provide a simple module-level bus object for scripts/tests that expect `from core.bus import bus`
bus = get_bus()
