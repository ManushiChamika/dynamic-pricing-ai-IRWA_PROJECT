# core/agents/__init__.py
from __future__ import annotations

try:
    from .auto_applier import AutoApplier, AutoApplierConfig  
except Exception:
    AutoApplier = None 
    AutoApplierConfig = None  

try:
    from .user_interaction import UserInteractionAgent  
except Exception:
    try:
        from .user_interact.user_interaction_agent import UserInteractionAgent 
    except Exception:
        class UserInteractionAgent: 
            def __init__(self, user_name: str = "User"):
                self.user_name = user_name
            async def handle(self, message: str) -> str:
                return "(stub) UserInteractionAgent not available."
            def get_response(self, message: str) -> str:
                return "(stub) UserInteractionAgent not available."

__all__ = ["AutoApplier", "AutoApplierConfig", "UserInteractionAgent"]
