#!/usr/bin/env python3
"""
Quick test to verify demo readiness for VIVA presentation
Tests all 4 agents and their integration with UIA
"""

import os
import sys
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
        print("✅ UserInteractionAgent imported successfully")
    except Exception as e:
        print(f"❌ UserInteractionAgent import failed: {e}")
        return False
    
    try:
        from core.agents.pricing_optimizer import PricingOptimizer
        print("✅ PricingOptimizer imported successfully")
    except Exception as e:
        print(f"❌ PricingOptimizer import failed: {e}")
        return False
    
    try:
        from core.agents.alert_notification_agent import AlertNotificationAgent
        print("✅ AlertNotificationAgent imported successfully")
    except Exception as e:
        print(f"❌ AlertNotificationAgent import failed: {e}")
        return False
    
    try:
        from core.agents.data_collection_agent import DataCollectionAgent
        print("✅ DataCollectionAgent imported successfully")
    except Exception as e:
        print(f"❌ DataCollectionAgent import failed: {e}")
        return False
    
    return True

def test_uia_tools():
    """Test UIA has the required tools for agent coordination"""
    print("\n🔧 Testing UIA tools...")
    
    try:
        from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
        uia = UserInteractionAgent("test_user")
        
        # Test simple query
        result = uia.process_query("What brands do we have available?")
        if "error" not in result.lower():
            print("✅ UIA basic query works")
        else:
            print(f"❌ UIA basic query failed: {result}")
            return False
        
        print("✅ UIA tools test passed")
        return True
        
    except Exception as e:
        print(f"❌ UIA tools test failed: {e}")
        return False

def test_database_connection():
    """Test database connections work"""
    print("\n💾 Testing database connections...")
    
    import sqlite3
    
    # Test market database
    try:
        conn = sqlite3.connect("data/market.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM market_data")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Market database: {count} products found")
    except Exception as e:
        print(f"❌ Market database failed: {e}")
        return False
    
    return True

def test_streamlit_running():
    """Test if Streamlit is running"""
    print("\n🌐 Testing Streamlit status...")
    
    import subprocess
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, shell=True)
        if ':8501' in result.stdout:
            print("✅ Streamlit is running on port 8501")
            return True
        else:
            print("❌ Streamlit not detected on port 8501")
            return False
    except Exception as e:
        print(f"❌ Streamlit check failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 VIVA DEMO READINESS TEST\n")
    
    tests = [
        ("Import Test", test_imports),
        ("UIA Tools Test", test_uia_tools),
        ("Database Test", test_database_connection),
        ("Streamlit Test", test_streamlit_running),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("📊 SUMMARY:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED - DEMO READY!")
        print("\n📋 Demo URLs:")
        print("  Streamlit App: http://localhost:8501")
        print("  Battle-tested prompts: VIVA_BATTLE_TESTED_PROMPTS.md")
        print("\n🎯 Quick Demo Flow:")
        print("  1. Simple query: 'What brands do we have available?'")
        print("  2. POA trigger: 'Optimize pricing strategy for gaming laptops using AI'")
        print("  3. Multi-agent: 'Collect data, optimize prices, and check alerts'")
        print("  4. Show Activity tab for real-time agent coordination")
    else:
        print("\n⚠️  SOME TESTS FAILED - CHECK BEFORE DEMO")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)