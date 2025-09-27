"""
Integration tests for MCP services
Tests end-to-end functionality with real MCP server processes
"""
import asyncio
import subprocess
import sys
import time
import json
from pathlib import Path
import tempfile
import os

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.agents.agent_sdk.auth import get_service_token, get_admin_token


class MCPTestClient:
    """Simple MCP test client for integration testing."""
    
    def __init__(self, server_command: list):
        self.server_command = server_command
        self.process = None
    
    async def start_server(self):
        """Start MCP server process."""
        print(f"Starting server: {' '.join(self.server_command)}")
        self.process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Give server time to start
        await asyncio.sleep(2)
        
        if self.process.returncode is not None:
            stderr = await self.process.stderr.read()
            raise RuntimeError(f"Server failed to start: {stderr.decode()}")
    
    async def stop_server(self):
        """Stop MCP server process."""
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
    
    async def call_tool(self, tool_name: str, params: dict) -> dict:
        """Call a tool on the MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            }
        }
        
        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        # Read response (simplified - in real MCP we'd handle multiple messages)
        response_line = await self.process.stdout.readline()
        if response_line:
            return json.loads(response_line.decode())
        
        return {"error": "No response"}


async def test_alert_service_integration():
    """Test Alert Service MCP integration."""
    print("\n=== Testing Alert Service Integration ===")
    
    # Command to start alert service MCP server
    server_cmd = [
        sys.executable, "-m", "core.agents.alert_service.mcp_server"
    ]
    
    client = MCPTestClient(server_cmd)
    
    try:
        await client.start_server()
        print("✓ Alert service server started")
        
        # Test health check (no auth required)
        response = await client.call_tool("ping_health", {})
        if response.get("result", {}).get("ok"):
            print("✓ Health check passed")
        else:
            print(f"✗ Health check failed: {response}")
        
        # Test list_alerts with valid token
        token = get_service_token("alert_service")
        response = await client.call_tool("list_alerts", {
            "capability_token": token
        })
        
        if response.get("result", {}).get("ok"):
            print("✓ list_alerts with valid token passed")
        else:
            print(f"✗ list_alerts failed: {response}")
        
        # Test list_alerts with invalid token (should fail)
        response = await client.call_tool("list_alerts", {
            "capability_token": "invalid"
        })
        
        result = response.get("result", {})
        if not result.get("ok") and result.get("error") == "auth_error":
            print("✓ list_alerts with invalid token correctly rejected")
        else:
            print(f"✗ list_alerts should have failed: {response}")
    
    except Exception as e:
        print(f"✗ Alert service integration test failed: {e}")
    
    finally:
        await client.stop_server()


async def test_data_collector_integration():
    """Test Data Collector MCP integration."""
    print("\n=== Testing Data Collector Integration ===")
    
    server_cmd = [
        sys.executable, "-m", "core.agents.data_collector.mcp_server"
    ]
    
    client = MCPTestClient(server_cmd)
    
    try:
        await client.start_server()
        print("✓ Data collector server started")
        
        # Test health check
        response = await client.call_tool("ping_health", {})
        if response.get("result", {}).get("ok"):
            print("✓ Health check passed")
        
        # Test list_sources with valid token
        token = get_service_token("data_collector")
        response = await client.call_tool("list_sources", {
            "capability_token": token
        })
        
        if response.get("result", {}).get("ok"):
            print("✓ list_sources with valid token passed")
        else:
            print(f"✗ list_sources failed: {response}")
        
        # Test fetch_market_features with valid token
        response = await client.call_tool("fetch_market_features", {
            "sku": "TEST-SKU",
            "capability_token": token
        })
        
        if response.get("result", {}).get("ok"):
            print("✓ fetch_market_features with valid token passed")
        else:
            print(f"✗ fetch_market_features failed: {response}")
    
    except Exception as e:
        print(f"✗ Data collector integration test failed: {e}")
    
    finally:
        await client.stop_server()


async def test_price_optimizer_integration():
    """Test Price Optimizer MCP integration."""
    print("\n=== Testing Price Optimizer Integration ===")
    
    server_cmd = [
        sys.executable, "-m", "core.agents.price_optimizer.mcp_server"
    ]
    
    client = MCPTestClient(server_cmd)
    
    try:
        await client.start_server()
        print("✓ Price optimizer server started")
        
        # Test health check
        response = await client.call_tool("ping_health", {})
        if response.get("result", {}).get("ok"):
            print("✓ Health check passed")
        
        # Test propose_price with valid token
        token = get_service_token("price_optimizer")
        response = await client.call_tool("propose_price", {
            "sku": "TEST-SKU",
            "our_price": 100.0,
            "competitor_price": 95.0,
            "capability_token": token
        })
        
        result = response.get("result", {})
        if result.get("ok") and "proposal" in result:
            print("✓ propose_price with valid token passed")
            proposal_id = result["proposal"]["proposal_id"]
            
            # Test explain_proposal
            response = await client.call_tool("explain_proposal", {
                "proposal_id": proposal_id,
                "capability_token": token
            })
            
            if response.get("result", {}).get("ok"):
                print("✓ explain_proposal passed")
            else:
                print(f"✗ explain_proposal failed: {response}")
        
        else:
            print(f"✗ propose_price failed: {response}")
    
    except Exception as e:
        print(f"✗ Price optimizer integration test failed: {e}")
    
    finally:
        await client.stop_server()


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
        print("✓ Token creation works")
        
        # Test valid verification
        verify_capability(token, "read")
        print("✓ Valid token verification works")
        
        # Test invalid scope
        try:
            verify_capability(token, "admin")
            print("✗ Should have failed for insufficient scope")
        except InsufficientScopeError:
            print("✓ Insufficient scope correctly rejected")
        
        # Test service tokens
        for service in ["alert_service", "data_collector", "price_optimizer"]:
            token = get_service_token(service)
            assert len(token) > 0
        print("✓ Service token generation works")
        
    except Exception as e:
        print(f"✗ Auth functionality test failed: {e}")


def create_pytest_config():
    """Create a simple pytest configuration for the project."""
    pytest_ini = """
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
asyncio_mode = auto
"""
    
    with open(PROJECT_ROOT / "pytest.ini", "w") as f:
        f.write(pytest_ini)
    
    print("Created pytest.ini configuration")


async def main():
    """Run all integration tests."""
    print("=== MCP Integration Tests ===")
    
    # Test auth system first (doesn't require servers)
    test_auth_functionality()
    
    # Create pytest config
    create_pytest_config()
    
    # Test individual services
    await test_alert_service_integration()
    await test_data_collector_integration()
    await test_price_optimizer_integration()
    
    print("\n=== Integration Tests Complete ===")
    print("Note: Some tests may fail if dependencies are missing.")
    print("To run with pytest: pip install pytest pytest-asyncio")
    print("Then run: pytest test_mcp_integration.py")


if __name__ == "__main__":
    asyncio.run(main())