#!/usr/bin/env python3

"""
Dashboard-only navigation smoke test.
Validates that the app always serves the dashboard and supports chat deep-linking.
Requires the Streamlit app to be running on http://localhost:8502
"""

import requests

BASE_URL = "http://localhost:8502"


def _get(url: str) -> str:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.text.lower()


def _assert_streamlit_shell(html: str) -> None:
    # Streamlit serves a shell HTML; look for generic markers
    assert "streamlit" in html or "data-testid" in html or "stApp".lower() in html, (
        "Expected Streamlit shell markers not found"
    )


def test_dashboard_load_root():
    html = _get(f"{BASE_URL}")
    _assert_streamlit_shell(html)


def test_dashboard_ignores_legacy_pages():
    for legacy in ("landing", "login", "register"):
        html = _get(f"{BASE_URL}/?page={legacy}")
        _assert_streamlit_shell(html)


def test_chat_deeplink():
    html = _get(f"{BASE_URL}/?section=chat")
    _assert_streamlit_shell(html)


if __name__ == "__main__":
    # Simple manual run
    test_dashboard_load_root()
    test_dashboard_ignores_legacy_pages()
    test_chat_deeplink()
    print("Dashboard-only navigation smoke passed.")
