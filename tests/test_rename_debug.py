import traceback
from backend.routers.utils import generate_thread_title
from core.agents.llm_client import get_llm_client

print("=== Testing Auto-Rename for Thread 230 ===\n")

print("1. Testing LLM client...")
try:
    llm = get_llm_client()
    print(f"   LLM available: {llm.is_available()}")
    print(f"   LLM provider: {llm.provider if hasattr(llm, 'provider') else 'N/A'}")
except Exception as e:
    print(f"   Error getting LLM: {e}")
    traceback.print_exc()

print("\n2. Testing title generation...")
try:
    title = generate_thread_title(230)
    print(f"   Generated title: {title}")
except Exception as e:
    print(f"   Error: {e}")
    traceback.print_exc()
