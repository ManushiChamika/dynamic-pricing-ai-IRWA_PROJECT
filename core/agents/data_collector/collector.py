from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from core.agents.agent_sdk.bus_factory import get_bus as _get_bus
from core.agents.agent_sdk.protocol import Topic
from core.agents.agent_sdk.events_models import MarketTick
from core.payloads import MarketFetchRequestPayload, MarketFetchAckPayload, MarketFetchDonePayload
from .repo import DataRepo

# Optional legacy agent SDK bus for backward compatibility.
# If available, we will dual-publish the raw dict payload to the legacy bus/topic.
try:  # Safe import; legacy module may not exist in all environments
    from core.agents.agent_sdk import get_bus as get_legacy_bus, Topic as LegacyTopic
except Exception:
    get_legacy_bus = None  # type: ignore[assignment]
    LegacyTopic = None  # type: ignore[assignment]


class DataCollector:
    def __init__(self, repo: DataRepo):
        self.repo = repo
        self._instance_id = uuid.uuid4().hex[:8]  # Add instance ID for debugging
        self._processed_requests = set()  # Track processed request IDs to prevent duplicates
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        """Set up event bus subscriptions for market fetch requests."""
        bus = _get_bus()
        print(f"[DataCollector-{self._instance_id}] Setting up subscription to MARKET_FETCH_REQUEST")
        bus.subscribe(Topic.MARKET_FETCH_REQUEST.value, self._handle_market_fetch_request)

    async def ingest_tick(self, d: Dict[str, Any]) -> None:
        # Normalize required fields
        payload = {
            "sku": d["sku"],
            "market": d.get("market", "DEFAULT"),
            "our_price": float(d["our_price"]),
            "competitor_price": d.get("competitor_price"),
            "demand_index": d.get("demand_index"),
            "ts": d.get("ts")
            or datetime.now(timezone.utc).isoformat(),
            "source": d.get("source", "manual"),
        }
        await self.repo.insert_tick(payload)
        # Publish MARKET_TICK as a typed dataclass on the global bus so downstream
        # consumers (e.g., AlertNotifier) receive the expected structure.
        competitor_price_value = payload.get("competitor_price")
        comp_price: Optional[float] = (
            float(competitor_price_value) if competitor_price_value is not None else None
        )
        demand_index_value = float(payload.get("demand_index") or 0.0)

        tick = MarketTick(
            sku=payload["sku"],
            our_price=payload["our_price"],
            competitor_price=comp_price,
            demand_index=demand_index_value,
        )
        await _get_bus().publish(Topic.MARKET_TICK.value, tick)

        # Best-effort legacy publish for backward compatibility.
        # If the legacy bus exists, also publish the original dict payload; ignore errors.
        if get_legacy_bus is not None and LegacyTopic is not None:
            try:
                legacy_bus = get_legacy_bus()
                res = legacy_bus.publish(LegacyTopic.MARKET_TICK.value, payload)
                # Handle both coroutine and sync publish implementations.
                import asyncio as _asyncio

                if _asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                # Non-fatal: continue if legacy publish fails.
                try:
                    print(f"[DataCollector] Legacy bus publish failed: {e}")
                except Exception:
                    pass

    async def ingest_stream(
        self, it: Iterable[Dict[str, Any]], delay_s: float = 1.0
    ) -> None:
        import asyncio

        for d in it:
            await self.ingest_tick(d)
            await asyncio.sleep(delay_s)

    async def _handle_market_fetch_request(self, payload: MarketFetchRequestPayload) -> None:
        """Handle market fetch requests by running appropriate connectors."""
        request_id = payload["request_id"]
        sku = payload["sku"]
        market = payload["market"]
        sources = payload["sources"]
        urls = payload.get("urls", [])
        depth = payload["depth"]
        
        print(f"[DataCollector-{self._instance_id}] Handling market fetch request: {request_id}")
        
        # Check for duplicate request processing
        if request_id in self._processed_requests:
            print(f"[DataCollector-{self._instance_id}] DUPLICATE REQUEST DETECTED - Ignoring request_id: {request_id}")
            return
        
        # Mark request as being processed
        self._processed_requests.add(request_id)
        print(f"[DataCollector-{self._instance_id}] Added request_id {request_id} to processed set. Total processed: {len(self._processed_requests)}")
        
        bus = _get_bus()
        
        try:
            # Create a job for tracking
            job_id = await self.repo.create_job(sku, market, ",".join(sources), depth)
            
            # Send ACK
            ack_payload: MarketFetchAckPayload = {
                "request_id": request_id,
                "job_id": job_id,
                "status": "QUEUED",
                "error": None
            }
            await bus.publish(Topic.MARKET_FETCH_ACK.value, ack_payload)
            
            # Mark job as running
            await self.repo.mark_job_running(job_id)
            
            # Update ACK to running
            ack_payload["status"] = "RUNNING"
            await bus.publish(Topic.MARKET_FETCH_ACK.value, ack_payload)
            
            tick_count = 0
            
            # Process each source
            for source in sources:
                if source == "web_scraper" and urls:
                    # Use web scraper connector
                    try:
                        from .connectors.web_scraper import fetch_competitor_price
                        
                        for url in urls:
                            try:
                                result = fetch_competitor_price(url)
                                if result.get("status") == "success" and "price" in result:
                                    # Create tick data
                                    tick_data = {
                                        "sku": sku,
                                        "market": market,
                                        "our_price": 0.0,  # Will be updated from product catalog
                                        "competitor_price": float(result["price"]),
                                        "demand_index": 1.0,  # Default
                                        "ts": datetime.now(timezone.utc).isoformat(),
                                        "source": f"web_scraper:{url}"
                                    }
                                    
                                    # Insert tick
                                    await self.ingest_tick(tick_data)
                                    tick_count += 1
                                    
                            except Exception as e:
                                print(f"[DataCollector] Failed to scrape {url}: {e}")
                                
                    except ImportError:
                        print("[DataCollector] web_scraper connector not available")
            
            # Mark job as done
            await self.repo.mark_job_done(job_id)
            
            # Send completion notification
            done_payload: MarketFetchDonePayload = {
                "request_id": request_id,
                "job_id": job_id,
                "status": "DONE",
                "tick_count": tick_count
            }
            await bus.publish(Topic.MARKET_FETCH_DONE.value, done_payload)
            
        except Exception as e:
            # Mark job as failed if it was created
            try:
                if 'job_id' in locals():
                    await self.repo.mark_job_failed(job_id, str(e))
            except:
                pass
                
            # Send failure ACK
            fail_payload: MarketFetchAckPayload = {
                "request_id": request_id,
                "job_id": locals().get('job_id', ''),
                "status": "FAILED",
                "error": str(e)
            }
            await bus.publish(Topic.MARKET_FETCH_ACK.value, fail_payload)


