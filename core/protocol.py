# core/protocol.py
from enum import Enum


class Topic(Enum):
    """Event bus topics for inter-agent communication."""
    
    # User interaction topics
    USER_REQUEST = "user_request"
    PRICE_RESPONSE = "price_response"
    
    # Market data topics
    MARKET_TICK = "market_tick"
    MARKET_UPDATE = "market_update"
    
    # Pricing topics
    PRICE_PROPOSAL = "price_proposal"
    PRICE_UPDATE = "price_update"
    
    # Alert topics
    ALERT = "alert"
    
    # Agent lifecycle topics
    AGENT_START = "agent_start"
    AGENT_STOP = "agent_stop"
