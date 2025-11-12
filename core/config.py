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
        """Load configuration from environment variables via pydantic settings."""
        from core.settings import get_settings
        s = get_settings()

        self.environment = (s.environment or "development").lower()
        self.debug = bool(s.dev_mode or self.environment == "development")

        self.auth_secret = s.mcp_auth_secret
        if not self.auth_secret and self.debug:
            import secrets
            self.auth_secret = secrets.token_urlsafe(32)
            logger.warning("Generated development auth secret. Set MCP_AUTH_SECRET in your environment for stability.")
        self.token_expiry_seconds = int(getattr(s, "mcp_token_expiry", 300) or 300)
        self.auth_metrics_enabled = bool(getattr(s, "mcp_auth_metrics", True))
        self.auth_log_level = str(getattr(s, "mcp_auth_log_level", "INFO")).upper()

        self.bus_backend = str(getattr(s, "bus_backend", "inproc")).lower()
        self.bus_redis_url = str(getattr(s, "bus_redis_url", "redis://localhost:6379/0"))
        self.bus_max_queue_size = int(getattr(s, "bus_max_queue_size", 1000) or 1000)
        self.bus_concurrency_limit = int(getattr(s, "bus_concurrency_limit", 10) or 10)

        self.database_url = str(getattr(s, "database_url", "sqlite:///./app/data.db"))

        self.openai_api_key = getattr(s, "openai_api_key", None)
        self.openai_base_url = getattr(s, "openai_base_url", None)

        self.log_level = str(getattr(s, "log_level", "INFO")).upper()
        self.log_structured = bool(getattr(s, "log_structured", True))

        self.service_host = str(getattr(s, "service_host", "0.0.0.0"))
        self.service_port = int(getattr(s, "service_port", 8000) or 8000)
    
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
        r = redis.from_url(config.bus_redis_url, decode_responses=True)
        return True
    except Exception as e:
        logger.warning(f"Redis connection check failed: {e}")
        return False

def resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

def resolve_app_db() -> Path:
    try:
        from core.settings import get_settings
        settings_path = getattr(get_settings(), "data_db", None)
    except Exception:
        settings_path = None
    env_path = os.getenv("DATA_DB")
    root = resolve_repo_root()
    base = settings_path or env_path
    if base:
        p = Path(base)
        return p if p.is_absolute() else root / p
    return root / "app" / "data.db"


def resolve_market_db() -> Path:
    root = resolve_repo_root()
    return root / "data" / "market.db"

if __name__ == "__main__":
    try:
        config = init_config()
        print("[OK] Configuration validation passed")
        print("\nCurrent configuration:")
        for key, value in config.to_dict().items():
            print(f"  {key}: {value}")
        print(f"app_db: {resolve_app_db()}")
        print(f"market_db: {resolve_market_db()}")
    except ConfigError as e:
        print(f"[ERROR] Configuration validation failed:\n{e}")
        exit(1)

