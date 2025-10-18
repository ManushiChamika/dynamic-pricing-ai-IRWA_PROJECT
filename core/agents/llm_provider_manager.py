from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
import importlib


_GEMINI_WORKING_KEY_CACHE: Optional[str] = None


def _get_gemini_working_key_file() -> Path:
    root = Path(__file__).resolve().parents[2]
    cache_dir = root / ".llm_cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / "gemini_working_key.txt"


def _load_gemini_working_key() -> Optional[str]:
    try:
        cache_file = _get_gemini_working_key_file()
        if cache_file.exists():
            key = cache_file.read_text(encoding="utf-8").strip()
            return key if key else None
    except Exception as e:
        logging.getLogger("core.agents.llm").debug("Failed to load Gemini working key: %s", e)
    return None


def _save_gemini_working_key(key: str) -> None:
    try:
        if not key:
            return
        cache_file = _get_gemini_working_key_file()
        cache_file.write_text(key, encoding="utf-8")
    except Exception as e:
        logging.getLogger("core.agents.llm").debug("Failed to save Gemini working key: %s", e)


class ProviderManager:
    def __init__(self, logger: logging.Logger):
        self._log = logger
        self._providers: List[Dict[str, Any]] = []
    
    def prepare_headers(self, provider_name: str, key: str) -> Dict[str, str]:
        if provider_name == "openrouter":
            return {
                "HTTP-Referer": os.getenv("OPENROUTER_REFERRER", "https://dynamic-pricing-ai.local"),
                "X-Title": os.getenv("OPENROUTER_TITLE", "Dynamic Pricing AI"),
            }
        if provider_name == "gemini":
            return {"x-goog-api-key": key}
        return {}
    
    def register_provider(
        self,
        openai_mod: Any,
        provider_name: str,
        provider_api_key: Optional[str],
        provider_model: Optional[str],
        provider_base_url: Optional[str],
    ) -> None:
        if not provider_api_key:
            return

        model_name = provider_model or "gpt-4o-mini"
        headers = self.prepare_headers(provider_name, provider_api_key)
        kwargs: Dict[str, Any] = {"api_key": provider_api_key}
        if provider_base_url:
            kwargs["base_url"] = provider_base_url
        if headers:
            kwargs["default_headers"] = headers

        try:
            client = openai_mod.OpenAI(**kwargs)
        except TypeError:
            headers_payload = kwargs.pop("default_headers", None)
            client = openai_mod.OpenAI(**kwargs)
            if headers_payload:
                try:
                    client.default_headers = headers_payload
                except Exception:
                    pass
        except Exception as exc:
            self._log.error("Failed to initialize %s client: %s", provider_name, exc)
            return

        self._providers.append(
            {
                "name": provider_name,
                "client": client,
                "model": model_name,
                "base_url": provider_base_url,
                "api_key": provider_api_key,
            }
        )
        self._log.debug(
            "Registered provider %s | model=%s base_url=%s",
            provider_name,
            model_name,
            provider_base_url or "<default>",
        )
    
    def load_providers_from_env(
        self,
        openai_mod: Any,
        explicit_key: Optional[str] = None,
        explicit_base: Optional[str] = None,
        explicit_model: Optional[str] = None,
    ) -> None:
        or_key = os.getenv("OPENROUTER_API_KEY")
        or_base = explicit_base if (explicit_key and explicit_base) else os.getenv("OPENROUTER_BASE_URL")
        if not or_base and or_key:
            or_base = "https://openrouter.ai/api/v1"
        or_model = os.getenv("OPENROUTER_MODEL") or "z-ai/glm-4.5-air:free"

        oa_key = os.getenv("OPENAI_API_KEY")
        oa_model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

        gemini_base = os.getenv("GEMINI_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta/openai/"
        if gemini_base and not gemini_base.endswith("/"):
            gemini_base = gemini_base + "/"
        gemini_model = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        
        gemini_keys = []
        gemini_key_1 = os.getenv("GEMINI_API_KEY")
        if gemini_key_1:
            gemini_keys.append(("gemini", gemini_key_1))
        gemini_key_2 = os.getenv("GEMINI_API_KEY_2")
        if gemini_key_2:
            gemini_keys.append(("gemini_2", gemini_key_2))
        gemini_key_3 = os.getenv("GEMINI_API_KEY_3")
        if gemini_key_3:
            gemini_keys.append(("gemini_3", gemini_key_3))
        
        try:
            working_gemini_key = _load_gemini_working_key()
            if working_gemini_key and gemini_keys and any(key == working_gemini_key for _, key in gemini_keys):
                original_order = {item: idx for idx, item in enumerate(gemini_keys)}
                gemini_keys.sort(key=lambda x: (x[1] != working_gemini_key, original_order.get(x, 999)))
        except Exception as e:
            self._log.debug("Failed to sort Gemini keys by working key: %s", e)

        if explicit_key:
            custom_model = explicit_model or or_model or oa_model or gemini_model
            self.register_provider(openai_mod, "custom", explicit_key, custom_model, explicit_base)
        else:
            self.register_provider(openai_mod, "openrouter", or_key, or_model, or_base)
            self.register_provider(openai_mod, "openai", oa_key, oa_model, None)
            for gemini_name, gemini_key in gemini_keys:
                self.register_provider(openai_mod, gemini_name, gemini_key, gemini_model, gemini_base)
    
    def get_providers(self) -> List[Dict[str, Any]]:
        return self._providers
    
    def has_providers(self) -> bool:
        return bool(self._providers)
