from __future__ import annotations

import os
import json
from typing import Dict, Any, Optional

from core.agents.llm_client import LLMClient
from .algorithms import ALGORITHMS


class LLMBrain:
	def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None, strict_ai_selection: bool | None = None):
		self.llm_client = LLMClient(api_key=api_key, base_url=base_url, model=model)
		self.strict_ai_selection = strict_ai_selection if strict_ai_selection is not None else os.getenv("STRICT_AI_SELECTION", "true").lower() == "true"
		
		if not self.llm_client.is_available():
			if self.strict_ai_selection:
				print(f"ERROR: LLM unavailable ({self.llm_client.unavailable_reason()}) and strict_ai_selection=True; AI tool selection will fail")
			else:
				print(f"WARNING: LLM unavailable ({self.llm_client.unavailable_reason()}); LLMBrain will use deterministic fallback")

	def decide_tool(self, user_intent: str, available_tools: dict[str, object], market_context: dict = None):
		tool_descriptions = []
		for name, tool_func in available_tools.items():
			if name == "rule_based":
				tool_descriptions.append({
					"name": name, 
					"description": "Conservative competitive pricing: averages competitor prices and applies 2% discount to undercut market",
					"use_case": "When maintaining market share is priority over profit margins",
					"arguments": {}
				})
			elif name == "ml_model":
				tool_descriptions.append({
					"name": name,
					"description": "Machine learning model for demand-aware pricing based on historical patterns",
					"use_case": "When sufficient historical data exists and sophisticated analysis is needed",
					"arguments": {}
				})
			elif name == "profit_maximization":
				tool_descriptions.append({
					"name": name,
					"description": "Aggressive profit-focused pricing: adds 10% markup over average competitor price",
					"use_case": "When maximizing margins is priority over market share",
					"arguments": {}
				})
			else:
				tool_descriptions.append({
					"name": name,
					"description": "Generic pricing tool",
					"use_case": "General purpose pricing",
					"arguments": {}
				})

		context_info = ""
		if market_context:
			record_count = market_context.get("record_count", 0)
			latest_price = market_context.get("latest_price")
			avg_price = market_context.get("avg_price")
			context_info = f"\nMarket Context:\n- Available competitor records: {record_count}\n"
			if latest_price: context_info += f"- Latest competitor price: ${latest_price}\n"
			if avg_price: context_info += f"- Average competitor price: ${avg_price}\n"

# Prompt-Based Classification → LLM-driven intent selection
# KeywoHeuristic → simple text-matching fallback

# NLP pattern: Instruction-following for structured JSON output (tool selection) with a keyword-based failsafe.

		prompt = (
			"You are an AI pricing agent brain. Analyze the user's request and market context to select the most appropriate pricing tool.\n\n"
			f"User Request: \"{user_intent}\"\n"
			f"{context_info}\n"
			f"Available Tools:\n{json.dumps(tool_descriptions, indent=2)}\n\n"
			"Requirements:\n"
			"1. Consider user intent, market conditions, and business objectives\n"
			"2. Choose the tool that best aligns with the stated goal\n"
			"3. Provide a brief reason for your selection\n\n"
			"Respond with ONLY a JSON object in this exact format:\n"
			'{"tool_name": "<selected_tool>", "arguments": {}, "reason": "<brief_explanation>"}'
		)

		if not self.llm_client.is_available():
			if self.strict_ai_selection:
				return {"error": "ai_selection_failed", "message": f"LLM unavailable: {self.llm_client.unavailable_reason()}"}
			else:
				intent = (user_intent or "").lower()
				if "profit" in intent or "maximize" in intent:
					return {"tool_name": "profit_maximization", "arguments": {}, "reason": "fallback: keyword 'profit' detected"}
				return {"tool_name": "rule_based", "arguments": {}, "reason": "fallback: default conservative approach"}

		try:
			raw = self.llm_client.chat(
				messages=[{"role": "user", "content": prompt}],
				max_tokens=300,
				temperature=0.0,
			)
			
			try:
				from core.agents.agent_sdk.activity_log import activity_log as act_log
				redacted_raw = raw[:100] + "..." if len(raw) > 100 else raw
				act_log.log("llm_brain", "decide_tool.request", "info", 
					message=f"provider={self.llm_client.provider()} model={self.llm_client.model} prompt_len={len(prompt)} response_len={len(raw)}", 
					details={"raw_response_preview": redacted_raw, "available_tools": list(available_tools.keys())})
			except Exception:
				pass
			
			start = raw.find("{")
			end = raw.rfind("}")
			if start == -1 or end == -1:
				return {"error": "ai_selection_failed", "message": "LLM response missing JSON format"}
			
			try:
				parsed = json.loads(raw[start : end + 1])
			except json.JSONDecodeError as e:
				return {"error": "ai_selection_failed", "message": f"Invalid JSON from LLM: {e}"}
			
			if not isinstance(parsed, dict):
				return {"error": "ai_selection_failed", "message": "LLM response not a JSON object"}
			
			tool_name = parsed.get("tool_name")
			arguments = parsed.get("arguments", {})
			reason = parsed.get("reason", "No reason provided")
			
			if not tool_name:
				return {"error": "ai_selection_failed", "message": "Missing tool_name in LLM response"}
			
			if tool_name not in available_tools:
				return {"error": "ai_selection_failed", "message": f"Invalid tool_name '{tool_name}', available: {list(available_tools.keys())}"}
			
			if not isinstance(arguments, dict):
				return {"error": "ai_selection_failed", "message": "Arguments must be a dictionary"}
			
			try:
				from core.agents.agent_sdk.activity_log import activity_log as act_log
				act_log.log("llm_brain", "decide_tool.success", "completed", 
					message=f"provider={self.llm_client.provider()} selected={tool_name} reason='{reason}'", 
					details={"tool_name": tool_name, "arguments": arguments, "reason": reason, "market_context": market_context})
			except Exception:
				pass
			
			return {"tool_name": tool_name, "arguments": arguments, "reason": reason}
			
		except Exception as e:
			try:
				from core.agents.agent_sdk.activity_log import activity_log as act_log
				act_log.log("llm_brain", "decide_tool.failed", "failed", 
					message=f"LLM request failed: {str(e)}", 
					details={"error": str(e), "provider": self.llm_client.provider(), "model": self.llm_client.model})
			except Exception:
				pass
			return {"error": "ai_selection_failed", "message": f"LLM request failed: {str(e)}"}
