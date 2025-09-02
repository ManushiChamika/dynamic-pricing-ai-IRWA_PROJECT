import re
from typing import Optional

SEMANTIC_HINTS = {
    "cheapest": ["cheapest", "lowest", "bargain", "budget", "least costly"],
    "most_expensive": ["expensive", "highest", "costliest", "premium"],
    "trending": ["trending", "popular", "moving", "activity", "hot"],
    "stats": ["average", "summary", "stats", "min", "max", "over", "past"],
    "optimize": ["optimize", "reprice", "set price", "update price"],
    "competitor_pressure": ["pressure", "competitor", "competition"],
}

class Intent:
    def __init__(self, type: str, product: Optional[str] = None, period: int = 7, count: int = 5):
        self.type = type
        self.product = product
        self.period = period
        self.count = count

def parse_intent(message: str) -> Intent:
    msg = message.lower()

    # detect number of days
    m = re.search(r"last (\d+) days?", msg)
    days = int(m.group(1)) if m else 7

    # detect top-N
    n = re.search(r"top (\d+)", msg)
    count = int(n.group(1)) if n else 5

    # detect SKU
    sku_match = re.search(r"\b([A-Z]{2,}-\d[\w-]*)\b", msg, flags=re.IGNORECASE)
    sku = sku_match.group(1).upper() if sku_match else None

    # match synonyms
    for intent, synonyms in SEMANTIC_HINTS.items():
        if any(word in msg for word in synonyms):
            return Intent(type=intent, product=sku, period=days, count=count)

    return Intent(type="stats", product=sku, period=days, count=count)
