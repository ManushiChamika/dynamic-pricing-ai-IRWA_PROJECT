#!/usr/bin/env python3
"""
Simple import test to verify all MCP auth modules are working
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_imports():
    """Test all imports for MCP auth implementation."""
    print("Testing imports...")
    
    try:
        # Test auth module
        from core.agents.agent_sdk.auth import (
            create_token, 
            verify_capability,
            get_service_token,
            get_admin_token,
            AuthError,
            TokenExpiredError,
            InvalidTokenError,
            InsufficientScopeError
        )
        print("[OK] Auth module imports successful")
        
        # Test token creation
        token = create_token({"read", "write"})
        print(f"[OK] Token creation successful: {token[:20]}...")
        
        # Test token verification
        result = verify_capability(token, "read")
        print(f"[OK] Token verification successful: {result['valid']}")
        
        # Test service tokens
        alert_token = get_service_token("alert_service")
        data_token = get_service_token("data_collector")
        price_token = get_service_token("price_optimizer")
        admin_token = get_admin_token()
        print("[OK] Service token generation successful")
        
    except Exception as e:
        print(f"[FAIL] Auth module import failed: {e}")
        return False
    
    try:
        # Test MCP server imports
        from core.agents.alert_service.mcp_server import list_alerts, create_alert
        print("[OK] Alert service MCP imports successful")
    except Exception as e:
        print(f"[FAIL] Alert service MCP import failed: {e}")
        return False
    
    try:
        from core.agents.data_collector.mcp_server import fetch_market_features, start_collection
        print("[OK] Data collector MCP imports successful")
    except Exception as e:
        print(f"[FAIL] Data collector MCP import failed: {e}")
        return False
    
    try:
        from core.agents.price_optimizer.mcp_server import main
        print("[OK] Price optimizer MCP imports successful")
    except Exception as e:
        print(f"[FAIL] Price optimizer MCP import failed: {e}")
        return False
    
    return True

def test_auth_functionality():
    """Test basic auth functionality."""
    print("\nTesting auth functionality...")
    
    from core.agents.agent_sdk.auth import (
        create_token, 
        verify_capability,
        get_service_token,
        InsufficientScopeError,
        InvalidTokenError
    )
    
    # Test valid token
    token = create_token({"read", "write"})
    result = verify_capability(token, "read")
    assert result["valid"] is True
    print("[OK] Valid token verification works")
    
    # Test insufficient scope
    try:
        verify_capability(token, "admin")
        print("[FAIL] Should have failed with insufficient scope")
        return False
    except InsufficientScopeError:
        print("[OK] Insufficient scope detection works")
    
    # Test invalid token
    try:
        verify_capability("invalid", "read")
        print("[FAIL] Should have failed with invalid token")
        return False
    except InvalidTokenError:
        print("[OK] Invalid token detection works")
    
    # Test service tokens
    alert_token = get_service_token("alert_service")
    result = verify_capability(alert_token, "create_rule")
    assert result["valid"] is True
    print("[OK] Service token functionality works")
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("MCP Auth Import and Functionality Test")
    print("=" * 50)
    
    imports_ok = test_imports()
    if imports_ok:
        functionality_ok = test_auth_functionality()
        if functionality_ok:
            print("\n[SUCCESS] All tests passed! MCP auth implementation is working correctly.")
        else:
            print("\n[FAIL] Functionality tests failed.")
            sys.exit(1)
    else:
        print("\n[FAIL] Import tests failed.")
        sys.exit(1)