import os
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
import subprocess
import platform

# Load .env variables if available
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

if 'load_dotenv' in globals() and callable(load_dotenv):
    load_dotenv()

# Optional LLM helper
try:
    from core.agents.llm_client import get_llm_client  # type: ignore
except Exception:
    get_llm_client = None

# Tool implementations
try:
    from .tools import TOOLS_MAP  # type: ignore
except Exception:
    TOOLS_MAP = {}


class UserInteractionAgent:
    def __init__(self, user_name: str, mode: str = "user"):
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
        self.enable_sound = str(os.getenv("SOUND_NOTIFICATIONS", "0")).strip().lower() in {"1", "true", "yes", "on"}
        # Memory to store conversation history
        self.memory: List[Dict[str, str]] = []

        # Resolve DB paths (keep your structure; ensure distinct files)
        # You can set APP_ROOT to override the inferred root.
        default_root = Path(os.getenv("APP_ROOT", Path(__file__).resolve().parents[3]))
        self.app_db = default_root / "app" / "data.db"
        # Use a different file for market DB (adjust if your project uses another path)
        self.market_db = default_root / "data" / "market.db"

        # Last-inference metadata (populated on LLM calls)
        self.last_model: Optional[str] = None
        self.last_provider: Optional[str] = None
        self.last_usage: Dict[str, Any] = {}

    def _play_completion_sound(self):
        """Play a sound to indicate task completion (guarded by feature flag)."""
        if not getattr(self, "enable_sound", False):
            return
        try:
            system = platform.system()
            if system == 'Windows':
                # Use powershell Beep without shell=True + list
                subprocess.call(['powershell', '-c', '[console]::Beep(800,1200)'])
            elif system == 'Darwin':  # macOS
                subprocess.call(['afplay', '/System/Library/Sounds/Glass.aiff'])
            elif system == 'Linux':
                subprocess.call(['beep', '-f', '800', '-l', '1200'])
        except Exception:
            pass  # Silent failure if sound not available

    def is_dynamic_pricing_related(self, message: str) -> bool:
        message_lower = (message or "").lower()
        return any(keyword in message_lower for keyword in self.keywords)

    def add_to_memory(self, role: str, content: str):
        """Add message to memory"""
        self.memory.append({"role": role, "content": content})

    def get_response(self, message: str):
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
        - Location: core/agents/user_interact/user_interaction_agent.py

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
            "Migration:\n"
            "  OLD: uia.get_response(message)\n"
            "  NEW: for delta in uia.stream_response(message):\n"
            "           # Process delta (string or dict)\n\n"
            "API Endpoint:\n"
            "  Use: POST /api/threads/{thread_id}/messages/stream\n"
        )

    def stream_response(self, message: str):
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

        base_guidance = (
            "📊 You are a specialized assistant for the dynamic pricing system.\n"
            "🔧 You can call tools to retrieve data and recommend prices.\n"
            "⚡ When answering in streaming mode, keep responses concise and actionable.\n\n"
            "📝 *Markdown Formatting Guide* (We use react-markdown v10.1.0):\n"
            "Use proper markdown formatting to enhance clarity and engagement:\n"
            "✓ *Bold* for emphasis: **important concepts**\n"
            "✓ Italic for definitions: *key term*\n"
            "✓ Code for SKUs/variables: `` SKU-123 ``\n"
            "✓ Unordered lists: - item\n"
            "✓ Ordered lists: 1. step\n"
            "✓ Blockquotes: > callout or warning\n"
            "✓ Headers: ## Section Title\n"
            "✓ Fenced code blocks: ` sql ` (enables syntax highlighting)\n"
            "✓ Strikethrough: `~~deprecated~~ new way`\n"
            "✓ Links: `[text](url)` for references\n"
            "✓ Tables (simple): `| col | col |` for structured data\n"
            "✓ Task lists: `- [x] done` or `- [ ] pending`\n\n"
            "💡 **Markdown Renderer Strengths** (react-markdown + remark):\n"
            "✓ **100% CommonMark compliant**\n"
            "✓ **Secure by default**\n"
            "✓ **Syntax highlighting**\n"
            "✓ **GitHub Flavored Markdown** via plugins\n"
            "✓ **Safe HTML handling** (escaped)\n\n"
            "⚠ **Markdown Renderer Limitations**:\n"
            "✗ No LaTeX/mermaid/raw HTML\n"
            "✗ Keep tables simple\n\n"
            "🎯 **Best Practices**:\n"
            "• Use markdown liberally for readability\n"
            "• Prefer simple, flat tables\n"
            "• Use code blocks for SQL/JSON/Python\n"
            "• Use blockquotes for warnings/callouts\n"
        )
        user_style = (
            "👤 **User Mode Active**\n"
            "💬 Reply in a concise, user-friendly way with clear next actions.\n"
            "📚 Prefer plain language over technical details.\n"
            "🎨 Use markdown to make responses scannable.\n"
        )
        dev_style = (
            "👨‍💻 **Developer Mode Active**\n"
            "🔍 Provide structured sections (Answer, Rationale, Next Steps).\n"
            "⚙ Include technical details and context.\n"
            "📊 Use simple tables for comparisons.\n"
        )
        system_prompt = base_guidance + (dev_style if self.mode == "developer" else user_style)

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

