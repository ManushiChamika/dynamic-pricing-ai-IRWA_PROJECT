import os
import logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(name)s: %(message)s')

os.environ["DEBUG_LLM"] = "1"

from core.agents.llm_client import get_llm_client

def test_title_generation():
    print("\n=== Testing Title Generation ===\n")
    
    llm = get_llm_client()
    print(f"LLM Available: {llm.is_available()}")
    print(f"Provider: {llm.provider()}")
    print(f"Model: {llm.model}")
    
    if not llm.is_available():
        print(f"LLM unavailable: {llm.unavailable_reason()}")
        return
    
    transcript = """User queries:
- what is 2+2
- tell me about python
- how do I read a file

Assistant responses (summarized):
- 4
- Python is a programming language
- Use open() function"""
    
    system = (
        "You are a helpful assistant that creates concise, meaningful thread titles. "
        "Analyze the conversation and generate a 4-6 word title that captures the main topic or goal. "
        "Return ONLY the title text, nothing else."
    )
    prompt = f"Generate a thread title based on this conversation:\n\n{transcript}"
    
    print("\n=== Sending Request ===")
    print(f"System: {system[:50]}...")
    print(f"Prompt: {prompt[:100]}...")
    
    try:
        title = llm.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ], max_tokens=200, temperature=0.3)
        
        print(f"\n=== Response ===")
        print(f"Title: '{title}'")
        print(f"Length: {len(title)}")
        print(f"Type: {type(title)}")
        print(f"Repr: {repr(title)}")
        
        if llm.last_usage:
            print(f"\n=== Usage ===")
            for k, v in llm.last_usage.items():
                print(f"  {k}: {v}")
        
    except Exception as e:
        print(f"\n=== ERROR ===")
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_title_generation()
