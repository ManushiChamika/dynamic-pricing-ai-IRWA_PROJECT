import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.chat_db import create_thread

print("Creating thread...")
t = create_thread(title="Date Test Thread", owner_id=103)

print(f"Thread created: id={t.id}")
print(f"  title: {t.title}")
print(f"  owner_id: {t.owner_id}")
print(f"  created_at: {t.created_at} (type: {type(t.created_at)})")
print(f"  updated_at: {t.updated_at} (type: {type(t.updated_at)})")

if t.created_at:
    print(f"  created_at.isoformat(): {t.created_at.isoformat()}")
else:
    print("  ERROR: created_at is None!")

if t.updated_at:
    print(f"  updated_at.isoformat(): {t.updated_at.isoformat()}")
else:
    print("  ERROR: updated_at is None!")
