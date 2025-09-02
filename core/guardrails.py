from dataclasses import dataclass
from typing import Optional

@dataclass
class Guardrails:
    min_margin: float = 0.12     # 12% minimum margin
    max_delta: float = 0.10      # no more than 10% step from current

def validate_price(current: Optional[float], proposed: float, cost: Optional[float], g: Guardrails):
    if cost is not None and proposed > 0:
        margin = (proposed - cost) / proposed
        if margin < g.min_margin:
            return False, f"margin {margin:.3f} < {g.min_margin:.3f}"
    if current is not None and current > 0:
        delta = abs(proposed - current) / current
        if delta > g.max_delta:
            return False, f"delta {delta:.3f} > {g.max_delta:.3f}"
    return True, "ok"
