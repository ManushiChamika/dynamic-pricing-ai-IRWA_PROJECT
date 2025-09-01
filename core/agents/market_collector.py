import asyncio
from core.agents.data_collector.repo import DataRepo
from core.agents.data_collector.collector import DataCollector
from core.agents.data_collector.connectors.mock import mock_ticks

async def run_market_collector(
	sku: str = "SKU-123",
	market: str = "DEFAULT",
	depth: int = 5,
	delay_s: float = 0.25,
):
	"""Feed mock market ticks through DataCollector so MARKET_TICK events are produced.

	This function initializes the DataRepo and DataCollector, then ingests a short
	stream of mock ticks. It prints start and finish messages for demo visibility.
	"""
	print(f"[market_collector] Starting feeder: sku={sku} market={market} depth={depth} delay={delay_s}s")
	repo = DataRepo()
	await repo.init()
	dc = DataCollector(repo)
	await dc.ingest_stream(
		mock_ticks(sku=sku, market=market, n=max(1, depth)),
		delay_s=delay_s,
	)
	print(f"[market_collector] Finished feeder for {sku}.")
