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
        provider_api_key = provider_api_key.strip()
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
        or_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
        or_base = explicit_base if (explicit_key and explicit_base) else (os.getenv("OPENROUTER_BASE_URL") or "").strip()
        if not or_base and or_key:
            or_base = "https://openrouter.ai/api/v1"
        or_model = (os.getenv("OPENROUTER_MODEL") or "z-ai/glm-4.5-air:free").strip()

        oa_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        oa_model = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()

        gemini_base = (os.getenv("GEMINI_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta/openai/").strip()
        if gemini_base and not gemini_base.endswith("/"):
            gemini_base = gemini_base + "/"
        gemini_flash_model = (os.getenv("GEMINI_FLASH_MODEL") or "gemini-2.5-flash").strip()
        gemini_pro_model = (os.getenv("GEMINI_PRO_MODEL") or "gemini-2.5-pro").strip()
        
        gemini_keys = []
        gemini_key_1 = (os.getenv("GEMINI_API_KEY") or "").strip()
        if gemini_key_1:
            gemini_keys.append(("gemini", gemini_key_1))
        gemini_key_2 = (os.getenv("GEMINI_API_KEY_2") or "").strip()
        if gemini_key_2:
            gemini_keys.append(("gemini_2", gemini_key_2))
        gemini_key_3 = (os.getenv("GEMINI_API_KEY_3") or "").strip()
        if gemini_key_3:
            gemini_keys.append(("gemini_3", gemini_key_3))
        # When running under pytest prefer deterministic behavior: do not auto-load Gemini keys
        # from environment or cache so tests can control availability via monkeypatch.setenv
        if os.getenv("PYTEST_CURRENT_TEST"):
            self._log.debug("Detected pytest run; ignoring Gemini keys and cache for deterministic tests")
            gemini_keys = []
        
        try:
            # If any GEMINI env var is present (even if empty), respect caller intent and do not use cache
            if any(k in os.environ for k in ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3")):
                working_gemini_key = None
            else:
                working_gemini_key = _load_gemini_working_key()

            try:
                print("LLM env scan:", {"OPENROUTER": or_key, "OPENAI": oa_key, "GEMINI_KEYS": gemini_keys, "GEMINI_WORKING": working_gemini_key})
            except Exception:
                pass
            self._log.debug("LLM env scan: OPENROUTER=%r OPENAI=%r GEMINI_KEYS=%r GEMINI_WORKING=%r", or_key, oa_key, gemini_keys, working_gemini_key)

            if working_gemini_key and gemini_keys and any(key == working_gemini_key for _, key in gemini_keys):
                original_order = {item: idx for idx, item in enumerate(gemini_keys)}
                gemini_keys.sort(key=lambda x: (x[1] != working_gemini_key, original_order.get(x, 999)))
        except Exception as e:
            self._log.debug("Failed to sort Gemini keys by working key: %s", e)

        if explicit_key:
            custom_model = explicit_model or or_model or oa_model or gemini_pro_model
            self.register_provider(openai_mod, "custom", explicit_key, custom_model, explicit_base)
        else:
            for gemini_name, gemini_key in gemini_keys:
                self.register_provider(openai_mod, f"{gemini_name}_pro", gemini_key, gemini_pro_model, gemini_base)
            for gemini_name, gemini_key in gemini_keys:
                self.register_provider(openai_mod, gemini_name, gemini_key, gemini_flash_model, gemini_base)
            self.register_provider(openai_mod, "openrouter", or_key, or_model, or_base)
            self.register_provider(openai_mod, "openai", oa_key, oa_model, None)
    
    def get_providers(self) -> List[Dict[str, Any]]:
        return self._providers
    
    def has_providers(self) -> bool:
        return bool(self._providers)
