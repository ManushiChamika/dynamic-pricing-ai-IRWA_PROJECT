import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))
from hypothesis import given, strategies as st
from core.agents.price_optimizer.optimizer import Features, optimize


@given(
    sku=st.text(min_size=1, max_size=10),
    our_price=st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
    competitor_price=st.one_of(st.none(), st.floats(min_value=0.01, max_value=10000)),
    demand_index=st.one_of(st.none(), st.floats(min_value=0.0, max_value=10.0)),
    cost=st.one_of(st.none(), st.floats(min_value=0.0, max_value=10000)),
    min_price=st.floats(min_value=0.0, max_value=5000),
    max_price=st.floats(min_value=0.0, max_value=5000),
    min_margin=st.floats(min_value=0.0, max_value=0.9),
)
def test_optimize_properties(sku, our_price, competitor_price, demand_index, cost, min_price, max_price, min_margin):
    if min_price > max_price:
        min_price, max_price = max_price, min_price
    f = Features(sku=sku, our_price=our_price, competitor_price=competitor_price, demand_index=demand_index, cost=cost)
    result = optimize(f, min_price=min_price, max_price=max_price, min_margin=min_margin)
    assert 'recommended_price' in result
    rp = result['recommended_price']
    assert isinstance(rp, float) or isinstance(rp, int)
    eps = 0.01
    assert rp >= min_price - eps - 1e-8 and rp <= max_price + eps + 1e-8
    assert 0.0 <= result.get('confidence', 0.0) <= 1.0
