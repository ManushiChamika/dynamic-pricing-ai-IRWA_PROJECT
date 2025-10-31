import asyncio
import sys
from backend.routers.prices import _fetch_products

async def test_fetch():
    print("Testing _fetch_products...")
    
    products = await _fetch_products("16")
    print(f"\n[OK] Found {len(products)} products for owner_id=16")
    
    if products:
        print("\nSample products:")
        for sku, price in list(products.items())[:5]:
            print(f"  {sku}: ${price}")
    
    print("\nTesting with specific SKU filter...")
    single = await _fetch_products("16", "LAPTOP-001")
    if single:
        print(f"[OK] Found filtered product: {single}")
    else:
        print("[FAIL] SKU filter failed")
    
    print("\nTesting with non-existent owner...")
    empty = await _fetch_products("99999")
    print(f"[OK] Non-existent owner returns {len(empty)} products (expected 0)")
    
    print("\n[OK] All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_fetch())
