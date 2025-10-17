
import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.chat_db import SessionLocal, Message

def find_messages_with_provider():
    with SessionLocal() as db:
        messages = db.query(Message).filter(Message.meta.isnot(None)).all()
        
        found_messages = []
        for msg in messages:
            try:
                meta = json.loads(msg.meta)
                if 'provider' in meta and meta['provider'] is not None:
                    found_messages.append({
                        'id': msg.id,
                        'thread_id': msg.thread_id,
                        'role': msg.role,
                        'content': msg.content,
                        'meta': meta
                    })
            except (json.JSONDecodeError, TypeError):
                continue
    
    return found_messages

if __name__ == "__main__":
    messages_with_provider = find_messages_with_provider()
    if messages_with_provider:
        print(json.dumps(messages_with_provider, indent=2))
    else:
        print("No messages with provider information found.")
