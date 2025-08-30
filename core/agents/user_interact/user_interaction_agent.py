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

    def get_response(self, message):
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            data = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": f"You are chatting with {self.user_name}."},
                    {"role": "user", "content": message},
                ],
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"Error {response.status_code}: {response.text}"

        except Exception as e:
            return f"Exception: {str(e)}"
