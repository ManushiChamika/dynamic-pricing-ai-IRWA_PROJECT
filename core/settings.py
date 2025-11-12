from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    environment: str = "development"
    dev_mode: bool = False
    mcp_auth_secret: Optional[str] = None
    mcp_token_expiry: int = 300
    mcp_auth_metrics: bool = True
    mcp_auth_log_level: str = "INFO"
    bus_backend: str = "inproc"
    bus_redis_url: str = "redis://localhost:6379/0"
    bus_max_queue_size: int = 1000
    bus_concurrency_limit: int = 10
    database_url: str = "sqlite:///./app/data.db"
    data_db: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: Optional[str] = None
    openrouter_model: str = "deepseek/deepseek-r1-0528:free"
    gemini_api_key: Optional[str] = None
    gemini_base_url: Optional[str] = None
    summarizer_model: Optional[str] = None
    alerts_cap_secret: str = "dev-secret"
    ui_llm_max_tokens: Optional[int] = None
    llm_price_map: Optional[str] = None
    log_level: str = "INFO"
    log_structured: bool = True
    service_host: str = "0.0.0.0"
    service_port: int = 8000
    use_mcp: bool = False
    use_langchain: bool = False
    ui_require_login: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="allow", case_sensitive=False)


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
