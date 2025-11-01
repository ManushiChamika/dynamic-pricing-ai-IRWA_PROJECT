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
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        
        price_selectors = [
            ".a-price .a-offscreen",
            ".a-price-whole",
            "span.a-price",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#price_inside_buybox",
            ".a-section.a-spacing-none.aok-align-center .a-price .a-offscreen",
            "[data-a-color='price'] .a-offscreen",
            "[itemprop='price']",
            "meta[itemprop='price']",
            ".price",
            ".product-price"
        ]
        
        price_element = None
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                break

        if not price_element:
            return {"status": "error", "message": "price element not found - site may be blocking scraper"}

        price_text = price_element.get("content") if price_element.has_attr("content") else price_element.get_text(strip=True)
        price = _extract_price(price_text)

        return {"status": "success", "price": price, "source": url}
    except Exception as e:
        return {"status": "error", "message": str(e)}
