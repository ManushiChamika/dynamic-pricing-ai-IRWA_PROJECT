import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import os
from core.agents.llm_client import LLMClient
import logging

logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

def test_provider_verification():
    print("=" * 80)
    print("LLM PROVIDER VERIFICATION TEST")
    print("=" * 80)
    
    print("\n1. CHECKING CONFIGURATION")
    print("-" * 80)
    or_key = os.getenv("OPENROUTER_API_KEY", "")
    oa_key = os.getenv("OPENAI_API_KEY", "")
    gemini_keys_str = os.getenv("GEMINI_API_KEY", "")
    gemini_keys = [k.strip() for k in gemini_keys_str.split(",") if k.strip()]
    
    print(f"OpenRouter Key Present: {bool(or_key)}")
    print(f"OpenRouter Key (first 10 chars): {or_key[:10] if or_key else 'N/A'}")
    print(f"OpenRouter Model: {os.getenv('OPENROUTER_MODEL', 'default')}")
    print(f"OpenAI Key Present: {bool(oa_key)}")
    print(f"OpenAI Key (first 10 chars): {oa_key[:10] if oa_key else 'N/A'}")
    print(f"OpenAI Model: {os.getenv('OPENAI_MODEL', 'default')}")
    print(f"Gemini Keys Count: {len(gemini_keys)}")
    print(f"Gemini Model: {os.getenv('GEMINI_MODEL', 'default')}")
    
    print("\n2. INITIALIZING LLM CLIENT")
    print("-" * 80)
    client = LLMClient()
    
    print(f"Client Available: {client.is_available()}")
    print(f"Total Providers Registered: {len(client._providers)}")
    print(f"Active Provider Index: {client._active_index}")
    print(f"Active Provider Name: {client.provider()}")
    print(f"Active Model: {client.model}")
    
    print("\n3. REGISTERED PROVIDERS LIST")
    print("-" * 80)
    for idx, provider in enumerate(client._providers):
        is_active = " [ACTIVE]" if idx == client._active_index else ""
        print(f"  [{idx}] {provider['name']:20s} | {provider['model']:40s}{is_active}")
    
    print("\n4. TESTING ACTUAL API CALL")
    print("-" * 80)
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello from provider test' and nothing else."}
    ]
    
    try:
        print("Sending test message...")
        response = client.chat(test_messages, max_tokens=50, temperature=0.1)
        print(f"\n[SUCCESS] Response received: {response}")
        
        print("\n5. USAGE METADATA")
        print("-" * 80)
        if client.last_usage:
            for key, value in client.last_usage.items():
                print(f"  {key}: {value}")
        else:
            print("  No usage metadata available")
        
        print("\n6. PROVIDER AFTER API CALL")
        print("-" * 80)
        print(f"Current Provider: {client.provider()}")
        print(f"Current Model: {client.model}")
        print(f"Active Index: {client._active_index}")
        
    except Exception as e:
        print(f"\n[FAILED] API Call Failed: {e}")
        print("\nAttempting to check fallback behavior...")
        print(f"Provider after failure: {client.provider()}")
        print(f"Model after failure: {client.model}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_provider_verification()
