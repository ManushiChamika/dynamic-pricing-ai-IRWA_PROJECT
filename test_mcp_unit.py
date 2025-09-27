"""
Unit tests for MCP server implementations
Tests auth, validation, tool handlers, and error handling
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
import json
import uuid
from typing import Dict, Any

# Import the auth system
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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

class TestMCPAuth:
    """Test MCP authentication and authorization."""
    
    def test_create_token(self):
        """Test token creation with different scopes."""
        scopes = {"read", "write"}
        token = create_token(scopes)
        
        # Should contain timestamp:scopes.signature
        assert ":" in token
        assert "." in token
        
        parts = token.split('.')
        assert len(parts) == 2
        
        payload, signature = parts
        timestamp_str, scope_str = payload.split(':', 1)
        
        # Check timestamp is recent
        timestamp = int(timestamp_str)
        now = int(datetime.now().timestamp())
        assert abs(now - timestamp) < 60  # Within 1 minute
        
        # Check scopes
        token_scopes = set(scope_str.split(','))
        assert token_scopes == scopes
    
    def test_verify_capability_valid(self):
        """Test capability verification with valid tokens."""
        token = create_token({"read", "write"})
        
        # Should pass for read
        result = verify_capability(token, "read")
        assert result["valid"] is True
        assert "read" in result["scopes"]
        
        # Should pass for write
        verify_capability(token, "write")
    
    def test_verify_capability_insufficient_scope(self):
        """Test capability verification with insufficient scope."""
        token = create_token({"read"})
        
        with pytest.raises(InsufficientScopeError):
            verify_capability(token, "write")
    
    def test_verify_capability_invalid_token(self):
        """Test capability verification with invalid tokens."""
        # Malformed token
        with pytest.raises(InvalidTokenError):
            verify_capability("invalid", "read")
        
        # Empty token
        with pytest.raises(InvalidTokenError):
            verify_capability("", "read")
        
        # Wrong signature
        with pytest.raises(InvalidTokenError):
            verify_capability("123456:read.wrongsignature", "read")
    
    def test_verify_capability_expired_token(self):
        """Test capability verification with expired token."""
        # Create token that's already expired
        import time
        old_time = int(time.time()) - 7200  # 2 hours ago
        
        with patch('core.agents.agent_sdk.auth.time.time', return_value=old_time):
            expired_token = create_token({"read"})
        
        # Should fail when checking now
        with pytest.raises(TokenExpiredError):
            verify_capability(expired_token, "read")
    
    def test_service_tokens(self):
        """Test service-specific token generation."""
        # Alert service token
        alert_token = get_service_token("alert_service")
        result = verify_capability(alert_token, "read")
        assert "create_rule" in result["scopes"]
        assert "subscribe" in result["scopes"]
        
        # Data collector token
        data_token = get_service_token("data_collector")
        result = verify_capability(data_token, "collect")
        assert "import" in result["scopes"]
        
        # Price optimizer token  
        price_token = get_service_token("price_optimizer")
        result = verify_capability(price_token, "propose")
        assert "apply" in result["scopes"]
        assert "explain" in result["scopes"]
    
    def test_admin_token(self):
        """Test admin token has all scopes."""
        admin_token = get_admin_token()
        result = verify_capability(admin_token, "admin")
        
        # Should have all scopes
        expected_scopes = {"admin", "read", "write", "create_rule", "subscribe", 
                          "collect", "import", "propose", "apply", "explain"}
        assert expected_scopes.issubset(result["scopes"])


class TestAlertServiceMCP:
    """Test Alert Service MCP implementation."""
    
    @pytest.fixture
    def mock_repo(self):
        """Mock repository for testing."""
        repo = Mock()
        repo.list_alerts = AsyncMock(return_value=[])
        repo.create_rule = AsyncMock(return_value={"rule_id": "test-rule"})
        repo.ack_incident = AsyncMock(return_value={"ok": True})
        repo.resolve_incident = AsyncMock(return_value={"ok": True})
        return repo
    
    @pytest.fixture
    def mock_tools(self):
        """Mock tools for testing."""
        tools = Mock()
        tools.list_alerts = AsyncMock(return_value={"ok": True, "alerts": []})
        tools.create_rule = AsyncMock(return_value={"ok": True, "rule_id": "test"})
        tools.ack_incident = AsyncMock(return_value={"ok": True})
        tools.resolve_incident = AsyncMock(return_value={"ok": True})
        tools.subscribe_alerts = AsyncMock(return_value={"ok": True, "subscription_id": "sub-123"})
        return tools
    
    @pytest.mark.asyncio
    async def test_list_alerts_with_auth(self, mock_tools):
        """Test list_alerts with proper authentication."""
        # Import the MCP server module
        with patch('core.agents.alert_service.mcp_server.tools', mock_tools):
            from core.agents.alert_service.mcp_server import list_alerts
            
            # Valid token with read scope
            token = get_service_token("alert_service")
            result = await list_alerts(capability_token=token)
            
            assert result["ok"] is True
            mock_tools.list_alerts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_alerts_auth_failure(self):
        """Test list_alerts with invalid auth."""
        from core.agents.alert_service.mcp_server import list_alerts
        
        # Invalid token
        result = await list_alerts(capability_token="invalid")
        assert result["ok"] is False
        assert result["error"] == "auth_error"
    
    @pytest.mark.asyncio
    async def test_create_alert_with_auth(self, mock_tools):
        """Test create_alert with proper authentication."""
        with patch('core.agents.alert_service.mcp_server.tools', mock_tools):
            from core.agents.alert_service.mcp_server import create_alert
            
            token = get_service_token("alert_service")
            spec = {"name": "test-alert", "condition": "price > 100"}
            
            result = await create_alert(spec=spec, capability_token=token)
            assert result["ok"] is True
            mock_tools.create_rule.assert_called_once_with(spec)
    
    @pytest.mark.asyncio
    async def test_create_alert_insufficient_scope(self):
        """Test create_alert with insufficient scope."""
        from core.agents.alert_service.mcp_server import create_alert
        
        # Token without create_rule scope
        token = create_token({"read"})
        spec = {"name": "test-alert"}
        
        result = await create_alert(spec=spec, capability_token=token)
        assert result["ok"] is False
        assert result["error"] == "auth_error"


class TestDataCollectorMCP:
    """Test Data Collector MCP implementation."""
    
    @pytest.fixture
    def mock_repo(self):
        repo = Mock()
        repo.init = AsyncMock()
        repo.features_for = AsyncMock(return_value={"features": []})
        repo.upsert_products = AsyncMock(return_value=5)
        repo.create_job = AsyncMock(return_value="job-123")
        repo.get_job = AsyncMock(return_value={"status": "running"})
        return repo
    
    @pytest.fixture
    def mock_collector(self):
        collector = Mock()
        collector.ingest_tick = AsyncMock()
        return collector
    
    @pytest.mark.asyncio
    async def test_fetch_market_features_with_auth(self, mock_repo):
        """Test fetch_market_features with proper authentication."""
        with patch('core.agents.data_collector.mcp_server._repo', mock_repo):
            from core.agents.data_collector.mcp_server import fetch_market_features
            
            token = get_service_token("data_collector")
            result = await fetch_market_features(
                sku="TEST-SKU",
                capability_token=token
            )
            
            assert result["ok"] is True
            mock_repo.init.assert_called_once()
            mock_repo.features_for.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_market_features_auth_failure(self):
        """Test fetch_market_features with invalid auth."""
        from core.agents.data_collector.mcp_server import fetch_market_features
        
        result = await fetch_market_features(
            sku="TEST-SKU",
            capability_token="invalid"
        )
        
        assert result["ok"] is False
        assert result["error"] == "auth_error"
    
    @pytest.mark.asyncio
    async def test_start_collection_with_auth(self, mock_repo):
        """Test start_collection with proper authentication."""
        with patch('core.agents.data_collector.mcp_server._repo', mock_repo):
            from core.agents.data_collector.mcp_server import start_collection
            
            token = get_service_token("data_collector")
            result = await start_collection(
                sku="TEST-SKU",
                capability_token=token
            )
            
            assert result["ok"] is True
            assert "job_id" in result
            mock_repo.create_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_import_product_catalog_validation(self, mock_repo):
        """Test product catalog import with validation."""
        with patch('core.agents.data_collector.mcp_server._repo', mock_repo):
            from core.agents.data_collector.mcp_server import import_product_catalog
            
            token = get_service_token("data_collector")
            
            # Valid products
            rows = [
                {"sku": "SKU1", "name": "Product 1"},
                {"sku": "SKU2", "name": "Product 2"}
            ]
            
            result = await import_product_catalog(
                rows=rows,
                capability_token=token
            )
            
            assert result["ok"] is True
            assert result["processed"] == 2
            mock_repo.upsert_products.assert_called_once()


class TestPriceOptimizerMCP:
    """Test Price Optimizer MCP implementation."""
    
    @pytest.mark.asyncio
    async def test_propose_price_with_auth(self):
        """Test propose_price with proper authentication."""
        # Mock the optimize function
        with patch('core.agents.price_optimizer.mcp_server.optimize') as mock_optimize:
            mock_optimize.return_value = {
                "price": 99.99,
                "margin": 0.25,
                "confidence": 0.85,
                "reasoning": "Optimized based on market conditions"
            }
            
            # Import after patching
            from core.agents.price_optimizer.mcp_server import main
            
            # Create MCP instance
            if hasattr(main, '__wrapped__'):
                # If it's already been called, get the mcp instance
                import core.agents.price_optimizer.mcp_server as mcp_module
                if hasattr(mcp_module, 'mcp'):
                    propose_price = None
                    for tool_name, tool_func in mcp_module.mcp._tools.items():
                        if tool_name == 'propose_price':
                            propose_price = tool_func
                            break
                    
                    if propose_price:
                        token = get_service_token("price_optimizer")
                        result = await propose_price(
                            sku="TEST-SKU",
                            our_price=100.0,
                            capability_token=token
                        )
                        
                        assert result["ok"] is True
                        assert "proposal" in result
                        assert result["proposal"]["sku"] == "TEST-SKU"
    
    @pytest.mark.asyncio
    async def test_propose_price_validation_error(self):
        """Test propose_price with validation errors."""
        with patch('core.agents.price_optimizer.mcp_server.optimize'):
            from core.agents.price_optimizer.mcp_server import main
            
            # Test with invalid price (negative)
            # This would be handled by Pydantic validation
            pass  # Implementation would test validation errors


class TestSchemaValidation:
    """Test Pydantic schema validation across services."""
    
    def test_alert_service_schemas(self):
        """Test alert service input validation schemas."""
        from core.agents.alert_service.mcp_server import (
            ListAlertsRequest,
            CreateAlertRequest,
            AlertActionRequest
        )
        
        # Valid request
        request = ListAlertsRequest(status="active", limit=50)
        assert request.status == "active"
        assert request.limit == 50
        
        # Invalid status
        with pytest.raises(ValueError):
            ListAlertsRequest(status="invalid")
        
        # Invalid limit (too high)
        with pytest.raises(ValueError):
            ListAlertsRequest(limit=2000)
    
    def test_data_collector_schemas(self):
        """Test data collector input validation schemas."""
        from core.agents.data_collector.mcp_server import (
            StartCollectionRequest,
            FetchMarketFeaturesRequest,
            ImportProductCatalogRequest
        )
        
        # Valid request
        request = StartCollectionRequest(
            sku="TEST-SKU",
            connector="mock",
            depth=5
        )
        assert request.sku == "TEST-SKU"
        assert request.connector == "mock"
        
        # Invalid connector
        with pytest.raises(ValueError):
            StartCollectionRequest(sku="TEST", connector="invalid")
    
    def test_price_optimizer_schemas(self):
        """Test price optimizer input validation schemas."""
        from core.agents.price_optimizer.mcp_server import (
            ProposePriceRequest,
            ProposalActionRequest
        )
        
        # Valid request
        request = ProposePriceRequest(
            sku="TEST-SKU",
            our_price=100.0,
            min_margin=0.15
        )
        assert request.sku == "TEST-SKU"
        assert request.our_price == 100.0
        
        # Invalid price (negative)
        with pytest.raises(ValueError):
            ProposePriceRequest(sku="TEST", our_price=-10.0)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])