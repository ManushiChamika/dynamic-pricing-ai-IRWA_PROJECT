import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.chat_db import list_threads, get_thread_messages
import json

def check_recent_messages():
    print("=" * 80)
    print("CHECKING RECENT MESSAGE MODEL/PROVIDER DATA")
    print("=" * 80)
    
    threads = list_threads()
    
    all_messages = []
    for thread in threads:
        msgs = get_thread_messages(thread.id)
        all_messages.extend(msgs)
    
    assistant_messages = [m for m in all_messages if m.role == "assistant"]
    assistant_messages.sort(key=lambda x: x.created_at, reverse=True)
    
    print(f"\nTotal assistant messages: {len(assistant_messages)}")
    print(f"\nShowing last 10 assistant messages:\n")
    
    for i, msg in enumerate(assistant_messages[:10], 1):
        meta = json.loads(msg.meta) if msg.meta else {}
        provider = meta.get("provider", "N/A")
        
        content_preview = msg.content[:50].encode('ascii', errors='replace').decode('ascii')
        
        print(f"{i}. Message ID: {msg.id}")
        print(f"   Model: {msg.model or 'N/A'}")
        print(f"   Provider (from metadata): {provider}")
        print(f"   Content preview: {content_preview}...")
        print(f"   Created: {msg.created_at}")
        print()

if __name__ == "__main__":
    check_recent_messages()
