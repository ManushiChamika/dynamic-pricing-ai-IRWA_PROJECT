from __future__ import annotations

# Re-export auto_applier bits
try:
    from .auto_applier import AutoApplier, AutoApplierConfig  # type: ignore
except Exception:
    AutoApplier = None  # type: ignore
    AutoApplierConfig = None  # type: ignore

# Try both possible locations for the user interaction agent.
try:
    from .user_interaction import UserInteractionAgent  # type: ignore
except Exception:
    try:
        from .user_interact.user_interaction_agent import UserInteractionAgent  # type: ignore
    except Exception:
        class UserInteractionAgent:  # type: ignore
            def __init__(self, user_name: str = "User"):
                self.user_name = user_name
            async def handle(self, message: str) -> str:
                return "(stub) UserInteractionAgent not available."
            def get_response(self, message: str) -> str:
                return "(stub) UserInteractionAgent not available."

__all__ = ["AutoApplier", "AutoApplierConfig", "UserInteractionAgent"]
