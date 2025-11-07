from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    environment: str = "development"
    mcp_auth_secret: Optional[str] = None
    mcp_token_expiry: int = 300
    mcp_auth_metrics: bool = True
    mcp_auth_log_level: str = "INFO"
    bus_backend: str = "inproc"
    bus_redis_url: str = "redis://localhost:6379/0"
    bus_max_queue_size: int = 1000
    bus_concurrency_limit: int = 10
    database_url: str = "sqlite:///./app/data.db"
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_base_url: Optional[str] = None
    log_level: str = "INFO"
    log_structured: bool = True
    service_host: str = "0.0.0.0"
    service_port: int = 8000
    use_mcp: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="allow", case_sensitive=False)


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()