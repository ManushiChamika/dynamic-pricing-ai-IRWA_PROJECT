from typing import Dict, List, Optional

TOOL_SCHEMAS = [
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
    {
        "type": "function",
        "function": {
            "name": "optimize_price",
            "description": "Request autonomous price optimization for a product SKU. The Price Optimizer Agent will analyze market data, run pricing algorithms, validate constraints, and publish a price proposal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "description": "Product SKU to optimize pricing for"},
                },
                "required": ["sku"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_stale_market_data",
            "description": "Check for market data entries that are older than a specified threshold. Returns count and details of stale items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "threshold_minutes": {"type": "integer", "description": "Age threshold in minutes. Default is 60.", "default": 60, "minimum": 1},
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scan_for_alerts",
            "description": "Scan for and retrieve all pricing alerts and incidents from the incidents table. Returns open, acknowledged, and resolved alerts with severity levels and details.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
]

AGENT_TOOL_MAPPING: Dict[str, str] = {
    "list_inventory_items": "UserInteractionAgent",
    "get_inventory_item": "UserInteractionAgent",
    "list_pricing_list": "PriceOptimizationAgent",
    "list_price_proposals": "PriceOptimizationAgent",
    "list_market_data": "DataCollectorAgent",
    "check_stale_market_data": "DataCollectorAgent",
    "run_pricing_workflow": "PriceOptimizationAgent",
    "optimize_price": "PriceOptimizationAgent",
    "scan_for_alerts": "AlertNotificationAgent",
    "collect_market_data": "DataCollectorAgent",
    "request_market_fetch": "DataCollectorAgent",
}

def get_agent_for_tool(tool_name: Optional[str]) -> str:
    return AGENT_TOOL_MAPPING.get(tool_name or "", "")
