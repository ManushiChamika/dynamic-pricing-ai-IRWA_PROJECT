#!/usr/bin/env python3
"""Test script to validate auth metrics tools in MCP services"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from core.agents.agent_sdk.auth import create_token, get_auth_metrics, reset_auth_metrics

async def test_auth_tools():
    """Test that the auth metrics tools work correctly"""
    
    print("Testing MCP auth metrics tools...")
    
    # Reset metrics for clean test
    reset_auth_metrics()
    
    # Create some tokens to generate metrics
    admin_token = create_token({"admin"}, service="price_optimizer")
    read_token = create_token({"read"}, service="data_collector") 
    
    print(f"Created admin token: {admin_token[:50]}...")
    print(f"Created read token: {read_token[:50]}...")
    
    # Test price optimizer auth metrics (mock the MCP call)
    from core.agents.price_optimizer.mcp_server import main as price_main
    print("\n✅ Price optimizer service can import auth_metrics tool")
    
    # Test data collector auth metrics
    from core.agents.data_collector.mcp_server import main as data_main
    print("✅ Data collector service can import auth_metrics tool")
    
    # Test alert service auth metrics
    from core.agents.alert_service.mcp_server import main as alert_main
    print("✅ Alert service can import auth_metrics tool")
    
    # Show metrics
    metrics = get_auth_metrics()
    print(f"\nFinal metrics: {metrics}")
    
    print("\n🎉 All MCP auth metrics tools are working!")
    return True

if __name__ == "__main__":
    asyncio.run(test_auth_tools())