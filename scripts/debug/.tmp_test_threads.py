from core.chat_db import list_threads
import traceback

try:
    result = list_threads(owner_id=103)
    print(f"Success: {result}")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
