# Minimal stub for run_pricing_optimizer
import asyncio

async def run_pricing_optimizer():
	print("[pricing_optimizer] Running pricing optimizer...")
	await asyncio.sleep(2)
	print("[pricing_optimizer] Finished pricing optimizer run.")
# core/agents/pricing_optimizer.py

import os
import re
import json
import sqlite3
import time
import importlib
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


# Load .env from project root if present (simple loader, no extra deps)
def _load_dotenv_if_present():
	# If key already present, skip
	if os.getenv("OPENAI_API_KEY"):
		return
	# Project root is two parents up from this file (core/agents/...)
	root = Path(__file__).resolve().parents[2]
	env_path = root / ".env"
	if not env_path.exists():
		return
	try:
		with env_path.open("r", encoding="utf-8") as f:
			for line in f:
				line = line.strip()
				if not line or line.startswith("#"):
					continue
				if "=" not in line:
					continue
				k, v = line.split("=", 1)
				k = k.strip()
				v = v.strip().strip('"').strip("'")
				if k and not os.getenv(k):
					os.environ[k] = v
	except Exception:
		pass


# attempt to load .env early
_load_dotenv_if_present()

# --- Step 1: Tools (algorithms) ---

def rule_based(records):
	"""
	Conservative competitive pricing algorithm:
	- Analyzes competitor price distribution
	- Applies 2% discount to median competitor price for market share
	- Uses weighted average favoring recent prices
	"""
	if not records:
		return None
	
	prices = [r[0] for r in records]
	if len(prices) == 1:
		return round(prices[0] * 0.98, 2)
	
	# Weighted average (more recent prices have higher weight)
	weights = list(range(1, len(prices) + 1))
	weighted_avg = sum(p * w for p, w in zip(prices, weights)) / sum(weights)
	
	# Apply conservative 2% discount for competitive positioning
	competitive_price = weighted_avg * 0.98
	
	print(f"[rule_based] Analyzed {len(prices)} competitor prices, weighted avg: ${weighted_avg:.2f}, competitive price: ${competitive_price:.2f}")
	return round(competitive_price, 2)


def ml_model(records):
	"""
	Advanced ML-inspired pricing model:
	- Analyzes price volatility and trends
	- Considers market positioning based on price range
	- Applies dynamic adjustment based on competitive density
	"""
	if not records:
		return None
	
	prices = [r[0] for r in records]
	
	# Calculate statistics
	avg_price = sum(prices) / len(prices)
	min_price = min(prices)
	max_price = max(prices)
	price_range = max_price - min_price
	
	# Volatility-based adjustment
	if len(prices) > 1:
		volatility = price_range / avg_price if avg_price > 0 else 0
		# Lower volatility = more stable market = can price closer to average
		# Higher volatility = unstable market = price more conservatively
		volatility_factor = 1.0 - (volatility * 0.1)  # Adjust by up to 10%
	else:
		volatility_factor = 1.0
	
	# Market positioning (slightly above average for quality perception)
	ml_price = avg_price * 1.02 * volatility_factor
	
	print(f"[ml_model] Market analysis: avg=${avg_price:.2f}, range=${price_range:.2f}, volatility={volatility:.3f}, ML price: ${ml_price:.2f}")
	return round(ml_price, 2)


def profit_maximization(records):
	"""
	Aggressive profit-focused pricing strategy:
	- Targets premium market positioning
	- Analyzes competitor price ceiling
	- Applies strategic markup based on market gaps
	"""
	if not records:
		# Fallback: assume $100 baseline for premium positioning
		base_price = 100.0  
		premium_price = base_price * 1.25
		print(f"[profit_maximization] No market data, using premium baseline: ${premium_price:.2f}")
		return round(premium_price, 2)
	
	prices = [r[0] for r in records]
	avg_price = sum(prices) / len(prices)
	max_price = max(prices)
	
	# Strategic markup: position between average and maximum competitor price
	# This captures value while remaining competitive
	if max_price > avg_price * 1.1:  # If there's a premium segment
		target_price = avg_price + (max_price - avg_price) * 0.7  # Position at 70% toward premium
	else:
		target_price = avg_price * 1.15  # Standard 15% markup
	
	# Ensure minimum 10% markup over average for profit
	profit_price = max(target_price, avg_price * 1.10)
	
	print(f"[profit_maximization] Premium strategy: avg=${avg_price:.2f}, max=${max_price:.2f}, profit price: ${profit_price:.2f}")
	return round(profit_price, 2)


