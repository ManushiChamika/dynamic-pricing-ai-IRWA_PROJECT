# core/protocol.py
from enum import Enum

class Topic(Enum):
    MARKET_TICK = "MARKET_TICK"
    PRICE_PROPOSAL = "PRICE_PROPOSAL"
    ALERT = "ALERT" 
