# Centralized authentication and authorization for MCP services
import hmac
import hashlib
import time
import os
from typing import Set, Optional
import functools

# Default scopes for different service types
DEFAULT_SCOPES = {
    "alert_service": {"read", "write", "create_rule", "subscribe"},
    "data_collector": {"read", "write", "collect", "import"},
    "price_optimizer": {"read", "write", "propose", "apply", "explain"},
    "admin": {"read", "write", "create_rule", "subscribe", "collect", "import", "propose", "apply", "explain", "admin"}
}

# Global secret from environment
AUTH_SECRET = os.getenv("MCP_AUTH_SECRET", "dev-mcp-secret")
TOKEN_EXPIRY_SECONDS = int(os.getenv("MCP_TOKEN_EXPIRY", "3600"))  # 1 hour default

class AuthError(Exception):
    """Base exception for authentication/authorization failures."""
    pass

class TokenExpiredError(AuthError):
    """Token has expired."""
    pass

class InvalidTokenError(AuthError):
    """Token is malformed or invalid."""
    pass

class InsufficientScopeError(AuthError):
    """Token lacks required scope."""
    pass

def create_token(scopes: Set[str], expiry_seconds: int = None) -> str:
    """Create a capability token with specified scopes.
    
    Args:
        scopes: Set of scope strings to grant
        expiry_seconds: Token lifetime (defaults to TOKEN_EXPIRY_SECONDS)
    
    Returns:
        Token string in format: timestamp:scope1,scope2.signature
    """
    if expiry_seconds is None:
        expiry_seconds = TOKEN_EXPIRY_SECONDS
    
    timestamp = int(time.time())
    scope_str = ",".join(sorted(scopes))
    payload = f"{timestamp}:{scope_str}"
    
    signature = hmac.new(
        AUTH_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{payload}.{signature}"

def verify_capability(token: str, required_scope: str) -> dict:
    """Verify a capability token has the required scope.
    
    Args:
        token: Token string to verify
        required_scope: Scope that must be present in token
        
    Returns:
        Dict with token metadata (timestamp, scopes)
        
    Raises:
        AuthError: If token is invalid, expired, or lacks scope
    """
    if not token:
        raise InvalidTokenError("No token provided")
    
    try:
        # Parse token: timestamp:scope1,scope2.signature
        payload, signature = token.rsplit(".", 1)
        timestamp_str, scope_str = payload.split(":", 1)
        
        # Verify signature
        expected_sig = hmac.new(
            AUTH_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            raise InvalidTokenError("Invalid token signature")
        
        # Check expiry
        timestamp = int(timestamp_str)
        if time.time() - timestamp > TOKEN_EXPIRY_SECONDS:
            raise TokenExpiredError("Token has expired")
        
        # Check scope
        granted_scopes = set(scope_str.split(",")) if scope_str else set()
        if required_scope not in granted_scopes:
            raise InsufficientScopeError(f"Token lacks required scope: {required_scope}")
        
        return {
            "timestamp": timestamp,
            "scopes": granted_scopes,
            "valid": True
        }
        
    except (ValueError, IndexError) as e:
        raise InvalidTokenError(f"Malformed token: {e}") from e

def require_scope(scope: str):
    """Decorator to require a specific scope for MCP tool access.
    
    Args:
        scope: Required scope string
        
    The decorated function must accept a 'capability_token' parameter.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract capability_token from kwargs
            token = kwargs.get('capability_token', '')
            
            try:
                verify_capability(token, scope)
                return await func(*args, **kwargs)
            except AuthError as e:
                return {
                    "ok": False,
                    "error": "auth_error",
                    "message": str(e),
                    "required_scope": scope
                }
            except Exception as e:
                return {
                    "ok": False,
                    "error": "internal_error", 
                    "message": str(e)
                }
        
        return wrapper
    return decorator

def get_service_token(service_name: str) -> str:
    """Get a default token for a service with its standard scopes.
    
    Args:
        service_name: Name of service ("alert_service", "data_collector", etc.)
        
    Returns:
        Token string with default scopes for the service
    """
    scopes = DEFAULT_SCOPES.get(service_name, {"read"})
    return create_token(scopes)

def get_admin_token() -> str:
    """Get an admin token with all scopes."""
    return create_token(DEFAULT_SCOPES["admin"])

# Dev/testing utilities
def create_dev_token(scopes: str) -> str:
    """Create a token for development/testing.
    
    Args:
        scopes: Comma-separated scope string (e.g., "read,write")
        
    Returns:
        Token string
    """
    scope_set = set(s.strip() for s in scopes.split(","))
    return create_token(scope_set)

# Backward compatibility with existing alert service auth
def verify_capability_legacy(token: str, scope: str):
    """Legacy verify_capability function for backward compatibility.
    
    Raises PermissionError instead of AuthError to match original behavior.
    """
    try:
        verify_capability(token, scope)
    except AuthError as e:
        raise PermissionError(str(e)) from e