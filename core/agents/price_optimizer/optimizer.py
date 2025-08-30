from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Features:
    sku: str
    our_price: float
    competitor_price: Optional[float] = None
    demand_index: Optional[float] = None
    cost: Optional[float] = None


def optimize(
    f: Features,
    min_price: float,
    max_price: float,
    min_margin: float = 0.12,
) -> Dict[str, Any]:
    """
    Heuristic v0:
    - Start from our_price.
    - If competitor undercuts by >= ~2%, reduce slightly (to 99% of competitor) within bounds.
    - Enforce margin floor if cost provided.
    - Clamp to [min_price, max_price].
    """
    base = float(f.our_price)
    rationale = []

    # Competitor undercut heuristic
    if f.competitor_price is not None:
        try:
            if f.competitor_price * 1.02 < f.our_price:
                base = max(f.competitor_price * 0.99, min_price)
                rationale.append("Competitor undercut → reduce slightly")
        except Exception:
            pass

    # Enforce margin floor
    if f.cost is not None:
        try:
            floor = f.cost / (1.0 - float(min_margin))
            if base < floor:
                base = floor
                rationale.append("Margin floor enforced")
        except Exception:
            pass

    # Clamp to bounds
    base = min(max(base, min_price), max_price)

    return {
        "recommended_price": round(base, 2),
        "confidence": 0.6,  # placeholder
        "rationale": "; ".join(rationale) or "No change",
        "constraints_evaluation": {
            "min_price": min_price,
            "max_price": max_price,
            "min_margin": min_margin,
        },
    }



