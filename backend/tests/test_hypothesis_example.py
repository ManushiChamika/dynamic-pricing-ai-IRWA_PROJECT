from hypothesis import given, strategies as st


def square(n: int) -> int:
    return n * n


@given(st.integers(min_value=-1000, max_value=1000))
def test_square_non_negative(n):
    result = square(n)
    assert result >= 0