# Tool-Streaming Chat → real-time LLM dialogue with function calling
# NLP pattern: Prompted, tool-augmented generation
#  with streaming and bounded multi-turn tool orchestration.

                    # Tool schemas matching our implementations
                    tools = [
                        {
                            "type": "function",
                            "function": {
                                "name": "list_inventory_items",
                                "description": "List items from the local product catalog (app/data.db). Use for inventory overviews.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "search": {"type": "string", "description": "Filter by substring in SKU or title."},
                                        "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                                    },
                                    "additionalProperties": False,
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "get_inventory_item",
                                "description": "Get a single inventory item by SKU from app/data.db/product_catalog.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "sku": {"type": "string", "description": "Item SKU (exact match)"},
                                    },
                                    "required": ["sku"],
                                    "additionalProperties": False,
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_pricing_list",
                                "description": "List current market pricing entries from market.db/pricing_list.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "search": {"type": "string", "description": "Filter by substring in product_name."},
                                        "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                                    },
                                    "additionalProperties": False,
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_price_proposals",
                                "description": "List recent price proposals from app/data.db/price_proposals.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "sku": {"type": "string", "description": "Optional filter by SKU"},
                                        "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                                    },
                                    "additionalProperties": False,
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_market_data",
                                "description": "List products from market.db (market research data). Find products by brand or name.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "search": {"type": "string", "description": "Filter by substring in product_name or brand."},
                                        "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                                    },
                                    "additionalProperties": False,
                                },
                            },
                        },
                    ]

                    # Map tool name to agent label for UI badges
                    def _agent_for_tool(name: Optional[str]):
                        mapping = {
                            "list_inventory_items": "UserInteractionAgent",
                            "get_inventory_item": "UserInteractionAgent",
                            "list_pricing_list": "PriceOptimizationAgent",
                            "list_price_proposals": "PriceOptimizationAgent",
                            "list_market_data": "DataCollectorAgent",
                            "run_pricing_workflow": "PriceOptimizationAgent",
                            "optimize_price": "PriceOptimizationAgent",
                            "scan_for_alerts": "AlertNotificationAgent",
                            "collect_market_data": "DataCollectorAgent",
                            "request_market_fetch": "DataCollectorAgent",
                        }
                        return mapping.get(name or "")

                    # Accumulate full content for memory on completion
                    full_parts: List[str] = []

                    try:
                        for event in llm.chat_with_tools_stream(
                            messages=msgs,
                            tools=tools,
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
                                        # Back-compat: yield as raw string
                                        yield text
                                elif et == "tool_call":
                                    name = event.get("name")
                                    status = event.get("status")
                                    if status == "start":
                                        agent = _agent_for_tool(name)
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
