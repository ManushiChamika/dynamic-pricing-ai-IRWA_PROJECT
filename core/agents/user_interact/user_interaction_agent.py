from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class UserInteractionAgent:
    def __init__(self, user_name, model_name="gpt2"):
        self.user_name = user_name
        self.model_name = model_name

        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def get_response(self, message):
        try:
            # Encode input
            inputs = self.tokenizer.encode(message + self.tokenizer.eos_token, return_tensors="pt").to(self.device)
            # Generate output
            outputs = self.model.generate(inputs, max_length=200, pad_token_id=self.tokenizer.eos_token_id)
            # Decode
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response
        except Exception as e:
            return f"Error: {e}"