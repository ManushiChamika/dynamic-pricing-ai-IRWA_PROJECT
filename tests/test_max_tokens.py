import os
import logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(name)s: %(message)s')

os.environ["DEBUG_LLM"] = "1"

from core.agents.llm_client import get_llm_client

def test_various_max_tokens():
    print("\n=== Testing Various max_tokens Values ===\n")
    
    llm = get_llm_client()
    if not llm.is_available():
        print(f"LLM unavailable: {llm.unavailable_reason()}")
        return
    
    simple_prompt = [
        {"role": "user", "content": "Say 'hello' and nothing else"}
    ]
    
    for max_tok in [10, 20, 50, 100, 200]:
        print(f"\n--- Testing max_tokens={max_tok} ---")
        try:
            result = llm.chat(simple_prompt, max_tokens=max_tok, temperature=0.3)
            print(f"Result: '{result}'")
            print(f"Length: {len(result)}")
            if llm.last_usage:
                print(f"Completion tokens: {llm.last_usage.get('completion_tokens', 'N/A')}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_various_max_tokens()
