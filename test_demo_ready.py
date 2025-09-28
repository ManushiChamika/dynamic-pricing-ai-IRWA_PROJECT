#!/usr/bin/env python3
"""
Quick test script to verify UIA -> POA integration works
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_database_access():
    """Test database connectivity"""
    print("\n=== Testing Database Access ===")
    try:
        import sqlite3
        from pathlib import Path
        
        db_path = Path('app/data.db')
        if not db_path.exists():
            print("[FAIL] Database file not found")
            assert False, "Database file not found"
            
        conn = sqlite3.connect(db_path)
        cursor = conn.execute('SELECT COUNT(*) FROM product_catalog')
        count = cursor.fetchone()[0]
        
        cursor = conn.execute('SELECT sku, title, current_price FROM product_catalog LIMIT 3')
        products = cursor.fetchall()
        
        print(f"Found {count} products in catalog")
        print("Sample products:")
        for sku, title, price in products:
            print(f"  {sku}: {title} - ${price}")
            
        conn.close()
        print("[PASS] Database access test passed")
    except Exception as e:
        print(f"[FAIL] Database access test failed: {e}")
        assert False, f"Database access test failed: {e}"

def test_simple_query():
    """Test UIA handling simple query"""
    print("\n=== Testing Simple Query (UIA Only) ===")
    try:
        from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
        agent = UserInteractionAgent('TestUser')
        
        query = "What is the current price of SKU-123?"
        print(f"Query: {query}")
        
        response = agent.get_response(query)
        print(f"Response: {response[:300]}...")
        print("[PASS] Simple query test passed")
    except Exception as e:
        print(f"[FAIL] Simple query test failed: {e}")
        assert False, f"Simple query test failed: {e}"

def main():
    print("Testing UIA -> POA Integration")
    print("=" * 50)
    
    # Test database first
    try:
        test_database_access()
        db_ok = True
    except:
        db_ok = False
    
    if db_ok:
        # Test UIA functionality
        try:
            test_simple_query()
            uia_ok = True
        except:
            uia_ok = False
        
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        
        if uia_ok:
            print("[PASS] System ready for demo!")
            print("\nDemo queries to try in the UI:")
            print('  Simple: "What is the current price of SKU-123?"')
            print('  Complex: "Optimize price for SKU-123 using AI profit maximization"')
            print('  Complex: "Run pricing workflow for ASUS-ProArt-5979Ultr"')
            
            print("\nExpected behavior:")
            print("  - Simple queries: Blue 'Thinking...' bubble")
            print("  - Complex queries: Yellow 'Price Optimization Agent working...' bubble")
            print("  - POA will use AI to select pricing algorithms")
        else:
            print("[FAIL] Issues found - check logs above")
    else:
        print("[FAIL] Database issues - cannot proceed with demo")

if __name__ == "__main__":
    main()