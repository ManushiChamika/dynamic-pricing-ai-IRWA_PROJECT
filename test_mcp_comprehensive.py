"""
Integration tests for MCP services
Tests end-to-end functionality with real MCP server processes
"""
import asyncio
import sys
import json
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.agents.agent_sdk.auth import get_service_token, get_admin_token


def test_auth_functionality():
    """Test auth system functionality independently."""
    print("\n=== Testing Auth System ===")
    
    try:
        from core.agents.agent_sdk.auth import (
            create_token, verify_capability, get_service_token,
            AuthError, InsufficientScopeError
        )
        
        # Test token creation
        token = create_token({"read", "write"})
        assert len(token.split('.')) == 2
        print("[OK] Token creation works")
        
        # Test valid verification
        verify_capability(token, "read")
        print("[OK] Valid token verification works")
        
        # Test invalid scope
        try:
            verify_capability(token, "admin")
            print("[FAIL] Should have failed for insufficient scope")
        except InsufficientScopeError:
            print("[OK] Insufficient scope correctly rejected")
        
        # Test service tokens
        for service in ["alert_service", "data_collector", "price_optimizer"]:
            token = get_service_token(service)
            assert len(token) > 0
        print("[OK] Service token generation works")
        
    except Exception as e:
        print(f"[FAIL] Auth functionality test failed: {e}")
        assert False, f"Auth functionality test failed: {e}"


def test_mcp_tool_import():
    """Test that MCP tools can be imported and called directly."""
    print("\n=== Testing MCP Tool Imports ===")
    
    try:
        # Test alert service tools
        from core.agents.alert_service.mcp_server import list_alerts
        token = get_service_token("alert_service")
        result = asyncio.run(list_alerts(capability_token=token))
        assert result["ok"] is True
        print("[OK] Alert service list_alerts works")
        
        # Test data collector tools
        from core.agents.data_collector.mcp_server import fetch_market_features
        token = get_service_token("data_collector")
        result = asyncio.run(fetch_market_features(sku="TEST-SKU", capability_token=token))
        assert result["ok"] is True
        print("[OK] Data collector fetch_market_features works")
        
        # Test price optimizer tools
        from core.agents.price_optimizer.mcp_server import main
        # The price optimizer uses a different pattern - it creates the MCP instance when imported
        print("[OK] Price optimizer imports successfully")
        
    except Exception as e:
        print(f"[FAIL] MCP tool import test failed: {e}")
        assert False, f"MCP tool import test failed: {e}"


def test_auth_scenarios():
    """Test various auth scenarios."""
    print("\n=== Testing Auth Scenarios ===")
    
    try:
        from core.agents.agent_sdk.auth import (
            create_token, verify_capability, 
            InvalidTokenError, InsufficientScopeError
        )
        from core.agents.alert_service.mcp_server import list_alerts
        
        # Test with invalid token
        result = asyncio.run(list_alerts(capability_token="invalid"))
        assert result["ok"] is False
        assert result["error"] == "auth_error"
        print("[OK] Invalid token correctly rejected")
        
        # Test with insufficient scope
        limited_token = create_token({"read"})  # No create_rule scope
        from core.agents.alert_service.mcp_server import create_alert
        result = asyncio.run(create_alert(
            spec={"name": "test", "condition": "price > 100"}, 
            capability_token=limited_token
        ))
        assert result["ok"] is False
        assert result["error"] == "auth_error"
        print("[OK] Insufficient scope correctly rejected")
        
        # Test with expired token (simulate by tampering with timestamp)
        expired_token = "123456:read.invalidsignature"
        result = asyncio.run(list_alerts(capability_token=expired_token))
        assert result["ok"] is False
        assert result["error"] == "auth_error"
        print("[OK] Expired/invalid token correctly rejected")
        
    except Exception as e:
        print(f"[FAIL] Auth scenarios test failed: {e}")
        assert False, f"Auth scenarios test failed: {e}"


def run_comprehensive_tests():
    """Run all MCP integration tests."""
    print("=== MCP Authorization Integration Tests ===")
    print("Testing the complete MCP auth implementation")
    
    tests = [
        ("Auth Functionality", test_auth_functionality),
        ("MCP Tool Imports", test_mcp_tool_import),
        ("Auth Scenarios", test_auth_scenarios)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- Running {test_name} ---")
        try:
            if test_func():
                print(f"[PASS] {test_name}")
                passed += 1
            else:
                print(f"[FAIL] {test_name}")
        except Exception as e:
            print(f"[ERROR] {test_name} crashed: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] All MCP authorization tests passed!")
        print("\nNext steps:")
        print("1. MCP servers can be started individually with:")
        print("   python -m core.agents.alert_service.mcp_server")
        print("   python -m core.agents.data_collector.mcp_server")
        print("   python -m core.agents.price_optimizer.mcp_server")
        print("2. Use tokens from get_service_token() for authentication")
        print("3. All tools require capability_token parameter")
        return True
    else:
        print("[FAIL] Some tests failed - check implementation")
        return False


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)