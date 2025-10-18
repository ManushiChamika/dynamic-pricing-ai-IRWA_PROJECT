#!/usr/bin/env python3
import sys
sys.path.insert(0, r"C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT")

from core.chat_db import create_thread, add_message, list_threads, cleanup_empty_threads, delete_thread, get_thread_messages

print("=== Testing Empty Thread Prevention ===\n")

print("1. Creating test thread (empty)...")
test_thread = create_thread("Test Empty Thread", owner_id=1)
print(f"   Created thread ID {test_thread.id}")

print("\n2. Listing threads before cleanup...")
threads_before = list_threads(owner_id=1)
print(f"   Found {len(threads_before)} threads")
for t in threads_before:
    msg_count = len(get_thread_messages(t.id))
    print(f"   - Thread {t.id}: '{t.title}' ({msg_count} messages)")

print("\n3. Running cleanup_empty_threads()...")
deleted_count = cleanup_empty_threads(owner_id=1)
print(f"   Deleted {deleted_count} empty thread(s)")

print("\n4. Listing threads after cleanup...")
threads_after = list_threads(owner_id=1)
print(f"   Found {len(threads_after)} threads")
for t in threads_after:
    msg_count = len(get_thread_messages(t.id))
    print(f"   - Thread {t.id}: '{t.title}' ({msg_count} messages)")

print("\n5. Creating thread with message...")
test_thread2 = create_thread("Test With Message", owner_id=1)
msg = add_message(test_thread2.id, "user", "Hello world")
print(f"   Created thread {test_thread2.id} with message")

print("\n6. Running cleanup again...")
deleted_count = cleanup_empty_threads(owner_id=1)
print(f"   Deleted {deleted_count} empty thread(s)")

print("\n7. Final thread list...")
threads_final = list_threads(owner_id=1)
print(f"   Found {len(threads_final)} threads")
for t in threads_final:
    msg_count = len(get_thread_messages(t.id))
    print(f"   - Thread {t.id}: '{t.title}' ({msg_count} messages)")

print("\n=== Test Complete ===")
