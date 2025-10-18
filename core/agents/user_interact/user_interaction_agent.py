import os
import sqlite3
from pathlib import Path

from datetime import datetime
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
from typing import Any, Dict, List, Optional
import subprocess
import platform

# Load .env variables if available
if 'load_dotenv' in globals() and callable(load_dotenv):
    load_dotenv()

# Optional LLM helper
try:
    from core.agents.llm_client import get_llm_client
except Exception:
    get_llm_client = None

# Tool implementations
try:
    from .tools import TOOLS_MAP
except Exception:
    TOOLS_MAP = {}

try:
    from .prompts import get_system_prompt
except Exception:
    get_system_prompt = None

try:
    from .tool_schemas import TOOL_SCHEMAS, get_agent_for_tool
except Exception:
    TOOL_SCHEMAS = []
    get_agent_for_tool = lambda name: ""

class UserInteractionAgent:
    def __init__(self, user_name, mode: str = "user"):
        self.user_name = user_name
        self.mode = (mode or "user").lower()
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.model_name = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")
        self.keywords = [
            "price", "pricing", "discount", "offer", "demand", "supply",
            "cost", "profit", "margin", "dynamic pricing", "price optimization"
        ]
        # Feature flags
        self.enable_sound = os.getenv("SOUND_NOTIFICATIONS", "0").strip() in {"1", "true", "True", "yes", "on"}
        # Memory to store conversation history
        self.memory = []
        # Resolve DB paths
        root = Path(__file__).resolve().parents[3]
        self.app_db = root / "app" / "data.db"
        self.market_db = root / "app" / "data.db"
        # Last-inference metadata (populated on LLM calls)
        self.last_model = None
        self.last_provider = None

    def _play_completion_sound(self):
        """Play a sound to indicate task completion (guarded by feature flag)."""
        if not getattr(self, "enable_sound", False):
            return
        try:
            if platform.system() == 'Windows':
                subprocess.call(['powershell', '-c', '[console]::beep(800, 1200)'], shell=True)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['afplay', '/System/Library/Sounds/Glass.aiff'])
            elif platform.system() == 'Linux':
                subprocess.call(['beep', '-f', '800', '-l', '1200'])
        except Exception:
            pass  # Silent failure if sound not available



    def is_dynamic_pricing_related(self, message):
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.keywords)

    def add_to_memory(self, role, content):
        """Add message to memory"""
        self.memory.append({"role": role, "content": content})

    def get_response(self, message):
        """Deprecated: use stream_response() instead.
        
        This method is no longer used by the chat API. The streaming endpoint
        (POST /api/threads/{thread_id}/messages/stream) uses stream_response() for
        real-time token delivery.
        
        If you need non-streaming responses, please update your client to:
        1. Call POST /api/threads/{thread_id}/messages/stream instead
        2. Collect all SSE events until completion
        
        Error Details:
        - Method: get_response() [DEPRECATED]
        - Reason: Removed to reduce code duplication and improve maintainability
        - Migration: Use stream_response() for all LLM interactions
        - Location: core/agents/user_interact/user_interaction_agent.py:71
        
        Technical Context:
        The UserInteractionAgent originally had two separate LLM paths for
        non-streaming (get_response) and streaming (stream_response) modes.
        Both methods used identical system prompts and tool definitions.
        After code review, only stream_response() was being actively used.
        
        For backward compatibility or testing, migrate to:
        - Frontend: Already uses stream_response() via SSE
        - Backend tests: Use stream_response() and collect all deltas
        - External clients: Call the /messages/stream endpoint
        """
        raise NotImplementedError(
            "❌ get_response() has been removed. Use stream_response() instead.\n\n"
            "Why: Only stream_response() was actively used. Removing get_response() "
            "simplifies the codebase and reduces maintenance burden.\n\n"
            "Migration:\n"
            "  OLD: uia.get_response(message)\n"
            "  NEW: for delta in uia.stream_response(message):\n"
            "           # Process delta (string or dict)\n\n"
            "API Endpoint:\n"
            "  Use: POST /api/threads/{thread_id}/messages/stream\n"
            "  This endpoint streams SSE events with real-time tokens.\n\n"
            "If you absolutely need to restore get_response(), please:\n"
            "  1. Check git history for the implementation\n"
            "  2. File an issue explaining the use case\n"
            "  3. We can discuss re-adding it if justified\n"
        )

    def stream_response(self, message):
        """Yield assistant tokens and structured events as they arrive from the LLM.

        - Streams text deltas for the assistant reply
        - Emits structured events for tool orchestration so the UI can show
          live agent/tool indicators while preserving backward compatibility
          (plain string chunks still stream as before)
        """
        # Add user message to memory if not already present (when called from backend, memory
        # usually already contains the assembled history plus this user turn).
        if not self.memory or self.memory[-1].get("role") != "user" or self.memory[-1].get("content") != message:
            self.add_to_memory("user", message)

        if get_system_prompt is not None:
            system_prompt = get_system_prompt(self.mode)
        else:
            system_prompt = "You are a helpful assistant."

        # Stream via LLM client
        try:
            if get_llm_client is not None:
                llm = get_llm_client()
                if llm.is_available():
                    msgs = [{"role": "system", "content": system_prompt}]
                    msgs.extend(self.memory)

                    # Params
                    try:
                        ui_max_tokens = int(os.getenv("UI_LLM_MAX_TOKENS", "0") or "0")
                    except Exception:
                        ui_max_tokens = 0
                    max_tokens_cfg = ui_max_tokens if ui_max_tokens > 0 else 1024
                    temperature = 0.2 if self.mode == "user" else 0.3

                    # Accumulate full content for memory on completion
                    full_parts: List[str] = []

                    try:
                        for event in llm.chat_with_tools_stream(
                            messages=msgs,
                            tools=TOOL_SCHEMAS,
                            functions_map=TOOLS_MAP,
                            tool_choice="auto",
                            max_rounds=(4 if self.mode == "user" else 5),
                            max_tokens=max_tokens_cfg,
                            temperature=temperature,
                        ):
                            if isinstance(event, dict):
                                et = event.get("type")
                                if et == "delta":
                                    text = event.get("text")
                                    if text:
                                        full_parts.append(text)
                                        yield text
                                elif et == "tool_call":
                                    name = event.get("name")
                                    status = event.get("status")
                                    if status == "start":
                                        agent = get_agent_for_tool(name)
                                        if agent:
                                            yield {"type": "agent", "name": agent}
                                    yield {"type": "tool_call", "name": name, "status": status}
                            else:
                                if isinstance(event, str) and event:
                                    full_parts.append(event)
                                    yield event
                    except Exception:
                        # fallback to plain token stream
                        try:
                            for chunk in llm.chat_stream(messages=msgs, max_tokens=max_tokens_cfg, temperature=temperature):
                                if chunk:
                                    full_parts.append(chunk)
                                    yield chunk
                        except Exception:
                            pass

                    # After stream complete, capture metadata and store memory
                    try:
                        self.last_model = getattr(llm, "model", None)
                        self.last_provider = llm.provider() if hasattr(llm, "provider") else None
                        self.last_usage = getattr(llm, "last_usage", {})
                    except Exception:
                        self.last_usage = {}
                    answer = ("".join(full_parts)).strip()
                    if answer:
                        self.add_to_memory("assistant", answer)
                    self._play_completion_sound()
                    return
        except Exception:
            pass

        # Fallback if LLM unavailable
        fallback = "[non-LLM assistant] LLM is not available. Please ensure the LLM client is configured properly."
        try:
            self.add_to_memory("assistant", fallback)
        except Exception:
            pass
        self._play_completion_sound()
        yield fallback



