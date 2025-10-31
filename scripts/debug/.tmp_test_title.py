import sys
import traceback
from core.chat_db import get_thread_messages
from typing import Optional, List

def debug_generate_thread_title(thread_id: int) -> Optional[str]:
    print(f"Step 1: Importing LLM client...")
    try:
        from core.agents.llm_client import get_llm_client
        print("  OK Import successful")
    except Exception as e:
        print(f"  FAIL Import failed: {e}")
        return None

    print(f"Step 2: Getting messages...")
    msgs = get_thread_messages(thread_id)
    print(f"  Total messages: {len(msgs)}")
    if len(msgs) < 2:
        print(f"  FAIL Not enough messages (need at least 2)")
        return None
    print("  OK Message count OK")

    user_msgs = [m for m in msgs if m.role == "user"]
    assistant_msgs = [m for m in msgs if m.role == "assistant"]
    print(f"  User messages: {len(user_msgs)}")
    print(f"  Assistant messages: {len(assistant_msgs)}")

    if not user_msgs:
        print(f"  FAIL No user messages found")
        return None
    print("  OK User messages OK")

    print(f"Step 3: Getting LLM client...")
    try:
        llm = get_llm_client()
        print(f"  OK LLM client created")
        print(f"  is_available: {llm.is_available()}")
        if not llm.is_available():
            print(f"  FAIL LLM not available")
            return None
        print("  OK LLM available")
    except Exception as e:
        print(f"  FAIL Exception getting LLM: {e}")
        traceback.print_exc()
        return None

    print(f"Step 4: Building context...")
    context_parts: List[str] = []
    context_parts.append("User queries:")
    for um in user_msgs[-5:]:
        text = um.content.replace("\n", " ").strip()
        if len(text) > 200:
            text = text[:200] + "..."
        context_parts.append(f"- {text}")
    
    from backend.routers.utils import summarize_assistant_response
    context_parts.append("\nAssistant responses (summarized):")
    for am in assistant_msgs[-5:]:
        summary = summarize_assistant_response(am.content)
        if summary:
            summary_preview = summary.split("\n")[0][:150]
            context_parts.append(f"- {summary_preview}")

    transcript = "\n".join(context_parts)
    print(f"  Transcript length: {len(transcript)} chars")

    print(f"Step 5: Calling LLM...")
    try:
        system = (
            "You are a helpful assistant that creates concise, meaningful thread titles. "
            "Analyze the conversation and generate a 4-6 word title that captures the main topic or goal. "
            "Return ONLY the title text, nothing else."
        )
        prompt = f"Generate a thread title based on this conversation:\n\n{transcript}"
        print(f"  Sending request to LLM...")
        title = llm.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ], max_tokens=50, temperature=0.3)
        print(f"  Raw LLM response: {repr(title)}")
        
        title = title.strip() if title else None
        print(f"  Stripped title: {repr(title)}")
        
        if title:
            word_count = len(title.split())
            print(f"  Word count: {word_count}")
            if word_count <= 10:
                print(f"  OK Title valid")
                return title
            else:
                print(f"  FAIL Too many words (>{10})")
        else:
            print(f"  FAIL Empty title")
        return None
    except Exception as e:
        print(f"  FAIL LLM call failed: {e}")
        traceback.print_exc()
        return None

thread_id = 431
print(f"=== Testing generate_thread_title for thread {thread_id} ===\n")
result = debug_generate_thread_title(thread_id)
print(f"\n=== Final Result: {repr(result)} ===")
