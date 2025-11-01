from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple


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
    trace_id: Optional[str] = None,
    algorithm: Optional[str] = None,
    market_records: Optional[List[Tuple[float, str]]] = None,
    relax_max_price_to_meet_margin: bool = False,
) -> Dict[str, Any]:
    base = float(f.our_price)
    rationale: List[str] = []

    if algorithm and market_records is not None:
        from .algorithms import ALGORITHMS
        
        algo_func = ALGORITHMS.get(algorithm)
        if algo_func:
            try:
                algo_price = algo_func(market_records)
                if algo_price is not None:
                    base = algo_price
                    rationale.append(f"Algorithm {algorithm} suggested ${algo_price:.2f}")
            except Exception as e:
                rationale.append(f"Algorithm {algorithm} failed: {str(e)}, using fallback")

    if not rationale:
        if f.competitor_price is not None:
            try:
                if f.competitor_price * 1.02 < f.our_price:
                    base = max(f.competitor_price * 0.99, min_price)
                    rationale.append("Competitor undercut → reduce slightly")
            except Exception:
                pass

        if f.cost is not None:
            try:
                floor = f.cost / (1.0 - float(min_margin))
                # If floor is greater than max_price and relaxation is allowed, relax max_price
                floor_rounded = round(floor, 2)
                if floor_rounded > max_price and relax_max_price_to_meet_margin:
                    prev_max = max_price
                    max_price = floor_rounded
                    rationale.append(f"Max price relaxed from ${prev_max:.2f} to ${max_price:.2f} to satisfy margin floor")
                    # Ensure base is at least the rounded floor
                    if base < floor_rounded:
                        base = floor_rounded
                        rationale.append("Margin floor enforced")
                else:
                    if base < floor:
                        base = floor
                        rationale.append("Margin floor enforced")
            except Exception:
                pass

    base = min(max(base, min_price), max_price)

    # Round the recommendation and ensure rounding doesn't push it outside constraints
    recommended = round(base, 2)
    if recommended < min_price:
        recommended = float(min_price)
    if recommended > max_price:
        recommended = float(max_price)

    result = {
        "recommended_price": recommended,
        "confidence": 0.8 if algorithm else 0.6,
        "rationale": "; ".join(rationale) or "No change",
        "algorithm": algorithm or "heuristic",
        "constraints_evaluation": {
            "min_price": min_price,
            "max_price": max_price,
            "min_margin": min_margin,
            "relaxed_max_price_to_meet_margin": relax_max_price_to_meet_margin,
        },
    }

    
    # Publish price proposal event
    try:
        if trace_id:
            from datetime import datetime
            from core.agents.agent_sdk.activity_log import should_trace, activity_log, safe_redact
            from core.events.journal import write_event
            if should_trace():
                activity_log.log(
                    agent="PriceOptimizer",
                    action="proposal.generated",
                    status="completed",
                    message=f"Price proposal for {f.sku}: {f.our_price} → {result['recommended_price']}",
                    details=safe_redact({
                        "trace_id": trace_id,
                        "sku": f.sku,
                        "old_price": f.our_price,
                        "new_price": result["recommended_price"],
                        "confidence": result["confidence"],
                        "rationale": result["rationale"]
                    })
                )
                write_event("price.proposal", {
                    "trace_id": trace_id,
                    "sku": f.sku,
                    "old_price": f.our_price,
                    "new_price": result["recommended_price"],
                    "competitor_price": f.competitor_price,
                    "cost": f.cost,
                    "confidence": result["confidence"],
                    "rationale": result["rationale"],
                    "constraints": result["constraints_evaluation"],
                    "timestamp": datetime.now().isoformat()
                })
    except Exception:
        # Best-effort logging; never break the flow
        pass
    
    return result




