#!/usr/bin/env python3
"""
Direct test of MCP functions to debug integration issues
"""
import sys
import asyncio
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

async def test_alert_service():
    """Test alert service directly."""
    try:
        from core.agents.agent_sdk.auth import get_service_token
        from core.agents.alert_service.mcp_server import list_alerts
        
        token = get_service_token("alert_service")
        result = await list_alerts(capability_token=token)
        print(f"Alert service result: {result}")
        return result.get("ok", False)
    except Exception as e:
        print(f"Alert service error: {e}")
        return False

async def test_data_collector():
    """Test data collector directly."""
    try:
        from core.agents.agent_sdk.auth import get_service_token
        from core.agents.data_collector.mcp_server import fetch_market_features
        
        token = get_service_token("data_collector")
        result = await fetch_market_features(sku="TEST-SKU", capability_token=token)
        print(f"Data collector result: {result}")
        return result.get("ok", False)
    except Exception as e:
        print(f"Data collector error: {e}")
        return False

async def test_auth_rejection():
    """Test that invalid auth is rejected."""
    try:
        from core.agents.alert_service.mcp_server import list_alerts
        
        result = await list_alerts(capability_token="invalid")
        print(f"Auth rejection result: {result}")
        
        # Should return ok=False with error=auth_error
        return (result.get("ok") is False and 
                result.get("error") == "auth_error")
    except Exception as e:
        print(f"Auth rejection error: {e}")
        return False

async def main():
    print("=== Direct MCP Function Tests ===")
    
    print("\n1. Testing Alert Service...")
    alert_ok = await test_alert_service()
    print(f"Alert service: {'PASS' if alert_ok else 'FAIL'}")
    
    print("\n2. Testing Data Collector...")
    data_ok = await test_data_collector()
    print(f"Data collector: {'PASS' if data_ok else 'FAIL'}")
    
    print("\n3. Testing Auth Rejection...")
    auth_ok = await test_auth_rejection()
    print(f"Auth rejection: {'PASS' if auth_ok else 'FAIL'}")
    
    print(f"\n=== Summary ===")
    total_passed = sum([alert_ok, data_ok, auth_ok])
    print(f"Passed: {total_passed}/3")
    
    if total_passed == 3:
        print("[SUCCESS] All direct MCP function tests passed!")
    else:
        print("[INFO] Some tests failed - this may be due to missing dependencies")

if __name__ == "__main__":
    asyncio.run(main())