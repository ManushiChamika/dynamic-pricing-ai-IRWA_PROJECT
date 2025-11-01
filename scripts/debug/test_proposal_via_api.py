"""
Test proposal persistence by directly triggering the PricingOptimizerAgent.
This bypasses the chat interface and rate-limited LLM, using heuristic fallback.
"""
import asyncio
import sqlite3
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))

async def test_direct_optimization():
    """Directly trigger optimization and verify persistence"""
    print("\n" + "="*70)
    print(" TESTING: Direct Price Optimization -> Proposal Persistence")
    print("="*70 + "\n")
    
    from core.agents.agent_sdk.bus_factory import get_bus
    from core.agents.agent_sdk.protocol import Topic
    
    db_path = root / "app" / "data.db"
    
    # Get a product from catalog
    print("[1/4] Finding product in catalog...")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    product = conn.execute("""
        SELECT sku, title, current_price 
        FROM product_catalog 
        WHERE current_price IS NOT NULL AND current_price > 0
        LIMIT 1
    """).fetchone()
    conn.close()
    
    if not product:
        print("      [ERROR] No products found!")
        return
    
    test_sku = product['sku']
    test_price = product['current_price']
    print(f"      -> Product: {test_sku}")
    print(f"      -> Current Price: ${test_price:,.2f}\n")
    
    # Clear old proposals
    print("[2/4] Clearing old proposals for this product...")
    conn = sqlite3.connect(str(db_path))
    count = conn.execute("SELECT COUNT(*) FROM price_proposals WHERE sku = ?", (test_sku,)).fetchone()[0]
    conn.execute("DELETE FROM price_proposals WHERE sku = ?", (test_sku,))
    conn.commit()
    conn.close()
    print(f"      -> Cleared {count} old proposals\n")
    
    # Publish optimization request directly to event bus
    print("[3/4] Publishing OPTIMIZATION_REQUEST to event bus...")
    bus = get_bus()
    request = {
        "product_name": test_sku,
        "sku": test_sku,
        "current_price": test_price,
        "user_request": "Test optimization for proposal persistence"
    }
    
    await bus.publish(Topic.OPTIMIZATION_REQUEST.value, request)
    print("      -> Request published")
    print("      -> Waiting for PricingOptimizerAgent to process...")
    print("      -> (Will use heuristic fallback due to LLM rate limits)\n")
    
    # Wait for processing
    await asyncio.sleep(3)
    
    # Check database
    print("[4/4] Checking database for persisted proposal...")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    row = conn.execute("""
        SELECT * FROM price_proposals
        WHERE sku = ?
        ORDER BY ts DESC
        LIMIT 1
    """, (test_sku,)).fetchone()
    
    if row:
        print("\n" + "="*70)
        print(" SUCCESS - Proposal Persisted to Database")
        print("="*70)
        print(f"\nProposal Details:")
        print(f"  ID:              {row['id']}")
        print(f"  SKU:             {row['sku']}")
        print(f"  Current Price:   ${row['current_price']:,.2f}")
        print(f"  Proposed Price:  ${row['proposed_price']:,.2f}")
        print(f"  Change:          ${row['proposed_price'] - row['current_price']:+,.2f}")
        print(f"  Margin:          {row['margin']:.2%}")
        print(f"  Algorithm:       {row['algorithm']}")
        print(f"  Timestamp:       {row['ts']}")
        print("\n" + "="*70)
        print(" Complete Flow Verified:")
        print("  [✓] OPTIMIZATION_REQUEST published")
        print("  [✓] PricingOptimizerAgent processed request")
        print("  [✓] PRICE_PROPOSAL event published")
        print("  [✓] ProposalLogger persisted to database")
        print("="*70 + "\n")
    else:
        print("\n[FAILED] No proposal found!")
        print("The PricingOptimizerAgent may not be running.")
        print("Make sure the backend server is running: python backend/main.py\n")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(test_direct_optimization())
