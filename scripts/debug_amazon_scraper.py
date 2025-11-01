import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup

test_url = "https://www.amazon.com/Dell-XPS-15-9530-Laptop/dp/B0C5RZQQFK"

print(f"Testing web scraper with URL: {test_url}\n")

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

try:
    resp = requests.get(test_url, headers=headers, timeout=15)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
    price_candidates = [
        soup.select_one(".a-price-whole"),
        soup.select_one(".a-price .a-offscreen"),
        soup.select_one("span.a-price"),
        soup.select_one("#priceblock_ourprice"),
        soup.select_one("#priceblock_dealprice"),
        soup.select_one("[itemprop=price]"),
        soup.select_one("meta[itemprop=price]"),
    ]
    
    print("Price candidates found:")
    for i, el in enumerate(price_candidates):
        if el:
            text = el.get("content") if el.has_attr("content") else el.get_text(strip=True)
            print(f"  {i+1}. {el.name} {el.get('class', [])} -> {text}")
    
    all_price_classes = soup.select("[class*='price']")
    print(f"\nFound {len(all_price_classes)} elements with 'price' in class name")
    for el in all_price_classes[:10]:
        print(f"  {el.name} {el.get('class')} -> {el.get_text(strip=True)[:50]}")
        
except Exception as e:
    print(f"Error: {e}")
