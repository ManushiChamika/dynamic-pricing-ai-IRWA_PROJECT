"""
Price Optimizer package for Dynamic Pricing project.
Contains:
- optimizer: heuristic optimizer with constraints and rationale.
- agent: async PricingOptimizerAgent orchestrating the workflow.
- mcp_server: MCP tool endpoint for optimize_price (optional if MCP installed).
"""
from .agent import PricingOptimizerAgent  # re-export for convenience

__all__ = ["optimizer", "PricingOptimizerAgent"]

