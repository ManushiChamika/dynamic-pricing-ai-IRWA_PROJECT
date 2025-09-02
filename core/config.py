import os

ENV = os.getenv("ENV", "dev").lower()

# --- DB ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# --- Pricing Feed (external data source) ---
PRICING_FEED_BASE_URL = os.getenv("PRICING_FEED_BASE_URL", "https://api.example-pricing.com")
PRICING_FEED_API_KEY = os.getenv("PRICING_FEED_API_KEY")  # ← set this to pull market data

# --- LLM (chat agent) ---
# --- LLM (chat agent) ---
# Prefer explicit LLM_* vars; fall back to OpenRouter/OpenAI names
LLM_API_KEY = (
    os.getenv("LLM_API_KEY")        # Prefer explicit
    or os.getenv("OPENROUTER_API_KEY")  
    or os.getenv("OPENAI_API_KEY")
)

LLM_BASE_URL = (
    os.getenv("LLM_BASE_URL")
    or os.getenv("OPENROUTER_BASE_URL")  # OpenRouter compatible
    or "https://openrouter.ai/api/v1/chat/completions"
)

LLM_MODEL = (
    os.getenv("LLM_MODEL")
    or os.getenv("OPENROUTER_MODEL")
    or os.getenv("OPENAI_MODEL")
    or "z-ai/glm-4.5-air:free"  # reasonable default that works on OpenRouter
)


# --- Alerts / Email ---
ALERTS_CAP_SECRET = os.getenv("ALERTS_CAP_SECRET")
SMTP_HOST = os.getenv("ALERTS_SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("ALERTS_SMTP_PORT", "587"))
SMTP_USER = os.getenv("ALERTS_SMTP_USER", "")
SMTP_PASSWORD = os.getenv("ALERTS_SMTP_PASSWORD", "")
ALERTS_SMTP_REQUIRE_TLS = os.getenv("ALERTS_SMTP_REQUIRE_TLS", "true")

# --- Misc ---
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD")
