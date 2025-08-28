# core/agents/pricing_optimizer.py

import os
import sqlite3
import time
import importlib
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


# Toolbox mapping (dictionary of available tools)
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
				print("⚠️ openai package not installed; LLMBrain will use deterministic fallback")
		else:
			print("⚠️ No OpenRouter/OpenAI API key set; LLMBrain will use deterministic fallback")

	def decide_tool(self, user_intent, n_records):
		"""
		Ask the LLM which tool to use.
		"""
		prompt = f"""
		You are the brain of a Pricing Optimizer Agent.
		User intent: {user_intent}
		Number of competitor records: {n_records}

		Available tools:
		- rule_based: use average competitor price - 2%
		- ml_model: use machine learning for large datasets
		- profit_maximization: maximize profit with markup

		Decide the best tool. Answer with only one word:
		rule_based, ml_model, or profit_maximization.
		"""
		try:
			# If no client, use deterministic rule: prefer ml_model for large n, profit if intent contains profit
			if not self.client:
				intent = (user_intent or "").lower()
				if "profit" in intent or "maximize" in intent:
					return "profit_maximization"
				if n_records >= 50:
					return "ml_model"
				return "rule_based"

			resp = self.client.chat.completions.create(
				model=self.model,
				messages=[{"role": "user", "content": prompt}],
				max_tokens=5,
				temperature=0.0,
			)
			choice = resp.choices[0].message.content.strip().lower()
			return choice if choice in TOOLS else "rule_based"
		except Exception as e:
			print("❌ LLM error:", e)
			return "rule_based"

	def process_full_workflow(self, user_request: str, product_name: str, db_path: str = "market.db", notify_alert_fn=None, wait_seconds: int = 3, max_wait_attempts: int = 5, monitor_timeout: int = 0):
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

		# open DB connection locally
		try:
			conn = sqlite3.connect(db_path, check_same_thread=False)
			cursor = conn.cursor()
		except Exception as e:
			return err(f"DB connection failed: {e}")

		# helper: fetch records
		def fetch_records():
			try:
				cursor.execute("SELECT price, update_time FROM market_data WHERE product_name=?", (product_name,))
				return cursor.fetchall()
			except Exception as e:
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

		# Step 1 & 2: Check data freshness and request update if needed
		records = fetch_records()
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
			# send market data collect request (simulated)
			msg = f"UPDATE market_data for {product_name}"
			print(msg)
			# Poll DB for confirmation (simulated) up to max_wait_attempts
			attempt = 0
			while attempt < max_wait_attempts:
				time.sleep(wait_seconds)
				records = fetch_records()
				if records:
					# re-evaluate freshness
					latest = None
					for r in records:
						ts = _parse_time(r[1])
						if ts and (latest is None or ts > latest):
							latest = ts
					if latest and (datetime.now() - latest) <= timedelta(hours=24):
						break
				attempt += 1
			if attempt >= max_wait_attempts and (not records or latest is None or (datetime.now() - latest) > timedelta(hours=24)):
				return err("market data not refreshed after request")

		# Step 3: Process data & choose algorithm per rules
		records = fetch_records()
		if not records:
			return err("no market data available")

		n = len(records)
		intent = (user_request or "").lower()
		if "max" in intent and "profit" in intent or "maximize" in intent:
			algo = "profit_maximization"
		elif n < 100:
			algo = "rule_based"
		else:
			algo = "ml_model"

		# Step 4: Calculate price
		try:
			price = TOOLS[algo](records)
		except Exception as e:
			return err(f"calculation failed: {e}")
		if price is None:
			return err("calculation returned no price")

		# Step 5: Update database (insert or update)
		try:
			cursor.execute("SELECT product_name FROM pricing_list WHERE product_name=?", (product_name,))
			exists = cursor.fetchone() is not None
			if exists:
				cursor.execute(
					"UPDATE pricing_list SET optimized_price=?, last_update=CURRENT_TIMESTAMP, reason=? WHERE product_name=?",
					(price, f"optimized using {algo}", product_name),
				)
			else:
				cursor.execute(
					"INSERT INTO pricing_list (product_name, optimized_price, last_update, reason) VALUES (?, ?, CURRENT_TIMESTAMP, ?)",
					(product_name, price, f"optimized using {algo}"),
				)
			conn.commit()
		except Exception as e:
			return err(f"db update failed: {e}")

		# Step 6: Notify Alert Agent
		notify_msg = f"PRICE_UPDATED {product_name} {price}"
		if notify_alert_fn:
			try:
				notify_alert_fn(notify_msg)
			except Exception:
				print("Failed to call notify_alert_fn")
		else:
			print(notify_msg)

		result = {"product": product_name, "price": price, "algorithm": algo, "status": "success"}

		# Step 7: Monitor changes - optional single re-run if market_data updates during monitor_timeout
		if monitor_timeout and monitor_timeout > 0:
			start = time.time()
			# capture current latest update_time
			try:
				cursor.execute("SELECT MAX(update_time) FROM market_data WHERE product_name=?", (product_name,))
				baseline = cursor.fetchone()[0]
			except Exception:
				baseline = None
			while time.time() - start < monitor_timeout:
				time.sleep(1)
				try:
					cursor.execute("SELECT MAX(update_time) FROM market_data WHERE product_name=?", (product_name,))
					latest2 = cursor.fetchone()[0]
				except Exception:
					latest2 = None
				if latest2 and latest2 != baseline:
					# re-run once
					return self.process_full_workflow(user_request, product_name, db_path=db_path, notify_alert_fn=notify_alert_fn, wait_seconds=wait_seconds, max_wait_attempts=max_wait_attempts, monitor_timeout=0)

		return result



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


