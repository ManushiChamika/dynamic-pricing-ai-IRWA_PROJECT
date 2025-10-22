import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.chat_db import create_thread
from core.auth_service import validate_session_token

test_token = "xAeAl5cqwyH0TDHKExJMlM3O_w4EwYPiKyJ7Kjj8O9o"

print("Testing validate_session_token...")
try:
    sess = validate_session_token(test_token)
    print(f"[OK] Session: {sess}")
    owner_id = sess["user_id"] if sess else None
except Exception as e:
    print(f"[FAIL] Token validation failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    owner_id = None

print(f"\nTesting create_thread with owner_id={owner_id}...")
try:
    t = create_thread(title="Test Thread", owner_id=owner_id)
    print(f"[OK] Created thread: id={t.id}, title={t.title}, owner_id={t.owner_id}")
except Exception as e:
    print(f"[FAIL] Create thread failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
