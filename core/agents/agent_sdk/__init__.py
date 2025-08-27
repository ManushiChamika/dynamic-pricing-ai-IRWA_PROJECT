# core/agent_sdk/__init__.py
"""
Shim so callers can do:
    from core.agent_sdk import get_bus, Topic
or:
    from core.agent_sdk.bus_factory import get_bus
    from core.agent_sdk.protocol import Topic
"""

# Prefer local bus_factory/protocol modules if present
try:
    from .bus_factory import get_bus        # noqa: F401
except Exception as e:
    raise ImportError("core.agent_sdk.bus_factory not found") from e

try:
    from .protocol import Topic             # noqa: F401
except Exception as e:
    raise ImportError("core.agent_sdk.protocol not found") from e
