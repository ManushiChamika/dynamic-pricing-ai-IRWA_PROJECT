# dynamic-pricing-ai-IRWA_PROJECT  

## LLM configuration

The Streamlit app can use any available OpenAI-compatible provider in the following order:

1. **OpenRouter** (`OPENROUTER_API_KEY`, optional `OPENROUTER_BASE_URL` and `OPENROUTER_MODEL`).
2. **OpenAI** (`OPENAI_API_KEY`, optional `OPENAI_MODEL`).
3. **Gemini** via Google's OpenAI compatibility endpoint when `GEMINI_API_KEY` is set. Optional overrides:
	- `GEMINI_MODEL` (defaults to `gemini-2.0-flash`).
	- `GEMINI_BASE_URL` if you need to point at a different endpoint (defaults to `https://generativelanguage.googleapis.com/v1beta/openai/`).

Add the desired keys to `.env` and restart the app. When higher-priority providers are unavailable or return errors, the next configured provider is used before the UI falls back to non-LLM responses.