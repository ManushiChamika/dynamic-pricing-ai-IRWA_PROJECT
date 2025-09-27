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
from datetime import datetime, timedelta
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
	Simple rule-based algorithm:
	- Takes competitor prices
	- Returns average competitor price minus 2%
	"""
	prices = [r[0] for r in records]
	if not prices:
		return None
	avg = sum(prices) / len(prices)
	return round(avg * 0.98, 2)


def ml_model(records):
	"""
	Placeholder ML model:
	- Currently just returns average competitor price
	- Later can be replaced with regression/ML
	"""
	prices = [r[0] for r in records]
	if not prices:
		return None
	return round(sum(prices) / len(prices), 2)


def profit_maximization(records):
	"""
	Profit-maximization strategy:
	- Takes competitor prices
	- Returns average competitor price with +10% markup
	"""
	prices = [r[0] for r in records]
	if not prices:
		return None
	avg = sum(prices) / len(prices)
	return round(avg * 1.10, 2)


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

	def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
		# Try to import OpenAI dynamically. If not available, fall back to None
		# Prefer explicitly passed api_key, else try OPENROUTER_API_KEY then OPENAI_API_KEY
		api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
		base_url = base_url or os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"
		self.model = model or os.getenv("OPENROUTER_MODEL") or os.getenv("OPENAI_MODEL") or "z-ai/glm-4.5-air:free"
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
				print("WARNING: openai package not installed; LLMBrain will use deterministic fallback")
		else:
			print("WARNING: No OpenRouter/OpenAI API key set; LLMBrain will use deterministic fallback")

	def decide_tool(self, user_intent: str, available_tools: dict[str, object]):
		"""
		General-purpose tool selector. Returns a dict like:
		{"tool_name": str, "arguments": { ... }}

		If no LLM available, uses simple heuristics:
		- If URL present, choose fetch_competitor_price with that url
		- Else if intent mentions profit, choose profit_maximization
		- Else if few records (heuristic not available here), default rule_based
		"""
		# Build concise descriptions for the prompt
		descriptions = []
		for name in available_tools.keys():
			if name == "rule_based":
				descriptions.append({"name": name, "description": "Average competitor price minus 2%."})
			elif name == "ml_model":
				descriptions.append({"name": name, "description": "Machine learning model for pricing."})
			elif name == "profit_maximization":
				descriptions.append({"name": name, "description": "+10% markup over average competitor price."})
			else:
				descriptions.append({"name": name, "description": "Tool"})

		prompt = (
			"You are an AI agent brain. Based on the user's request, select the best tool to use from the "
			"following list and determine its arguments.\n\n" \
			f"User Request: \"{user_intent}\"\n\n" \
			f"Available Tools:\n{descriptions}\n\n" \
			"Respond with only a JSON object specifying the tool name and its arguments. "
			"Example: {\"tool_name\": \"fetch_competitor_price\", \"arguments\": {\"url\": \"http://example.com\"}}"
		)

		def _extract_first_url(text: str) -> str | None:
			if not text:
				return None
			m = re.search(r"https?://\S+", text)
			return m.group(0) if m else None

		def _default_selection():
			intent = (user_intent or "").lower()
			if "profit" in intent or "maximize" in intent:
				return {"tool_name": "profit_maximization", "arguments": {}}
			# fallback
			return {"tool_name": "rule_based", "arguments": {}}

		try:
			if not self.client:
				return _default_selection()

			resp = self.client.chat.completions.create(
				model=self.model,
				messages=[{"role": "user", "content": prompt}],
				max_tokens=200,
				temperature=0.0,
			)
			raw = resp.choices[0].message.content or ""
			# extract JSON
			start = raw.find("{")
			end = raw.rfind("}")
			parsed = json.loads(raw[start : end + 1]) if start != -1 and end != -1 else {}
			name = parsed.get("tool_name") if isinstance(parsed, dict) else None
			args = parsed.get("arguments", {}) if isinstance(parsed, dict) else {}
			if name in available_tools:
				return {"tool_name": name, "arguments": args if isinstance(args, dict) else {}}
			return _default_selection()
		except Exception as e:
			print("ERROR: LLM error:", e)
			return _default_selection()

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
						records.append((comp_price, features.get("as_of", datetime.now().isoformat())))
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
			if not latest or (datetime.now() - latest) > timedelta(hours=24):
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

		# First decision: may be scraper or an algorithm
		selection = self.decide_tool(user_request, dict(TOOLS))
		tool_name = selection.get("tool_name") if isinstance(selection, dict) else None
		arguments = selection.get("arguments", {}) if isinstance(selection, dict) else {}
		if _act:
			_act.log("llm_brain", "decide_tool", "completed", message=f"tool={tool_name}", details={"args": arguments})

		# Data collection is now handled via event bus - no direct scraping here

		# Ensure we have some data before pricing
		if not records:
			return err("no market data available")

		# Second decision: choose pricing algorithm (limit tools to algorithms)
		algo_tools = {k: v for k, v in TOOLS.items() if k in ("rule_based", "ml_model", "profit_maximization")}
		selection2 = self.decide_tool(user_request, dict(algo_tools))
		algo = selection2.get("tool_name") if isinstance(selection2, dict) else None
		if algo not in algo_tools:
			# simple heuristic fallback
			n = len(records)
			intent = (user_request or "").lower()
			if ("max" in intent and "profit" in intent) or ("maximize" in intent):
				algo = "profit_maximization"
			elif n < 100:
				algo = "rule_based"
			else:
				algo = "ml_model"

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

			try:
				_loop = _asyncio.get_running_loop()
				_loop.create_task(_publish_async())
			except RuntimeError:
				_threading.Thread(target=lambda: _asyncio.run(_publish_async()), daemon=True).start()

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
	agent = PricingOptimizerAgent()
	# Use process_full_workflow to run the full workflow end-to-end
	while True:
		res = agent.process_full_workflow("maximize profit", "iphone15")
		print(res)
		time.sleep(30)