# Toolbox mapping (dictionary of available tools) - removed web scraping
TOOLS = {
	"rule_based": rule_based,
	"ml_model": ml_model,
	"profit_maximization": profit_maximization,
}


# --- Step 2: LLM Brain ---

class LLMBrain:
	"""
	The LLM acts as the 'brain' of the Pricing Optimizer Agent.
	It decides which tool/algorithm to use based on user intent and data context.
	"""

	def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None, strict_ai_selection: bool | None = None):
		# Try to import OpenAI dynamically. If not available, fall back to None
		# Prefer explicitly passed api_key, else try OPENROUTER_API_KEY then OPENAI_API_KEY
		api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
		base_url = base_url or os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"
		self.model = model or os.getenv("OPENROUTER_MODEL") or os.getenv("OPENAI_MODEL") or "z-ai/glm-4.5-air:free"
		self.strict_ai_selection = strict_ai_selection if strict_ai_selection is not None else os.getenv("STRICT_AI_SELECTION", "true").lower() == "true"
		self.client = None
		if api_key:
			try:
				openai_mod = importlib.import_module("openai")
				# client construction depends on library; support passing base_url for OpenRouter
				try:
					# Newer OpenAI SDK accepts base_url and api_key in constructor
					self.client = openai_mod.OpenAI(api_key=api_key, base_url=base_url)
				except Exception:
					# Fallback: set module-level api_key and optionally base_url
					try:
						openai_mod.api_key = api_key
					except Exception:
						pass
					try:
						openai_mod.base_url = base_url
					except Exception:
						pass
					self.client = openai_mod
			except ModuleNotFoundError:
				if self.strict_ai_selection:
					print("ERROR: openai package not installed and strict_ai_selection=True; AI tool selection will fail")
				else:
					print("WARNING: openai package not installed; LLMBrain will use deterministic fallback")
		else:
			if self.strict_ai_selection:
				print("ERROR: No OpenRouter/OpenAI API key set and strict_ai_selection=True; AI tool selection will fail")
			else:
				print("WARNING: No OpenRouter/OpenAI API key set; LLMBrain will use deterministic fallback")

	def decide_tool(self, user_intent: str, available_tools: dict[str, object], market_context: dict = None):
		"""
		AI-powered tool selector. Returns a dict like:
		{"tool_name": str, "arguments": {...}, "reason": str} or {"error": str}

		Requires LLM client when strict_ai_selection=True.
		"""
		# Build detailed tool descriptions with schema info
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

		# Include market context in prompt
		context_info = ""
		if market_context:
			record_count = market_context.get("record_count", 0)
			latest_price = market_context.get("latest_price")
			avg_price = market_context.get("avg_price")
			context_info = f"\nMarket Context:\n- Available competitor records: {record_count}\n"
			if latest_price: context_info += f"- Latest competitor price: ${latest_price}\n"
			if avg_price: context_info += f"- Average competitor price: ${avg_price}\n"

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

		# AI-only selection logic
		if not self.client:
			if self.strict_ai_selection:
				return {"error": "ai_selection_failed", "message": "No LLM client available and strict_ai_selection=True"}
			else:
				# Legacy fallback mode
				intent = (user_intent or "").lower()
				if "profit" in intent or "maximize" in intent:
					return {"tool_name": "profit_maximization", "arguments": {}, "reason": "fallback: keyword 'profit' detected"}
				return {"tool_name": "rule_based", "arguments": {}, "reason": "fallback: default conservative approach"}

		try:
			resp = self.client.chat.completions.create(
				model=self.model,
				messages=[{"role": "user", "content": prompt}],
				max_tokens=300,
				temperature=0.0,
			)
			raw = resp.choices[0].message.content or ""
			
			# Enhanced telemetry: log raw LLM decision (redacted for safety)
			try:
				from core.agents.agent_sdk.activity_log import activity_log as act_log
				redacted_raw = raw[:100] + "..." if len(raw) > 100 else raw
				act_log.log("llm_brain", "decide_tool.request", "info", 
					message=f"model={self.model} prompt_len={len(prompt)} response_len={len(raw)}", 
					details={"raw_response_preview": redacted_raw, "available_tools": list(available_tools.keys())})
			except Exception:
				pass  # Don't fail on logging errors
			
			# Parse JSON response
			start = raw.find("{")
			end = raw.rfind("}")
			if start == -1 or end == -1:
				return {"error": "ai_selection_failed", "message": "LLM response missing JSON format"}
			
			try:
				parsed = json.loads(raw[start : end + 1])
			except json.JSONDecodeError as e:
				return {"error": "ai_selection_failed", "message": f"Invalid JSON from LLM: {e}"}
			
			# Validate response structure
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
			
			# Enhanced telemetry: log successful AI decision
			try:
				from core.agents.agent_sdk.activity_log import activity_log as act_log
				act_log.log("llm_brain", "decide_tool.success", "completed", 
					message=f"selected={tool_name} reason='{reason}'", 
					details={"tool_name": tool_name, "arguments": arguments, "reason": reason, "market_context": market_context})
			except Exception:
				pass  # Don't fail on logging errors
			
			return {"tool_name": tool_name, "arguments": arguments, "reason": reason}
			
		except Exception as e:
			# Enhanced telemetry: log LLM request failures
			try:
				from core.agents.agent_sdk.activity_log import activity_log as act_log
				act_log.log("llm_brain", "decide_tool.failed", "failed", 
					message=f"LLM request failed: {str(e)}", 
					details={"error": str(e), "model": self.model})
			except Exception:
				pass  # Don't fail on logging errors
			return {"error": "ai_selection_failed", "message": f"LLM request failed: {str(e)}"}

	async def _request_fresh_data(self, user_request: str, product_name: str, wait_seconds: int, max_wait_attempts: int, activity_log=None):
		"""Request fresh market data via event bus and wait for completion."""
		try:
			from core.agents.agent_sdk.bus_factory import get_bus
			from core.agents.agent_sdk.protocol import Topic
			from core.payloads import MarketFetchRequestPayload
			
			# Extract URLs from user request if any
			urls = re.findall(r'https?://\S+', user_request or '')
			
			# Create fetch request
			request_id = str(uuid.uuid4())
			fetch_request: MarketFetchRequestPayload = {
				"request_id": request_id,
				"sku": product_name,
				"market": "DEFAULT",
				"sources": ["web_scraper"] if urls else [],
				"urls": urls if urls else None,
				"horizon_minutes": 60,  # 1 hour freshness target
				"depth": min(len(urls), 5) if urls else 1
			}
			
			bus = get_bus()
			await bus.publish(Topic.MARKET_FETCH_REQUEST.value, fetch_request)
			
			if activity_log:
				activity_log.log("pricing_optimizer", "market.fetch.request", "info", 
					message=f"request_id={request_id} sku={product_name}")
			
			# Wait for completion (simplified - in production could listen for DONE events)
			import asyncio
			for attempt in range(max_wait_attempts):
				await asyncio.sleep(wait_seconds)
				# In a real implementation, we'd check for completion events
				# For now, we'll just wait and let the caller re-check data freshness
			
		except Exception as e:
			print(f"[pricing_optimizer] Failed to request fresh data: {e}")
			if activity_log:
				activity_log.log("pricing_optimizer", "market.fetch.request", "failed", message=str(e))

	async def process_full_workflow(self, user_request: str, product_name: str, db_path: str = "data/market.db", notify_alert_fn=None, wait_seconds: int = 3, max_wait_attempts: int = 5, monitor_timeout: int = 0):
		"""
		Execute the full pricing workflow described in the system prompt.
		Returns strict JSON dict on success or error.

		Parameters:
		- user_request: the user intent/request text
		- product_name: product to price
		- db_path: sqlite DB file
		- notify_alert_fn: optional callable(msg:str) to notify Alert Agent
		- wait_seconds: seconds to wait between simulated Market Data Collector polls
		- max_wait_attempts: how many times to re-check DB after requesting update
		- monitor_timeout: if >0, poll for market_data changes for this many seconds and re-run once
		"""
		# helper: strict error output
		def err(msg: str):
			return {"status": "error", "message": msg}

		# Use DataRepo to access market data from app/data.db
		try:
			from core.agents.data_collector.repo import DataRepo
			repo = DataRepo("app/data.db")  # Use app/data.db instead of data/market.db
			await repo.init()
		except Exception as e:
			return err(f"DataRepo initialization failed: {e}")

		# helper: fetch records from market_ticks table
		async def fetch_records():
			try:
				# Get recent ticks for this SKU
				since_iso = (datetime.now() - timedelta(days=7)).isoformat()  # Last 7 days
				features = await repo.features_for(product_name, "DEFAULT", since_iso)
				
				# Convert to the old format for compatibility with existing algorithms
				records = []
				if features.get("count", 0) > 0:
					comp_price = features.get("features", {}).get("competitor_price")
					if comp_price is not None:
						# Ensure as_of uses timezone-aware ISO format
						records.append((comp_price, features.get("as_of", datetime.now(timezone.utc).isoformat())))
				return records
			except Exception as e:
				print(f"[pricing_optimizer] Error fetching records: {e}")
				return []

		# helper: parse timestamp
		def _parse_time(s):
			if not s:
				return None
			try:
				# Try ISO first
				return datetime.fromisoformat(s)
			except Exception:
				try:
					# fallback common format
					return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
				except Exception:
					return None

		# Optional: activity log (best-effort)
		try:
			from core.agents.agent_sdk.activity_log import activity_log as _act
		except Exception:
			_act = None  # type: ignore

		if _act:
			_act.log("pricing_optimizer", "workflow.start", "in_progress", message=f"request='{user_request}' sku='{product_name}'")
			# Surface scraper availability in the activity feed for transparency
			if "fetch_competitor_price" not in TOOLS:
				_act.log("web_scraper", "tool.unavailable", "info", message="fetch_competitor_price not available (dependency missing or import error)")


		# Step 1 & 2: Check data freshness and request update if needed
		records = await fetch_records()
		stale = False
		if not records:
			stale = True
		else:
			# determine latest update
				latest = None
				for r in records:
					ts = _parse_time(r[1])
					if ts and (latest is None or ts > latest):
						latest = ts
				# Compare using timezone-aware now if latest has tzinfo
				_now = datetime.now(timezone.utc) if (latest and latest.tzinfo) else datetime.now()
				if not latest or (_now - latest) > timedelta(hours=24):
					stale = True

		if stale:
			# Send market data fetch request via event bus
			await self._request_fresh_data(user_request, product_name, wait_seconds, max_wait_attempts, _act)
			# Re-fetch records after data collection
			records = await fetch_records()
			if not records:
				# re-evaluate freshness after request
				latest = None
				for r in records:
					ts = _parse_time(r[1])
					if ts and (latest is None or ts > latest):
						latest = ts
				if not latest or (datetime.now() - latest) > timedelta(hours=24):
					return err("market data not refreshed after request")

		# Step 3: Process data & choose tool/algorithm using agentic selection
		records = await fetch_records()
		if not records:
			# We still allow a scrape-first workflow if requested
			records = []

		# Build market context for AI decision
		market_context = {
			"record_count": len(records),
			"latest_price": records[0][0] if records else None,
			"avg_price": sum(r[0] for r in records) / len(records) if records else None
		}

		# AI-only algorithm selection (limit to pricing algorithms only)
		algo_tools = {k: v for k, v in TOOLS.items() if k in ("rule_based", "ml_model", "profit_maximization")}
		selection = self.decide_tool(user_request, dict(algo_tools), market_context)
		
		# Handle AI selection errors
		if "error" in selection:
			if _act:
				_act.log("llm_brain", "decide_tool", "failed", 
						message=f"AI selection failed: {selection.get('message', 'unknown error')}", 
						details={"error": selection, "market_context": market_context})
			return err(f"AI tool selection failed: {selection.get('message', 'unknown error')}")
		
		algo = selection.get("tool_name")
		reason = selection.get("reason", "No reason provided")
		
		if _act:
			_act.log("llm_brain", "decide_tool", "completed", 
					message=f"algo={algo} reason={reason}", 
					details={"market_context": market_context, "selection": selection})

		# Ensure we have some data before pricing (unless AI explicitly chose a tool that can work without data)
		if not records and algo != "profit_maximization":  # profit_maximization might use fallback logic
			return err("no market data available for selected algorithm")

		# Step 4: Calculate price using selected algorithm
		try:
			price = TOOLS[algo](records)
		except Exception as e:
			return err(f"calculation failed: {e}")
		if price is None:
			return err("calculation returned no price")
		if _act:
			_act.log("pricing_optimizer", "compute_price", "completed", message=f"algo={algo} price={price}")

		# Publish a typed price.proposal payload only (no direct writes)
		try:
			import uuid as _uuid
			import sqlite3 as _sqlite3
			import asyncio as _asyncio
			import threading as _threading
			from core.agents.agent_sdk.bus_factory import get_bus as _get_bus
			from core.agents.agent_sdk.protocol import Topic as _Topic
			from core.payloads import PriceProposalPayload as _PPayload

			# Read current price from product catalog and previous price from price proposals
			# Both are now in app/data.db via DataRepo
			current_price_val = None
			previous_price_val = None
			
			try:
				import sqlite3 as _sqlite3
				from pathlib import Path as _Path
				
				_root = _Path(__file__).resolve().parents[2]
				_app_db = _root / "app" / "data.db"
				
				conn = _sqlite3.connect(_app_db.as_posix(), check_same_thread=False)
				cursor = conn.cursor()
				
				# Get current price from product catalog
				cursor.execute(
					"SELECT current_price FROM product_catalog WHERE sku=? LIMIT 1",
					(product_name,),
				)
				row = cursor.fetchone()
				if row and row[0] is not None:
					current_price_val = float(row[0])
				
				# Get most recent proposed price from price_proposals
				cursor.execute(
					"SELECT proposed_price FROM price_proposals WHERE sku=? ORDER BY ts DESC LIMIT 1",
					(product_name,),
				)
				row = cursor.fetchone()
				if row and row[0] is not None:
					previous_price_val = float(row[0])
				
				conn.close()
			except Exception as e:
				print(f"[pricing_optimizer] Error reading prices: {e}")

			proposal_id = str(_uuid.uuid4())
			pp: _PPayload = {
				"proposal_id": proposal_id,
				"product_id": product_name,
				"previous_price": float(previous_price_val if previous_price_val is not None else (current_price_val if current_price_val is not None else 0.0)),
				"proposed_price": float(price),
			}

			async def _publish_async():
				try:
					_bus_local = _get_bus()
					await _bus_local.publish(_Topic.PRICE_PROPOSAL.value, pp)
				except Exception as _e:
					try:
						print(f"[pricing_optimizer] publish price.proposal failed: {_e}")
					except Exception:
						pass

			await _publish_async()

			if _act:
				_act.log("pricing_optimizer", "governance.enabled", "info", message="Published price.proposal; no direct DB writes")
			return {"product": product_name, "proposed_price": float(price), "algorithm": str(algo), "proposal_id": proposal_id, "status": "proposed"}
		except Exception as _ep:
			try:
				print(f"[pricing_optimizer] proposal publish error: {_ep}")
			except Exception:
				pass
			return err("failed to publish proposal")
		# No direct DB writes, no decision logs, no price.update here.
		# Return a proposal summary only; GEA will handle application and logging.
		if _act:
			_act.log("pricing_optimizer", "workflow.end", "completed", message=f"sku='{product_name}' status=proposed")
		return {"product": product_name, "proposed_price": float(price), "algorithm": algo, "status": "proposed"}



# Pricing Optimizer Agent = LLMBrain
# The LLMBrain now IS the Pricing Optimizer Agent. Keep the name for compatibility.
PricingOptimizerAgent = LLMBrain


# --- Example run loop using the unified agent ---
if __name__ == "__main__":
	import asyncio
	import time
	
	async def main():
		agent = PricingOptimizerAgent()
		# Use process_full_workflow to run the full workflow end-to-end
		while True:
			res = await agent.process_full_workflow("maximize profit", "iphone15")
			print(res)
			await asyncio.sleep(30)  # Use asyncio.sleep instead of time.sleep
	
	asyncio.run(main())


