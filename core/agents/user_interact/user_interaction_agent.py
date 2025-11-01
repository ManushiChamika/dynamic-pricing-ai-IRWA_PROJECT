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
            "You are the Interaction Agent for the Dynamic Pricing AI platform.\n"
            "Coordinate specialised agents via tool calls, then narrate the results clearly for the user.\n"
            "Ask for any missing product details before triggering workflows.\n"
            "Always highlight which agents contributed, key price recommendations, market shifts, and suggested next actions.\n"
            "Use markdown with short sections such as Summary, Recommendation, Market Snapshot, Alerts, Next Steps.\n"
        )
        user_style = (
            "User mode:\n"
            "- Keep answers concise and approachable.\n"
            "- Emphasise the numbers that matter (price, confidence, gaps).\n"
            "- Offer at most two actionable next steps.\n"
        )
        dev_style = (
            "Developer mode:\n"
            "- Present sections: Summary, Details, Evidence, Next Steps.\n"
            "- Reference tool outputs explicitly for traceability.\n"
            "- Include tables or bullet lists for multi-item data.\n"
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
                                "name": "register_product",
                                "description": "Create or update a product in the catalog and capture competitor sources.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string", "description": "Product name provided by the user."},
                                        "cost": {"type": "number", "minimum": 0, "description": "Unit cost in user currency."},
                                        "sku": {"type": "string", "description": "Preferred SKU; auto-generated if missing."},
                                        "currency": {"type": "string", "description": "Currency code such as USD or EUR."},
                                        "list_price": {"type": "number", "minimum": 0, "description": "Optional starting list price."},
                                        "stock": {"type": "integer", "description": "Available inventory units."},
                                        "competitor_urls": {"type": "array", "items": {"type": "string"}, "description": "Competitor URLs or identifiers to monitor."},
                                        "market": {"type": "string", "description": "Market/region label (defaults to DEFAULT)."},
                                        "notes": {"type": "string", "description": "Additional context to store with the product."}
                                    },
                                    "required": ["title"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "run_agent_workflow",
                                "description": "Supervisor workflow that registers the product, gathers market data, optimises pricing, and compiles alerts.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "cost": {"type": "number", "minimum": 0},
                                        "sku": {"type": "string"},
                                        "currency": {"type": "string"},
                                        "list_price": {"type": "number", "minimum": 0},
                                        "stock": {"type": "integer"},
                                        "competitor_urls": {"type": "array", "items": {"type": "string"}},
                                        "market": {"type": "string"},
                                        "notes": {"type": "string"},
                                        "user_intent": {"type": "string", "description": "Summary of the user's pricing goal."}
                                    },
                                    "required": ["title"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "collect_market_data",
                                "description": "Invoke the Data Collection Agent to gather competitor quotes for a SKU.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "sku": {"type": "string"},
                                        "competitor_urls": {"type": "array", "items": {"type": "string"}},
                                        "market": {"type": "string"},
                                        "depth": {"type": "integer", "minimum": 1, "maximum": 10, "default": 3}
                                    },
                                    "required": ["sku"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "request_market_fetch",
                                "description": "Alias for collect_market_data when the user explicitly requests a fetch.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "sku": {"type": "string"},
                                        "competitor_urls": {"type": "array", "items": {"type": "string"}},
                                        "market": {"type": "string"},
                                        "depth": {"type": "integer", "minimum": 1, "maximum": 10, "default": 3}
                                    },
                                    "required": ["sku"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "optimize_price",
                                "description": "Run the Pricing Optimizer Agent for an existing SKU.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "sku": {"type": "string"},
                                        "user_goal": {"type": "string", "description": "Goal e.g. maximise profit or defend share."},
                                        "refresh_market": {"type": "boolean", "description": "Collect fresh market data before optimising."}
                                    },
                                    "required": ["sku"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "run_pricing_workflow",
                                "description": "Compatibility wrapper around optimize_price.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "sku": {"type": "string"},
                                        "user_goal": {"type": "string"},
                                        "refresh_market": {"type": "boolean"}
                                    },
                                    "required": ["sku"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "scan_for_alerts",
                                "description": "Query the Alert Agent for outstanding warnings.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "sku": {"type": "string", "description": "Optional SKU to scope the check."},
                                        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20}
                                    },
                                    "additionalProperties": False
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_inventory_items",
                                "description": "List items from the local product catalog.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "search": {"type": "string", "description": "Filter by substring in SKU or title."},
                                        "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}
                                    },
                                    "additionalProperties": False
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "get_inventory_item",
                                "description": "Fetch a single inventory record by SKU.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "sku": {"type": "string"}
                                    },
                                    "required": ["sku"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_pricing_list",
                                "description": "List stored optimisation results.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "search": {"type": "string"},
                                        "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}
                                    },
                                    "additionalProperties": False
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_price_proposals",
                                "description": "List historical price proposals.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "sku": {"type": "string", "description": "Optional SKU filter."},
                                        "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}
                                    },
                                    "additionalProperties": False
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_market_data",
                                "description": "List captured competitor quotes.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "search": {"type": "string"},
                                        "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}
                                    },
                                    "additionalProperties": False
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "execute_sql",
                                "description": "Developer-only helper for explicit SQL queries.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "database": {"type": "string", "enum": ["app", "market", "data"], "description": "Database alias (defaults to app)."},
                                        "query": {"type": "string", "description": "SQL query to execute."}
                                    },
                                    "required": ["query"],
                                    "additionalProperties": False
                                }
                            }
                        }
                    ]

                    # Map tool name to agent label for UI badges
                    def _agent_for_tool(name: Optional[str]):
                        mapping = {
                            "register_product": "Supervisor Agent",
                            "run_agent_workflow": "Supervisor Agent",
                            "collect_market_data": "Data Collection Agent",
                            "request_market_fetch": "Data Collection Agent",
                            "optimize_price": "Pricing Optimizer Agent",
                            "run_pricing_workflow": "Pricing Optimizer Agent",
                            "scan_for_alerts": "Alert Agent",
                            "list_inventory_items": "Interaction Agent",
                            "get_inventory_item": "Interaction Agent",
                            "list_pricing_list": "Pricing Optimizer Agent",
                            "list_price_proposals": "Pricing Optimizer Agent",
                            "list_market_data": "Data Collection Agent",
                            "execute_sql": "Supervisor Agent"
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
