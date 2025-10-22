from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .tools import Tools, get_llm_tools, execute_tool_call
from .repo import DataRepo

logger = logging.getLogger("data_collector_agent")

SYSTEM_PROMPT = """You are a proactive Market Intelligence Agent for a dynamic pricing system. Your primary goal is to ensure all products have fresh market data by monitoring data staleness and autonomously triggering collection jobs.

Your workflow:
1. ALWAYS start by calling get_stale_products() to identify products with outdated market data
2. Call get_active_jobs() to check if collection is already in progress
3. For each stale product (prioritizing the stalest first):
   - Avoid starting jobs that are already running
   - Call start_collection_job() to gather fresh competitor pricing
   - Limit concurrent jobs to prevent overload (max 3-5 active jobs)
4. Call get_recent_jobs() to monitor success rates and identify issues

IMPORTANT: You must work autonomously and proactively. Your goal is to maintain data freshness across all products without manual intervention."""


class DataCollectorAgent:
def __init__(
        self,
        repo: DataRepo,
        check_interval_seconds: int = 180,
    ):
        self.repo = repo
        self.check_interval_seconds = check_interval_seconds
        self.tools = Tools(repo)
        self.llm = None
        self.logger = logger
        self.running = False
        
        try:
            from core.agents.llm_client import get_llm_client
            self.llm = get_llm_client()
            if self.llm and self.llm.is_available():
                self.logger.info("LLM brain initialized successfully - autonomous mode enabled")
            else:
                self.logger.warning("LLM unavailable - agent will use simple heuristic mode")
        except Exception as e:
            self.logger.warning(f"Failed to initialize LLM: {e}")

    async def start(self):
        self.running = True
        self.logger.info(
            f"DataCollectorAgent started - LLM={'enabled' if self.llm and self.llm.is_available() else 'disabled'}, "
            f"check_interval={self.check_interval_seconds}s"
        )
        
        try:
            from core.agents.agent_sdk.bus_factory import get_bus
            from core.agents.agent_sdk.protocol import Topic
            
            bus = get_bus()
            await bus.publish(Topic.ALERT.value, {
                "ts": datetime.now().isoformat(),
                "sku": "SYS",
                "severity": "info",
                "title": f"DataCollectorAgent ready (LLM={'enabled' if self.llm and self.llm.is_available() else 'disabled'})"
            })
        except Exception:
            pass
        
        asyncio.create_task(self._autonomous_loop())

    async def stop(self):
        self.running = False
        self.logger.info("DataCollectorAgent stopped")

    async def _autonomous_loop(self):
        while self.running:
            try:
                self.logger.info("Running autonomous data freshness check...")
                
                if self.llm and self.llm.is_available():
                    await self._handle_autonomous_check()
                else:
                    await self._handle_heuristic_check()
                    
            except Exception as e:
                self.logger.error(f"Autonomous loop error: {e}", exc_info=True)
            
            await asyncio.sleep(self.check_interval_seconds)

    async def _handle_autonomous_check(self):
        try:
            prompt = """It's time for a proactive data freshness check. Please:

1. Check which products have stale market data (older than 60 minutes)
2. Review currently active collection jobs to avoid duplicates
3. Start collection jobs for the stalest products (prioritize those with no data or oldest data)
4. Limit to 3-5 concurrent jobs maximum to avoid overload

Complete this workflow autonomously using your tools."""

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            tools_schema = get_llm_tools()
            
            async def get_all_products_async():
                return await execute_tool_call("get_all_products", {}, self.tools)
            
            async def check_data_freshness_async(sku: str, market: str = "DEFAULT"):
                return await execute_tool_call("check_data_freshness", {"sku": sku, "market": market}, self.tools)
            
            async def get_stale_products_async(threshold_minutes: int = 60):
                return await execute_tool_call("get_stale_products", {"threshold_minutes": threshold_minutes}, self.tools)
            
            async def start_collection_job_async(sku: str, market: str = "DEFAULT", 
                                                connector: str = "mock", depth: int = 5):
                return await execute_tool_call("start_collection_job", {
                    "sku": sku, "market": market, "connector": connector, "depth": depth
                }, self.tools)
            
            async def get_active_jobs_async():
                return await execute_tool_call("get_active_jobs", {}, self.tools)
            
            async def get_recent_jobs_async(limit: int = 10):
                return await execute_tool_call("get_recent_jobs", {"limit": limit}, self.tools)
            
            functions_map = {
                "get_all_products": get_all_products_async,
                "check_data_freshness": check_data_freshness_async,
                "get_stale_products": get_stale_products_async,
                "start_collection_job": start_collection_job_async,
                "get_active_jobs": get_active_jobs_async,
                "get_recent_jobs": get_recent_jobs_async,
            }
            
            try:
                result = self.llm.chat_with_tools(
                    messages=messages,
                    tools=tools_schema,
                    functions_map=functions_map,
                    max_rounds=10,
                    max_tokens=2000
                )
                
                self.logger.info(f"LLM autonomous check completed: {result}")
                
            except Exception as e:
                self.logger.error(f"LLM autonomous check failed: {e}")
                await self._handle_heuristic_check()
                
        except Exception as e:
            self.logger.error(f"Autonomous check failed: {e}")

    async def _handle_heuristic_check(self):
        self.logger.info("Using heuristic data freshness check")
        
        try:
            stale_result = await self.tools.get_stale_products(threshold_minutes=60)
            
            if not stale_result.get("ok"):
                self.logger.error(f"Failed to get stale products: {stale_result.get('error')}")
                return
            
            stale_products = stale_result.get("stale_products", [])
            
            if not stale_products:
                self.logger.info("No stale products found - all data is fresh")
                return
            
            self.logger.info(f"Found {len(stale_products)} stale products")
            
            active_jobs_result = await self.tools.get_active_jobs()
            active_jobs = active_jobs_result.get("active_jobs", []) if active_jobs_result.get("ok") else []
            active_skus = {job["sku"] for job in active_jobs}
            
            self.logger.info(f"Currently active jobs: {len(active_jobs)}")
            
            max_concurrent = 5
            jobs_started = 0
            
            for product in stale_products[:10]:
                if jobs_started >= max_concurrent:
                    self.logger.info(f"Reached max concurrent jobs limit ({max_concurrent})")
                    break
                
                sku = product["sku"]
                
                if sku in active_skus:
                    self.logger.info(f"Skipping {sku} - job already active")
                    continue
                
                has_url = bool(product.get("source_url"))
                connector = "web_scraper" if has_url else "mock"
                
                self.logger.info(f"Starting collection job for {sku} using {connector} (stale for {product.get('minutes_stale', 'unknown')} minutes)")
                
                result = await self.tools.start_collection_job(
                    sku=sku,
                    market="DEFAULT",
                    connector=connector,
                    depth=5
                )
                
                if result.get("ok"):
                    jobs_started += 1
                    self.logger.info(f"Started job {result.get('request_id')} for {sku}")
                else:
                    self.logger.error(f"Failed to start job for {sku}: {result.get('error')}")
            
            self.logger.info(f"Heuristic check completed - started {jobs_started} jobs")
            
        except Exception as e:
            self.logger.error(f"Heuristic check failed: {e}", exc_info=True)
