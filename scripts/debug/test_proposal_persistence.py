"""
Test ProposalLogger persistence without requiring LLM.
Directly publishes PRICE_PROPOSAL events to the bus to verify database writes.
"""
import asyncio
import sqlite3
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))

async def test_proposal_persistence():
    """Test that PRICE_PROPOSAL events are persisted to database"""
    print("\n" + "="*70)
    print(" TESTING: ProposalLogger Database Persistence")
    print("="*70 + "\n")
    
    # Import components
    from core.agents.proposal_logger import ProposalLogger
    from core.agents.agent_sdk.bus_factory import get_bus
    from core.agents.agent_sdk.protocol import Topic
    
    print("[1/5] Starting ProposalLogger...")
    db_path = root / "app" / "data.db"
    proposal_logger = ProposalLogger(db_path=db_path)
    await proposal_logger.start()
    print("      -> ProposalLogger started and listening\n")
    
    # Clear old test proposals
    print("[2/5] Clearing old test proposals from database...")
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("DELETE FROM price_proposals WHERE sku = 'TEST-SKU-001'")
        conn.commit()
        conn.close()
        print("      -> Old test data cleared\n")
    except Exception as e:
        print(f"      [WARN] Failed to clear old data: {e}\n")
    
    # Publish test proposal
    print("[3/5] Publishing test PRICE_PROPOSAL event...")
    bus = get_bus()
    test_proposal = {
        "proposal_id": "test-123",
        "sku": "TEST-SKU-001",
        "product_id": "TEST-SKU-001",
        "proposed_price": 1500.00,
        "new_price": 1500.00,
        "current_price": 1200.00,
        "old_price": 1200.00,
        "previous_price": 1200.00,
        "margin": 0.15,
        "algorithm": "test_algorithm"
    }
    
    await bus.publish(Topic.PRICE_PROPOSAL.value, test_proposal)
    print("      -> Event published to bus\n")
    
    # Wait for async processing
    print("[4/5] Waiting for ProposalLogger to process event...")
    await asyncio.sleep(2)
    print("      -> Wait complete\n")
    
    # Verify database write
    print("[5/5] Checking database for persisted proposal...")
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        row = conn.execute("""
            SELECT * FROM price_proposals
            WHERE sku = 'TEST-SKU-001'
            ORDER BY ts DESC
            LIMIT 1
        """).fetchone()
        
        if row:
            print(f"      [SUCCESS] Proposal persisted to database!")
            print(f"      -> ID: {row['id']}")
            print(f"      -> SKU: {row['sku']}")
            print(f"      -> Current Price: ${row['current_price']:,.2f}")
            print(f"      -> Proposed Price: ${row['proposed_price']:,.2f}")
            print(f"      -> Margin: {row['margin']:.2%}")
            print(f"      -> Algorithm: {row['algorithm']}")
            print(f"      -> Timestamp: {row['ts']}")
        else:
            print("      [FAILED] No proposal found in database")
            print("      ProposalLogger may not be persisting events correctly")
        
        conn.close()
        
    except Exception as e:
        print(f"      [ERROR] Failed to check database: {e}")
    
    # Cleanup
    await proposal_logger.stop()
    
    print("\n" + "="*70)
    print(" TEST COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(test_proposal_persistence())
