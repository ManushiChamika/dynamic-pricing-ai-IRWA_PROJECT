import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))
from hypothesis import given, strategies as st
from core.agents.price_optimizer.optimizer import Features, optimize


@given(
    sku=st.text(min_size=1, max_size=10),
    our_price=st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
    cost=st.floats(min_value=0.01, max_value=5000, allow_nan=False, allow_infinity=False),
    min_price=st.floats(min_value=0.0, max_value=10000),
    max_price=st.floats(min_value=0.0, max_value=10000),
    min_margin=st.floats(min_value=0.0, max_value=0.9),
)
def test_margin_floor_enforced(sku, our_price, cost, min_price, max_price, min_margin):
    if min_price > max_price:
        min_price, max_price = max_price, min_price
    f = Features(sku=sku, our_price=our_price, competitor_price=None, demand_index=None, cost=cost)
    result = optimize(f, min_price=min_price, max_price=max_price, min_margin=min_margin)
    rp = result['recommended_price']
    floor = round(cost / (1.0 - float(min_margin)), 2)
    assert rp >= min_price - 1e-8
    assert rp <= max_price + 1e-8
    # Only require that the margin floor is enforced when it's feasible within constraints
    if floor <= max_price:
        assert rp >= floor - 1e-8


@given(
    sku=st.text(min_size=1, max_size=10),
    our_price=st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
    market_prices=st.lists(st.tuples(st.floats(min_value=0.01, max_value=10000), st.text(min_size=1, max_size=5)), min_size=1, max_size=10),
    min_price=st.floats(min_value=0.0, max_value=10000),
    max_price=st.floats(min_value=0.0, max_value=10000),
)
def test_algorithm_override_bounds(sku, our_price, market_prices, min_price, max_price):
    if min_price > max_price:
        min_price, max_price = max_price, min_price
    f = Features(sku=sku, our_price=our_price)
    # Use an algorithm name that exists; use "profit_maximization" which may suggest high prices
    result = optimize(f, min_price=min_price, max_price=max_price, algorithm='profit_maximization', market_records=market_prices)
    rp = result['recommended_price']
    assert rp >= min_price - 1e-8
    assert rp <= max_price + 1e-8
