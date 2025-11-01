import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agents.data_collector.connectors.web_scraper import fetch_competitor_price

test_url = "https://www.amazon.com/Dell-XPS-15-9530-Laptop/dp/B0C5RZQQFK"

print(f"Testing web scraper with URL: {test_url}")
result = fetch_competitor_price(test_url)
print(f"\nResult: {result}")

if result["status"] == "success":
    print(f"\nPrice found: ${result['price']}")
else:
    print(f"\nError: {result['message']}")
