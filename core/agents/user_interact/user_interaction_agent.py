import os
import requests
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

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
        if not self.is_dynamic_pricing_related(message):
            return "I'm only able to respond to queries related to the dynamic pricing system."

        # Add user message to memory
        self.add_to_memory("user", message)

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # Include memory in the system messages
            messages = [{"role": "system", "content": (
                f"You are a specialized assistant for the dynamic pricing system. "
                f"Only provide responses related to pricing strategies, discounts, "
                f"offers, demand/supply, and related financial metrics."
            )}]
            # Append previous conversation from memory
            messages.extend(self.memory)

            # Current user message
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
                # Add bot response to memory
                self.add_to_memory("assistant", answer)
                return answer
            else:
                return f"Error {response.status_code}: {response.text}"

        except Exception as e:
            return f"Exception: {str(e)}"
