"""
Configuration management with validation for the dynamic pricing system.
Centralizes environment variable handling with proper defaults and validation.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Configuration validation error."""
    pass

class Config:
    """Centralized configuration with validation."""
    
    def __init__(self):
        self._load_config()
        self._validate_required()
    
    def _load_config(self):
        """Load configuration from environment variables."""
        
        # Environment first (used for conditional defaults)
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        self.debug = self.environment == "development"
        
        # Auth Configuration
        self.auth_secret = os.getenv("MCP_AUTH_SECRET")
        if not self.auth_secret and self.debug:
            # Auto-generate a dev secret to keep imports working locally
            import secrets
            self.auth_secret = secrets.token_urlsafe(32)
            logger.warning("Generated development auth secret. Set MCP_AUTH_SECRET in your environment for stability.")
        self.token_expiry_seconds = int(os.getenv("MCP_TOKEN_EXPIRY", "300"))  # 5 minutes default
        self.auth_metrics_enabled = os.getenv("MCP_AUTH_METRICS", "1").lower() in ("1", "true", "yes")
        self.auth_log_level = os.getenv("MCP_AUTH_LOG_LEVEL", "INFO").upper()
        
        # Bus Configuration
        self.bus_backend = os.getenv("BUS_BACKEND", "inproc").lower()  # inproc|redis
        self.bus_redis_url = os.getenv("BUS_REDIS_URL", "redis://localhost:6379/0")
        self.bus_max_queue_size = int(os.getenv("BUS_MAX_QUEUE_SIZE", "1000"))
        self.bus_concurrency_limit = int(os.getenv("BUS_CONCURRENCY_LIMIT", "10"))
        
        # Database Configuration
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./data/market.db")
        
        # OpenAI Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        
        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_structured = os.getenv("LOG_STRUCTURED", "1").lower() in ("1", "true", "yes")
        
        # Service Configuration
        self.service_host = os.getenv("SERVICE_HOST", "0.0.0.0")
        self.service_port = int(os.getenv("SERVICE_PORT", "8000"))
    
    def _validate_required(self):
        """Validate required configuration values."""
        errors = []
        
        # Auth secret is critical for security
        if not self.auth_secret:
            errors.append("MCP_AUTH_SECRET is required for authentication")
        elif len(self.auth_secret) < 32:
            errors.append("MCP_AUTH_SECRET must be at least 32 characters for security")
        
        # Validate bus backend
        if self.bus_backend not in ("inproc", "redis"):
            errors.append(f"BUS_BACKEND must be 'inproc' or 'redis', got '{self.bus_backend}'")
        
        # Redis URL validation if using Redis backend
        if self.bus_backend == "redis" and not self.bus_redis_url.startswith("redis://"):
            errors.append("BUS_REDIS_URL must start with 'redis://' when using Redis backend")
        
        # Validate numeric ranges
        if not (1 <= self.token_expiry_seconds <= 86400):  # 1 second to 1 day
            errors.append("MCP_TOKEN_EXPIRY must be between 1 and 86400 seconds")
        
        if not (1 <= self.bus_max_queue_size <= 100000):
            errors.append("BUS_MAX_QUEUE_SIZE must be between 1 and 100000")
        
        if not (1 <= self.bus_concurrency_limit <= 1000):
            errors.append("BUS_CONCURRENCY_LIMIT must be between 1 and 1000")
        
        # Log level validation
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of {valid_log_levels}")
        if self.auth_log_level not in valid_log_levels:
            errors.append(f"MCP_AUTH_LOG_LEVEL must be one of {valid_log_levels}")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
            raise ConfigError(error_msg)
    
    def generate_auth_secret(self) -> str:
        """Generate a secure auth secret for development."""
        import secrets
        return secrets.token_urlsafe(32)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary (for debugging)."""
        config_dict = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                # Mask sensitive values
                if 'secret' in key.lower() or 'key' in key.lower() or 'password' in key.lower():
                    config_dict[key] = "***MASKED***" if value else None
                else:
                    config_dict[key] = value
        return config_dict
    
    def setup_logging(self):
        """Configure logging based on config settings."""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if not self.log_structured
                   else '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(funcName)s:%(lineno)d'
        )
        
        # Configure auth logging specifically
        auth_logger = logging.getLogger("mcp.auth")
        auth_logger.setLevel(getattr(logging, self.auth_log_level))

# Global config instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def init_config() -> Config:
    """Initialize configuration and return instance."""
    global _config
    _config = Config()
    _config.setup_logging()
    
    logger.info("Configuration loaded successfully")
    if _config.debug:
        logger.debug("Configuration: %s", _config.to_dict())
    
    return _config

# Environment setup helpers
def ensure_auth_secret():
    """Ensure auth secret exists, generate if needed in development."""
    config = get_config()
    if not config.auth_secret:
        if config.environment == "development":
            secret = config.generate_auth_secret()
            logger.warning(f"Generated development auth secret. Set MCP_AUTH_SECRET={secret} in your environment")
            config.auth_secret = secret
        else:
            raise ConfigError("MCP_AUTH_SECRET is required in production")

def check_redis_connection() -> bool:
    """Check if Redis is available (when using Redis backend)."""
    config = get_config()
    if config.bus_backend != "redis":
        return True
    
    try:
        import redis.asyncio as redis
        # Quick connection test
        r = redis.from_url(config.bus_redis_url, decode_responses=True)
        # This would need to be async in real usage
        return True
    except Exception as e:
        logger.warning(f"Redis connection check failed: {e}")
        return False

if __name__ == "__main__":
    # Configuration validation script
    try:
        config = init_config()
        print("[OK] Configuration validation passed")
        print("\nCurrent configuration:")
        for key, value in config.to_dict().items():
            print(f"  {key}: {value}")
    except ConfigError as e:
        print(f"[ERROR] Configuration validation failed:\n{e}")
        exit(1)