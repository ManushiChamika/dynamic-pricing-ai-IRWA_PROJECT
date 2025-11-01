from __future__ import annotations

from enum import Enum


class Topic(Enum):
    MARKET_TICK = "market.tick"
    MARKET_FETCH_REQUEST = "market.fetch.request"
    MARKET_FETCH_ACK = "market.fetch.ack"
    MARKET_FETCH_DONE = "market.fetch.done"
    PRICE_PROPOSAL = "price.proposal"
    ALERT = "alert.event"
    PRICE_UPDATE = "price.update"
    CHAT_PROMPT = "chat.prompt"
    CHAT_TOOL_CALL = "chat.tool_call"
