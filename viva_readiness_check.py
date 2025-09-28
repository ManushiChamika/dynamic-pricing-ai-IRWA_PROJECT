#!/usr/bin/env python3
"""
Quick VIVA Demo Test - Final verification before presentation
Tests core functionality needed for demo
"""

import os
import sys
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def main():
    print("=== VIVA DEMO READINESS CHECK ===\n")
    
    # Test 1: UIA Import and Basic Query
    print("1. Testing User Interaction Agent...")
    try:
        from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
        uia = UserInteractionAgent('demo_user')
        result = uia.get_response('What brands do we have available?')
        print("   SUCCESS: UIA responds with", len(result), "characters")
    except Exception as e:
        print(f"   FAILED: {e}")
        return False
    
    # Test 2: Database Content
    print("\n2. Testing Database...")
    try:
        import sqlite3
        conn = sqlite3.connect("data/market.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM market_data")
        count = cursor.fetchone()[0]
        cursor.execute("SELECT product_name FROM market_data LIMIT 3")
        samples = [row[0] for row in cursor.fetchall()]
        conn.close()
        print(f"   SUCCESS: Database has {count} products")
        print(f"   Samples: {', '.join(samples)}")
    except Exception as e:
        print(f"   FAILED: {e}")
        return False
    
    # Test 3: Streamlit Status
    print("\n3. Testing Streamlit...")
    try:
        import subprocess
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, shell=True)
        if ':8501' in result.stdout:
            print("   SUCCESS: Streamlit running on port 8501")
        else:
            print("   WARNING: Streamlit not detected")
            return False
    except Exception as e:
        print(f"   FAILED: {e}")
        return False
    
    # Test 4: Agent Tool Integration
    print("\n4. Testing Agent Tools...")
    try:
        # Test that UIA has the run_pricing_workflow tool
        response = uia.get_response('I need to optimize pricing strategy for gaming laptops using AI-driven competitive analysis')
        if len(response) > 50:
            print("   SUCCESS: Complex pricing query handled")
        else:
            print("   WARNING: Complex query got short response")
    except Exception as e:
        print(f"   FAILED: {e}")
        return False
    
    print("\n=== DEMO READY ===")
    print("\nDemo URLs:")
    print("  Streamlit: http://localhost:8501")
    print("  Prompts: VIVA_BATTLE_TESTED_PROMPTS.md")
    
    print("\nQuick Demo Flow:")
    print("  1. Simple: 'What brands do we have available?'")
    print("  2. Complex: 'Optimize pricing strategy for gaming laptops using AI'")
    print("  3. Multi-agent: 'Collect data, optimize prices, and check alerts'")
    print("  4. Show Activity tab for real-time feedback")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        print("\n" + ("="*50))
        if success:
            print("STATUS: READY FOR VIVA PRESENTATION!")
        else:
            print("STATUS: NEEDS ATTENTION BEFORE DEMO")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        sys.exit(1)