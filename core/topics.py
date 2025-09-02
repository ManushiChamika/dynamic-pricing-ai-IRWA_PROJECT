from enum import Enum

class Topic(str, Enum):
    MARKET_TICK = "market_tick"
    PRICE_PROPOSAL = "price_proposal"
    PRICE_APPLIED = "price_applied"
    ALERT = "alert"
