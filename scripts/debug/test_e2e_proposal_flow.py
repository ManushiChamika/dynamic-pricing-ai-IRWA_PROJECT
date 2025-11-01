"""
Test end-to-end proposal persistence with actual Price Optimizer Agent.
Uses fallback heuristic mode (no LLM) to avoid rate limits.
"""
import asyncio
import sqlite3
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))

async def test_e2e_with_fallback():
    """Test Price Optimizer generates and ProposalLogger persists proposals"""
    print("\n" + "="*70)
    print(" TESTING: End-to-End Proposal Flow (Heuristic Mode)")
    print("="*70 + "\n")
    
    # Import components
    from core.agents.price_optimizer.agent import PricingOptimizerAgent
    from core.agents.proposal_logger import ProposalLogger
    from core.agents.agent_sdk.bus_factory import get_bus
    from core.agents.agent_sdk.protocol import Topic
    
    print("[1/6] Starting ProposalLogger...")
    db_path = root / "app" / "data.db"
    proposal_logger = ProposalLogger(db_path=db_path)
    await proposal_logger.start()
    print("      -> ProposalLogger started\n")
    
    print("[2/6] Starting PricingOptimizerAgent...")
    optimizer = PricingOptimizerAgent()
    await optimizer.start()
    print("      -> PricingOptimizerAgent started\n")
    
    # Get a real product SKU from catalog
    print("[3/6] Finding real product in catalog...")
    try:
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
            print("      [ERROR] No products found in catalog")
            return
        
        test_sku = product['sku']
        print(f"      -> Testing with product: {test_sku} (${product['current_price']:,.2f})\n")
    except Exception as e:
        print(f"      [ERROR] Failed to get product: {e}\n")
        return
    
    # Clear old proposals for this product
    print("[4/6] Clearing old proposals for test product...")
    try:
        conn = sqlite3.connect(str(db_path))
        before_count = conn.execute("SELECT COUNT(*) FROM price_proposals WHERE sku = ?", (test_sku,)).fetchone()[0]
        conn.execute("DELETE FROM price_proposals WHERE sku = ?", (test_sku,))
        conn.commit()
        conn.close()
        print(f"      -> Cleared {before_count} old proposals\n")
    except Exception as e:
        print(f"      [WARN] Failed to clear old proposals: {e}\n")
    
    # Trigger optimization via OPTIMIZATION_REQUEST event
    print("[5/6] Publishing OPTIMIZATION_REQUEST...")
    bus = get_bus()
    request = {
        "product_name": test_sku,
        "sku": test_sku,
        "user_request": "Optimize price using heuristic fallback"
    }
    
    await bus.publish(Topic.OPTIMIZATION_REQUEST.value, request)
    print("      -> Request published, waiting for processing...\n")
    
    # Wait for processing (optimizer + logger)
    await asyncio.sleep(5)
    
    # Check database for persisted proposal
    print("[6/6] Checking database for persisted proposal...")
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        row = conn.execute("""
            SELECT * FROM price_proposals
            WHERE sku = ?
            ORDER BY ts DESC
            LIMIT 1
        """, (test_sku,)).fetchone()
        
        if row:
            print(f"      [SUCCESS] Full workflow completed!")
            print(f"      -> Proposal ID: {row['id']}")
            print(f"      -> SKU: {row['sku']}")
            print(f"      -> Current Price: ${row['current_price']:,.2f}")
            print(f"      -> Proposed Price: ${row['proposed_price']:,.2f}")
            print(f"      -> Margin: {row['margin']:.2%}")
            print(f"      -> Algorithm: {row['algorithm']}")
            print(f"      -> Timestamp: {row['ts']}")
            print(f"\n      ✅ Price Optimizer published proposal")
            print(f"      ✅ ProposalLogger persisted to database")
        else:
            print(f"      [FAILED] No proposal found for {test_sku}")
            print(f"      Check logs above for optimizer errors")
        
        conn.close()
        
    except Exception as e:
        print(f"      [ERROR] Failed to check database: {e}")
    
    # Cleanup
    await proposal_logger.stop()
    
    print("\n" + "="*70)
    print(" TEST COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(test_e2e_with_fallback())
