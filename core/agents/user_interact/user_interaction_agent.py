import os
import requests
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Optional LLM helper
try:
    from app.llm_client import get_llm_client
except Exception:
    get_llm_client = None

class UserInteractionAgent:
    def __init__(self, user_name):
        self.user_name = user_name
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.model_name = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")
        self.keywords = [
            "price", "pricing", "discount", "offer", "demand", "supply",
            "cost", "profit", "margin", "dynamic pricing", "price optimization"
        ]
        # Memory to store conversation history
        self.memory = []

    def is_dynamic_pricing_related(self, message):
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.keywords)

    def add_to_memory(self, role, content):
        """Add message to memory"""
        self.memory.append({"role": role, "content": content})

    def get_response(self, message):
        """Return an LLM-powered response for any query when available.

        Behavior:
        - If an LLM client is available, forward the message (with memory/system prompt) and return the model answer.
        - If LLM is not available, keep the original keyword guard but return an explicit non-LLM fallback message so callers know it's not the LLM speaking.
        """

        # Add user message to memory
        self.add_to_memory("user", message)

        # Build system prompt focused on dynamic pricing
        system_prompt = (
            f"You are a specialized assistant for the dynamic pricing system. "
            f"Only provide responses related to pricing strategies, discounts, "
            f"offers, demand/supply, and related financial metrics."
        )

        # Attempt to use LLM client if available
        try:
            if get_llm_client is not None:
                llm = get_llm_client()
                if llm.is_available():
                    msgs = [{"role": "system", "content": system_prompt}]
                    msgs.extend(self.memory)
                    msgs.append({"role": "user", "content": message})
                    try:
                        answer = llm.chat(msgs)
                        # Add assistant reply to memory
                        self.add_to_memory("assistant", answer)
                        return answer
                    except Exception as e:
                        # Fall through to explicit non-LLM fallback
                        pass

        except Exception:
            # Any error while attempting LLM shouldn't crash; we'll fall back
            pass

        # LLM not available or failed. Use keyword guard to determine messaging; but mark as non-LLM.
        if not self.is_dynamic_pricing_related(message):
            return "[non-LLM assistant] I'm only able to respond to queries related to the dynamic pricing system."

        # As a last resort, attempt the previous direct HTTP OpenRouter path (preserves compatibility)
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.memory)
            messages.append({"role": "user", "content": message})

            data = {
                "model": self.model_name,
                "messages": messages
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                answer = response.json()["choices"][0]["message"]["content"]
                self.add_to_memory("assistant", answer)
                return answer
            else:
                return f"[non-LLM assistant] Error {response.status_code}: {response.text}"

        except Exception as e:
            return f"[non-LLM assistant] Exception: {str(e)}"
