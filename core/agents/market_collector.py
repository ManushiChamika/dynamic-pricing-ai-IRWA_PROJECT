# Minimal stub for run_market_collector
import asyncio

async def run_market_collector(sku: str = "SKU-123"):
	print(f"[market_collector] Collecting market data for {sku}...")
	await asyncio.sleep(2)
	print(f"[market_collector] Finished collecting market data for {sku}.")
