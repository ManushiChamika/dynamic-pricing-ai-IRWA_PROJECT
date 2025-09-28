# Centralized authentication and authorization for MCP services
import hmac
import hashlib
import time
import os
from typing import Set, Optional, Dict, Any
import functools

# Import logging system - simplified approach for compatibility
import logging
import uuid

# Always use standard logging for now to avoid compatibility issues
logger = logging.getLogger("mcp.auth")

def new_correlation_id():
    return str(uuid.uuid4())[:8]

def log_structured(level, message, **kwargs):
    """Helper to log with structured data formatted as string."""
    # Format kwargs as string for standard logging
    if kwargs:
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        formatted_msg = f"{message} | {extra_info}"
    else:
        formatted_msg = message
    # Use the logger method without passing kwargs to avoid TypeError
    log_method = getattr(logger, level)
    log_method(formatted_msg)

# Simple metrics collection
class AuthMetrics:
    """Simple in-memory metrics collector for auth events."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self._metrics = {
            "tokens_created": 0,
            "tokens_verified": 0,
            "auth_failures": 0,
            "scope_denials": 0,
            "expired_tokens": 0,
            "invalid_tokens": 0,
            "service_tokens": {},
            "scope_requests": {}
        }
    
    def token_created(self, scopes: Set[str], service: str = None):
        self._metrics["tokens_created"] += 1
        if service:
            self._metrics["service_tokens"][service] = self._metrics["service_tokens"].get(service, 0) + 1
    
    def token_verified(self, scope: str):
        self._metrics["tokens_verified"] += 1
        self._metrics["scope_requests"][scope] = self._metrics["scope_requests"].get(scope, 0) + 1
    
    def auth_failure(self, error_type: str):
        self._metrics["auth_failures"] += 1
        if error_type == "expired":
            self._metrics["expired_tokens"] += 1
        elif error_type == "invalid":
            self._metrics["invalid_tokens"] += 1
        elif error_type == "insufficient_scope":
            self._metrics["scope_denials"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        return self._metrics.copy()

# Global metrics instance
_metrics = AuthMetrics()

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
METRICS_ENABLED = os.getenv("MCP_AUTH_METRICS", "1").lower() in ("1", "true", "yes", "on")

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

def create_token(scopes: Set[str], expiry_seconds: int = None, correlation_id: str = None, service: str = None) -> str:
    """Create a capability token with specified scopes.
    
    Args:
        scopes: Set of scope strings to grant
        expiry_seconds: Token lifetime (defaults to TOKEN_EXPIRY_SECONDS)
        correlation_id: Optional correlation ID for tracking
    
    Returns:
        Token string in format: iat:exp:scope1,scope2.signature
    """
    if expiry_seconds is None:
        expiry_seconds = TOKEN_EXPIRY_SECONDS
    
    iat = int(time.time())
    exp = iat + expiry_seconds
    scope_str = ",".join(sorted(scopes))
    payload = f"{iat}:{exp}:{scope_str}"
    
    signature = hmac.new(
        AUTH_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    token = f"{payload}.{signature}"
    
    # Log token creation and update metrics
    log_structured("info", "Token created", 
                   scopes=list(scopes), 
                   expiry_seconds=expiry_seconds,
                   correlation_id=correlation_id)
    
    _metrics.token_created(scopes, service)
    
    return token

def verify_capability(token: str, required_scope: str, correlation_id: str = None) -> dict:
    """Verify a capability token has the required scope.
    
    Args:
        token: Token string to verify
        required_scope: Scope that must be present in token
        correlation_id: Optional correlation ID for tracking
        
    Returns:
        Dict with token metadata (timestamp, scopes)
        
    Raises:
        AuthError: If token is invalid, expired, or lacks scope
    """
    # Generate correlation ID if not provided
    if correlation_id is None:
        correlation_id = new_correlation_id()
    
    if not token:
        log_structured("warning", "Token verification failed: no token provided", 
                       required_scope=required_scope,
                       correlation_id=correlation_id)
        _metrics.auth_failure("invalid")
        raise InvalidTokenError("No token provided")
    
    try:
        # Parse token - support both old and new formats
        payload, signature = token.rsplit(".", 1)
        
        # Verify signature first
        expected_sig = hmac.new(
            AUTH_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            log_structured("warning", "Token verification failed: invalid signature", 
                           required_scope=required_scope,
                           correlation_id=correlation_id)
            _metrics.auth_failure("invalid")
            raise InvalidTokenError("Invalid token signature")
        
        # Parse payload - detect format
        parts = payload.split(":")
        if len(parts) == 2:
            # Old format: iat:scopes
            iat_str, scope_str = parts
            iat = int(iat_str)
            exp = iat + TOKEN_EXPIRY_SECONDS
            token_format = "legacy"
        elif len(parts) == 3:
            # New format: iat:exp:scopes
            iat_str, exp_str, scope_str = parts
            iat = int(iat_str)
            exp = int(exp_str)
            token_format = "v2"
        else:
            raise ValueError(f"Invalid token format: expected 2 or 3 parts, got {len(parts)}")
        
        # Check expiry with small clock skew tolerance (5 seconds)
        now = time.time()
        if now > (exp + 5):
            token_age = now - iat
            log_structured("warning", "Token verification failed: expired", 
                           required_scope=required_scope,
                           token_age_seconds=token_age,
                           token_format=token_format,
                           correlation_id=correlation_id)
            _metrics.auth_failure("expired")
            raise TokenExpiredError("Token has expired")
        
        # Check scope
        granted_scopes = set(scope_str.split(",")) if scope_str else set()
        if required_scope not in granted_scopes:
            log_structured("warning", "Token verification failed: insufficient scope", 
                           required_scope=required_scope,
                           granted_scopes=list(granted_scopes),
                           correlation_id=correlation_id)
            _metrics.auth_failure("insufficient_scope")
            raise InsufficientScopeError(f"Token lacks required scope: {required_scope}")
        
        # Log successful verification and update metrics
        token_age = now - iat
        log_structured("info", "Token verification successful", 
                       required_scope=required_scope,
                       granted_scopes=list(granted_scopes),
                       token_age_seconds=token_age,
                       token_format=token_format,
                       correlation_id=correlation_id)
        
        _metrics.token_verified(required_scope)
        
        return {
            "timestamp": iat,
            "expiry": exp,
            "scopes": granted_scopes,
            "valid": True,
            "format": token_format,
            "correlation_id": correlation_id
        }
        
    except (ValueError, IndexError) as e:
        log_structured("error", "Token verification failed: malformed token", 
                       required_scope=required_scope,
                       error=str(e),
                       correlation_id=correlation_id)
        _metrics.auth_failure("invalid")
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
            correlation_id = new_correlation_id()
            
            # Log access attempt
            log_structured("info", "MCP tool access attempt", 
                           function=func.__name__,
                           required_scope=scope,
                           correlation_id=correlation_id)
            
            try:
                result = verify_capability(token, scope, correlation_id)
                
                # Call the actual function
                response = await func(*args, **kwargs)
                
                # Log successful access
                log_structured("info", "MCP tool access successful", 
                               function=func.__name__,
                               required_scope=scope,
                               correlation_id=correlation_id)
                
                return response
                
            except AuthError as e:
                log_structured("warning", "MCP tool access denied", 
                                function=func.__name__,
                                required_scope=scope,
                                error=str(e),
                                correlation_id=correlation_id)
                return {
                    "ok": False,
                    "error": "auth_error",
                    "message": str(e),
                    "required_scope": scope,
                    "correlation_id": correlation_id
                }
            except Exception as e:
                log_structured("error", "MCP tool access error", 
                                function=func.__name__,
                                required_scope=scope,
                                error=str(e),
                                correlation_id=correlation_id)
                return {
                    "ok": False,
                    "error": "internal_error", 
                    "message": str(e),
                    "correlation_id": correlation_id
                }
        
        return wrapper
    return decorator

def get_service_token(service_name: str, correlation_id: str = None) -> str:
    """Get a default token for a service with its standard scopes.
    
    Args:
        service_name: Name of service ("alert_service", "data_collector", etc.)
        correlation_id: Optional correlation ID for tracking
        
    Returns:
        Token string with default scopes for the service
    """
    scopes = DEFAULT_SCOPES.get(service_name, {"read"})
    
    log_structured("info", "Service token requested", 
                   service_name=service_name,
                   scopes=list(scopes),
                   correlation_id=correlation_id)
    
    token = create_token(scopes, correlation_id=correlation_id, service=service_name)
    return token

def get_admin_token(correlation_id: str = None) -> str:
    """Get an admin token with all scopes."""
    log_structured("warning", "Admin token requested", correlation_id=correlation_id)
    return create_token(DEFAULT_SCOPES["admin"], correlation_id=correlation_id)

# Metrics access
def get_auth_metrics() -> Dict[str, Any]:
    """Get current authentication metrics for monitoring/dashboards."""
    return _metrics.get_metrics()

def reset_auth_metrics():
    """Reset authentication metrics (useful for testing)."""
    _metrics.reset()

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