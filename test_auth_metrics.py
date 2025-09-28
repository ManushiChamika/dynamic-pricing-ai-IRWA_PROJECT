#!/usr/bin/env python3
"""Test auth metrics collection functionality."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from core.agents.agent_sdk.auth import (
    create_token, verify_capability, get_service_token, get_admin_token,
    get_auth_metrics, reset_auth_metrics,
    InvalidTokenError, TokenExpiredError, InsufficientScopeError
)
import time

def test_metrics_collection():
    """Test that metrics are properly collected during auth operations."""
    print("Testing auth metrics collection...")
    
    # Reset metrics to start clean
    reset_auth_metrics()
    initial_metrics = get_auth_metrics()
    print(f"Initial metrics: {initial_metrics}")
    
    # Test token creation metrics
    print("\nTesting token creation metrics...")
    token1 = create_token({"read", "write"})
    token2 = get_service_token("alert_service")
    admin_token = get_admin_token()
    
    metrics_after_creation = get_auth_metrics()
    print(f"Metrics after creation: {metrics_after_creation}")
    
    assert metrics_after_creation["tokens_created"] == 3, f"Expected 3 tokens created, got {metrics_after_creation['tokens_created']}"
    assert metrics_after_creation["service_tokens"]["alert_service"] == 1, "Expected 1 alert_service token"
    
    # Test successful verification metrics
    print("\nTesting successful verification metrics...")
    result1 = verify_capability(token1, "read")
    result2 = verify_capability(token2, "read")
    result3 = verify_capability(admin_token, "admin")
    
    metrics_after_verification = get_auth_metrics()
    print(f"Metrics after verification: {metrics_after_verification}")
    
    assert metrics_after_verification["tokens_verified"] == 3, f"Expected 3 tokens verified, got {metrics_after_verification['tokens_verified']}"
    assert metrics_after_verification["scope_requests"]["read"] == 2, "Expected 2 'read' scope requests"
    assert metrics_after_verification["scope_requests"]["admin"] == 1, "Expected 1 'admin' scope request"
    
    # Test failure metrics
    print("\nTesting failure metrics...")
    
    # Test invalid token
    try:
        verify_capability("invalid-token", "read")
        assert False, "Should have raised InvalidTokenError"
    except InvalidTokenError:
        pass
    
    # Test insufficient scope
    try:
        verify_capability(token1, "admin")  # token1 only has read,write
        assert False, "Should have raised InsufficientScopeError"
    except InsufficientScopeError:
        pass
    
    # Test expired token (create a token with 0 expiry)
    try:
        expired_token = create_token({"read"}, expiry_seconds=0)
        time.sleep(6)  # Wait for expiration (5 second clock skew tolerance + 1)
        verify_capability(expired_token, "read")
        assert False, "Should have raised TokenExpiredError"
    except TokenExpiredError:
        pass
    
    final_metrics = get_auth_metrics()
    print(f"Final metrics: {final_metrics}")
    
    # Should have 3 auth failures (invalid, insufficient_scope, expired)
    assert final_metrics["auth_failures"] == 3, f"Expected 3 auth failures, got {final_metrics['auth_failures']}"
    assert final_metrics["invalid_tokens"] == 1, f"Expected 1 invalid token, got {final_metrics['invalid_tokens']}"
    assert final_metrics["scope_denials"] == 1, f"Expected 1 scope denial, got {final_metrics['scope_denials']}"
    assert final_metrics["expired_tokens"] == 1, f"Expected 1 expired token, got {final_metrics['expired_tokens']}"
    
    print("All metrics collection tests passed!")

if __name__ == "__main__":
    try:
        test_metrics_collection()
        print("\nAuth metrics collection test completed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)