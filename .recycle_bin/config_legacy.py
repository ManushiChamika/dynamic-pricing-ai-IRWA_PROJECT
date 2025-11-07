"""Legacy Config (backup)."""
import os, logging, secrets
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    pass

class Config:
    def __init__(self):
        self._load_config()
        self._validate_required()
    def _load_config(self):
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        self.debug = self.environment == "development"
        self.auth_secret = os.getenv("MCP_AUTH_SECRET")
        if not self.auth_secret and self.debug:
            self.auth_secret = secrets.token_urlsafe(32)
            logger.warning("Generated development auth secret. Set MCP_AUTH_SECRET in env.")
        self.token_expiry_seconds = int(os.getenv("MCP_TOKEN_EXPIRY", "300"))
        self.auth_metrics_enabled = os.getenv("MCP_AUTH_METRICS", "1").lower() in ("1","true","yes")
        self.auth_log_level = os.getenv("MCP_AUTH_LOG_LEVEL", "INFO").upper()
        self.bus_backend = os.getenv("BUS_BACKEND", "inproc").lower()
        self.bus_redis_url = os.getenv("BUS_REDIS_URL", "redis://localhost:6379/0")
        self.bus_max_queue_size = int(os.getenv("BUS_MAX_QUEUE_SIZE", "1000"))
        self.bus_concurrency_limit = int(os.getenv("BUS_CONCURRENCY_LIMIT", "10"))
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./app/data.db")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_structured = os.getenv("LOG_STRUCTURED", "1").lower() in ("1","true","yes")
        self.service_host = os.getenv("SERVICE_HOST", "0.0.0.0")
        self.service_port = int(os.getenv("SERVICE_PORT", "8000"))
    def _validate_required(self):
        errors=[]
        if not self.auth_secret:
            errors.append("MCP_AUTH_SECRET is required")
        elif len(self.auth_secret)<32:
            errors.append("MCP_AUTH_SECRET must be >=32 chars")
        if self.bus_backend not in ("inproc","redis"):
            errors.append("BUS_BACKEND invalid")
        if self.bus_backend=="redis" and not self.bus_redis_url.startswith("redis://"):
            errors.append("BUS_REDIS_URL must start with redis://")
        if not (1<=self.token_expiry_seconds<=86400):
            errors.append("MCP_TOKEN_EXPIRY out of range")
        if not (1<=self.bus_max_queue_size<=100000):
            errors.append("BUS_MAX_QUEUE_SIZE out of range")
        if not (1<=self.bus_concurrency_limit<=1000):
            errors.append("BUS_CONCURRENCY_LIMIT out of range")
        valid={"DEBUG","INFO","WARNING","ERROR","CRITICAL"}
        if self.log_level not in valid:
            errors.append("LOG_LEVEL invalid")
        if self.auth_log_level not in valid:
            errors.append("MCP_AUTH_LOG_LEVEL invalid")
        if errors:
            raise ConfigError("Validation failed:\n"+"\n".join(errors))
    def generate_auth_secret(self)->str:
        return secrets.token_urlsafe(32)
    def to_dict(self)->Dict[str,Any]:
        d={}
        for k,v in self.__dict__.items():
            if k.startswith('_'): continue
            if any(s in k.lower() for s in ("secret","key","password")):
                d[k] = "***MASKED***" if v else None
            else:
                d[k]=v
        return d
    def setup_logging(self):
        logging.basicConfig(level=getattr(logging,self.log_level), format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.getLogger("mcp.auth").setLevel(getattr(logging,self.auth_log_level))

_config: Optional[Config]=None

def get_config()->Config:
    global _config
    if _config is None:
        _config=Config()
    return _config

def init_config()->Config:
    global _config
    _config=Config(); _config.setup_logging(); logger.info("Configuration loaded")
    if _config.debug:
        logger.debug("Configuration: %s", _config.to_dict())
    return _config

def ensure_auth_secret():
    c=get_config()
    if not c.auth_secret:
        if c.environment=="development":
            s=c.generate_auth_secret(); logger.warning(f"Generated dev secret {s}"); c.auth_secret=s
        else:
            raise ConfigError("MCP_AUTH_SECRET required in production")

def check_redis_connection()->bool:
    c=get_config()
    if c.bus_backend!="redis": return True
    try:
        import redis.asyncio as redis; redis.from_url(c.bus_redis_url, decode_responses=True); return True
    except Exception as e:
        logger.warning(f"Redis connection check failed: {e}"); return False

def resolve_repo_root()->Path:
    return Path(__file__).resolve().parents[1]

def resolve_app_db()->Path:
    env_path=os.getenv("DATA_DB"); root=resolve_repo_root();
    if env_path:
        p=Path(env_path); return p if p.is_absolute() else root/p
    return root/"app"/"data.db"

def resolve_market_db()->Path:
    root=resolve_repo_root(); return root/"data"/"market.db"
