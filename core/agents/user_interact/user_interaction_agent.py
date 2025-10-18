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

        base_guidance = (
            "📊 You are a specialized assistant for the dynamic pricing system.\n"
            "🔧 You can call tools to retrieve data and recommend prices.\n"
            "⚡ When answering in streaming mode, keep responses concise and actionable.\n\n"
            "📝 **Markdown Formatting Guide** (We use react-markdown v10.1.0):\n"
            "Use proper markdown formatting to enhance clarity and engagement:\n"
            "✓ **Bold** for emphasis: `**important concepts**`\n"
            "✓ *Italic* for definitions: `*key term*`\n"
            "✓ `Code` for SKUs/variables: `` `SKU-123` ``\n"
            "✓ Unordered lists: `- item`\n"
            "✓ Ordered lists: `1. step`\n"
            "✓ Blockquotes: `> callout or warning`\n"
            "✓ Headers: `## Section Title`\n"
            "✓ Fenced code blocks: ` ```sql ` (enables syntax highlighting)\n"
            "✓ Strikethrough: `~~deprecated~~ new way`\n"
            "✓ Links: `[text](url)` for references\n"
            "✓ Tables (simple): `| col | col |` for structured data\n"
            "✓ Task lists: `- [x] done` or `- [ ] pending`\n\n"
            "💡 **Markdown Renderer Strengths** (react-markdown + remark):\n"
            "✓ **100% CommonMark compliant** - rock-solid standard markdown support\n"
            "✓ **Secure by default** - no XSS vulnerabilities or dangerouslySetInnerHTML\n"
            "✓ **Syntax highlighting** - fenced code blocks with language detection\n"
            "✓ **Component flexibility** - swap elements with custom React components\n"
            "✓ **GitHub Flavored Markdown** - strikethrough, task lists, tables via plugins\n"
            "✓ **Nested structures** - deeply nested lists and mixed formatting\n"
            "✓ **Safe HTML handling** - HTML is escaped unless explicitly trusted\n"
            "✓ **Extensible** - supports remark/rehype plugins for custom syntax\n"
            "✓ **Emoji support** - professional emojis render naturally 📈 💰 ✅ ⚠️\n"
            "✓ **Link transformation** - automatic URL validation and sanitization\n\n"
            "⚠️ **Markdown Renderer Limitations** (react-markdown):\n"
            "✗ **No inline LaTeX** - math expressions like `$x^2$` are NOT supported\n"
            "✗ **No block LaTeX** - display math equations NOT supported\n"
            "✗ **No raw HTML** - HTML tags will be escaped/removed (by design for safety)\n"
            "✗ **No Mermaid diagrams** - flowcharts/sequence diagrams not supported\n"
            "✗ **No HTML class styling** - custom CSS classes cannot be applied\n"
            "✗ **No footnotes** - use inline references in parentheses instead\n"
            "✗ **No definition lists** - use blockquotes or simple text instead\n"
            "✗ **Table limitations** - avoid deeply nested cells; keep structure simple\n"
            "✗ **No custom directives** - special syntax like `:::note` not supported\n\n"
            "🎯 **Best Practices**:\n"
            "• Use markdown liberally - it significantly improves readability\n"
            "• Keep tables simple and flat - avoid nested cells or complex formatting\n"
            "• Use code blocks for technical output (SQL, JSON, Python)\n"
            "• Use blockquotes for warnings or important callouts\n"
            "• For mathematical content, use plain text: `profit = (price - cost) * quantity`\n"
        )
        user_style = (
            "👤 **User Mode Active**\n"
            "💬 Reply in a concise, user-friendly way with clear next actions.\n"
            "📚 Prefer plain language over technical details.\n"
            "🎨 Use markdown to make responses scannable and well-organized.\n"
            "✨ Add strategic emojis to guide attention to key metrics.\n\n"
            "🎯 **Response Protocol**:\n"
            "• Be concise - deliver only essential information\n"
            "• Anticipate what the user wants to do next based on their query\n"
            "• Always end responses with 3-6 brief numbered options for next actions\n"
            "• Format options as: `1. [Action description]`\n"
            "• User can reply with just a number to select an option\n"
            "• Example:\n"
            "  1. View detailed pricing for this product\n"
            "  2. Compare with competitor prices\n"
            "  3. Generate new price proposal\n"
            "  4. Check inventory status\n\n"
            "🎨 **Visual Response Enhancement**:\n"
            "• Use abundant emojis throughout responses - they guide attention and add personality\n"
            "• Incorporate simple ASCII art for visual emphasis (use sparingly for key sections)\n"
            "• Leverage all supported markdown features:\n"
            "  - **Bold** for emphasis and key metrics\n"
            "  - *Italic* for definitions and context\n"
            "  - `Code blocks` for SKUs, IDs, and technical values\n"
            "  - Headers (##, ###) to structure information\n"
            "  - Blockquotes (>) for warnings, insights, or callouts\n"
            "  - Strikethrough for deprecated/old values\n"
            "  - Links for references\n"
            "• Use tables for data comparison:\n"
            "  - Product specs comparison | Price comparison | Historical analysis\n"
            "  - Keep tables simple and flat, avoid nested cells\n"
            "• Use bullet points for lists:\n"
            "  - Key features\n"
            "  - Action items\n"
            "  - Recommendation details\n"
            "• Use ordered lists (1. 2. 3.) for sequential steps\n"
            "• Use task lists for tracking items: `- [x] Completed` or `- [ ] Pending`\n"
            "• Create visual hierarchy with varied formatting - don't use plain text walls\n"
            "• Balance visual richness with readability - enhance clarity, not clutter\n"
        )
        dev_style = (
            "👨‍💻 **Developer Mode Active**\n"
            "🔍 Provide structured output sections (Answer, Rationale, Next Steps).\n"
            "⚙️ Include technical details and implementation context.\n"
            "📋 Format code examples with syntax highlighting (` ```language `).\n"
            "📊 Use simple, clear tables for data comparison.\n"
            "📈 Include relevant metrics and technical specifications."
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
                                "description": "List current market pricing entries from app/data.db/pricing_list.",
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
                                "description": "List products from app/data.db (market research data). Use this to find products by brand or name in market data.",
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



