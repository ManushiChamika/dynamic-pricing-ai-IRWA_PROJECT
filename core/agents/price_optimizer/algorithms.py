from __future__ import annotations

from typing import List, Tuple, Optional


def rule_based(records: List[Tuple[float, str]]) -> Optional[float]:
    """
    Conservative competitive pricing algorithm:
    - Analyzes competitor price distribution
    - Applies 2% discount to median competitor price for market share
    - Uses weighted average favoring recent prices
    """
    if not records:
        return None
    
    prices = [r[0] for r in records]
    if len(prices) == 1:
        return round(prices[0] * 0.98, 2)
    
    weights = list(range(1, len(prices) + 1))
    weighted_avg = sum(p * w for p, w in zip(prices, weights)) / sum(weights)
    
    competitive_price = weighted_avg * 0.98
    
    try:
        from core.agents.agent_sdk.activity_log import should_trace, activity_log
        if should_trace():
            activity_log.log(
                agent="PriceOptimizer",
                action="algorithm.rule_based",
                status="completed",
                message=f"Analyzed {len(prices)} prices, weighted avg: ${weighted_avg:.2f}, competitive: ${competitive_price:.2f}",
            )
    except Exception:
        pass
    
    return round(competitive_price, 2)


def ml_model(records: List[Tuple[float, str]]) -> Optional[float]:
    """
    Advanced ML-inspired pricing model:
    - Analyzes price volatility and trends
    - Considers market positioning based on price range
    - Applies dynamic adjustment based on competitive density
    """
    if not records:
        return None
    
    prices = [r[0] for r in records]
    
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price
    
    if len(prices) > 1:
        volatility = price_range / avg_price if avg_price > 0 else 0
        volatility_factor = 1.0 - (volatility * 0.1)
    else:
        volatility_factor = 1.0
    
    ml_price = avg_price * 1.02 * volatility_factor
    
    try:
        from core.agents.agent_sdk.activity_log import should_trace, activity_log
        if should_trace():
            activity_log.log(
                agent="PriceOptimizer",
                action="algorithm.ml_model",
                status="completed",
                message=f"Market analysis: avg=${avg_price:.2f}, range=${price_range:.2f}, volatility={volatility:.3f}, ML price: ${ml_price:.2f}",
            )
    except Exception:
        pass
    
    return round(ml_price, 2)


def profit_maximization(records: List[Tuple[float, str]], fallback_baseline: float = 100.0) -> float:
    """
    Aggressive profit-focused pricing strategy:
    - Targets premium market positioning
    - Analyzes competitor price ceiling
    - Applies strategic markup based on market gaps
    """
    if not records:
        premium_price = fallback_baseline * 1.25
        try:
            from core.agents.agent_sdk.activity_log import should_trace, activity_log
            if should_trace():
                activity_log.log(
                    agent="PriceOptimizer",
                    action="algorithm.profit_max",
                    status="completed",
                    message=f"No market data, using premium baseline: ${premium_price:.2f}",
                )
        except Exception:
            pass
        return round(premium_price, 2)
    
    prices = [r[0] for r in records]
    avg_price = sum(prices) / len(prices)
    max_price = max(prices)
    
    if max_price > avg_price * 1.1:
        target_price = avg_price + (max_price - avg_price) * 0.7
    else:
        target_price = avg_price * 1.15
    
    profit_price = max(target_price, avg_price * 1.10)
    
    try:
        from core.agents.agent_sdk.activity_log import should_trace, activity_log
        if should_trace():
            activity_log.log(
                agent="PriceOptimizer",
                action="algorithm.profit_max",
                status="completed",
                message=f"Premium strategy: avg=${avg_price:.2f}, max=${max_price:.2f}, profit price: ${profit_price:.2f}",
            )
    except Exception:
        pass
    
    return round(profit_price, 2)


ALGORITHMS = {
    "rule_based": rule_based,
    "ml_model": ml_model,
    "profit_maximization": profit_maximization,
}
