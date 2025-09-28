#!/usr/bin/env python3
"""
VIVA Demo Test Script
Tests the multi-agent system functionality for presentation
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Test all critical imports work"""
    print("🔍 Testing imports...")
    
    try:
        from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
        print("✅ UIA import successful")
    except Exception as e:
        print(f"❌ UIA import failed: {e}")
        return False
    
    try:
        from core.agents.price_optimizer.agent import PriceOptimizationAgent
        print("✅ POA import successful")
    except Exception as e:
        print(f"❌ POA import failed: {e}")
        return False
    
    try:
        from core.agents.alert_service.engine import AlertEngine
        print("✅ Alert Engine import successful")
    except Exception as e:
        print(f"❌ Alert Engine import failed: {e}")
        return False
    
    try:
        from core.agents.data_collector.collector import DataCollectorAgent
        print("✅ Data Collector import successful")
    except Exception as e:
        print(f"❌ Data Collector import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database has demo data"""
    print("\n📊 Testing database...")
    
    try:
        import sqlite3
        conn = sqlite3.connect('data/market.db')
        cursor = conn.cursor()
        
        # Check product count
        cursor.execute('SELECT COUNT(*) FROM market_data')
        count = cursor.fetchone()[0]
        print(f"✅ Database has {count} products")
        
        if count < 10:
            print("⚠️  Warning: Few products for demo (recommend 20+)")
        
        # Check price range
        cursor.execute('SELECT MIN(current_price), MAX(current_price) FROM market_data')
        min_price, max_price = cursor.fetchone()
        print(f"✅ Price range: LKR {min_price:,.0f} - LKR {max_price:,.0f}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_uia_basic():
    """Test UIA basic functionality"""
    print("\n🤖 Testing UIA...")
    
    try:
        from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
        
        # Create UIA instance
        uia = UserInteractionAgent("viva_test")
        print("✅ UIA instance created")
        
        # Test simple query - this might still return empty, but shouldn't crash
        response = uia.get_response("Hello")
        print(f"✅ UIA responded (length: {len(response)})")
        
        if len(response) == 0:
            print("⚠️  UIA returns empty responses - check during demo")
        
        return True
        
    except Exception as e:
        print(f"❌ UIA test failed: {e}")
        traceback.print_exc()
        return False

def test_activity_system():
    """Test activity logging system"""
    print("\n📝 Testing Activity System...")
    
    try:
        from app.ui.services.activity import get_activity_service
        
        service = get_activity_service()
        print("✅ Activity service available")
        
        # Test logging an event
        service.log_agent_activity("test_agent", "demo", {"test": "data"})
        print("✅ Activity logging works")
        
        return True
        
    except Exception as e:
        print(f"❌ Activity system test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🎭 VIVA Demo System Test")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Database Test", test_database),  
        ("UIA Basic Test", test_uia_basic),
        ("Activity System Test", test_activity_system),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 System ready for VIVA demo!")
        print("\n📖 Next steps:")
        print("1. Start Streamlit app: streamlit run app/streamlit_app.py")
        print("2. Use demo prompts in VIVA_DEMO_PROMPTS.md")
        print("3. Monitor Activity view for agent coordination")
    else:
        print("\n⚠️  Some issues found - review before demo")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)