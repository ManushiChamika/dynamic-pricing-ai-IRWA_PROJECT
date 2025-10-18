"""
Price Optimizer package for Dynamic Pricing project.
Contains:
- optimizer: heuristic optimizer with constraints and rationale.
- agent: async PricingOptimizerAgent orchestrating the workflow.
- mcp_server: MCP tool endpoint for optimize_price (optional if MCP installed).
- algorithms: pricing algorithms (rule_based, ml_model, profit_maximization).
- llm_brain: LLM-powered algorithm selector.
"""
from .agent import PricingOptimizerAgent
from .algorithms import ALGORITHMS
from .optimizer import Features, optimize

__all__ = ["optimizer", "PricingOptimizerAgent", "ALGORITHMS", "Features", "optimize"]


