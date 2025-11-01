"""
Simple web scraping tool to fetch a competitor price from a given URL.

Note: The CSS selector used is an example and must be adapted to the actual target site.
"""
from __future__ import annotations

import re
from typing import Dict

import requests
from bs4 import BeautifulSoup


def _extract_price(text: str) -> float:
    """Best-effort extraction of a price number from text like "$1,234.56"."""
    if text is None:
        raise ValueError("empty price text")
    # Remove currency symbols and commas, keep digits and dot/comma
    cleaned = re.sub(r"[^0-9.,]", "", text)
    # Prefer dot as decimal separator; replace comma if necessary
    if cleaned.count(",") == 1 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")
    cleaned = cleaned.replace(",", "")
    return float(cleaned)


def fetch_competitor_price(url: str) -> Dict[str, object]:
    """Scrapes a given URL to find the main product price.

    Returns a dict with keys: status, price (on success), source, or message (on error).
    """
    try:
        if not url or not isinstance(url, str):
            return {"status": "error", "message": "invalid url"}

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        # NOTE: This selector is an EXAMPLE. You must find the real one for your target site.
        price_element = soup.select_one(".product-price-class")
        if not price_element:
            # Try a couple of common alternatives before giving up
            price_element = (
                soup.select_one("[itemprop=price]")
                or soup.select_one("meta[itemprop=price][content]")
                or soup.select_one(".price, .product-price, .a-price-whole")
            )

        if not price_element:
            return {"status": "error", "message": "price element not found"}

        # support meta content attribute
        price_text = price_element.get("content") if price_element.has_attr("content") else price_element.get_text(strip=True)
        price = _extract_price(price_text)

        return {"status": "success", "price": price, "source": url}
    except Exception as e:
        return {"status": "error", "message": str(e)}
