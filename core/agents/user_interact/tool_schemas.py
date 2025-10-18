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
]

AGENT_TOOL_MAPPING: Dict[str, str] = {
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

def get_agent_for_tool(tool_name: Optional[str]) -> str:
    return AGENT_TOOL_MAPPING.get(tool_name or "", "")
