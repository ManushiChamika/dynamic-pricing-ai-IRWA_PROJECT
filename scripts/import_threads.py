
import json
import sys
import os
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.chat_db import create_thread, add_message

def import_thread(file_path: str, filename: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        messages = json.load(f)
    
    if not messages:
        print(f"No messages found in {file_path}, skipping.")
        return

    thread = create_thread(title=filename)
    print(f"Created thread {thread.id} for {file_path}")

    for msg in messages:
        add_message(
            thread_id=thread.id,
            role=msg.get('role'),
            content=msg.get('content'),
            model=msg.get('model'),
            meta=json.dumps(msg.get('metadata')) if msg.get('metadata') else None
        )
    print(f"Imported {len(messages)} messages for thread {thread.id}")

if __name__ == "__main__":
    threads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'chat_threads'))
    for filename in os.listdir(threads_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(threads_dir, filename)
            try:
                import_thread(file_path, filename)
            except Exception as e:
                print(f"Error importing {filename}: {e}")
