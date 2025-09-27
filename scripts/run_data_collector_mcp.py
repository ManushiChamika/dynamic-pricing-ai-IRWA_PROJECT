#!/usr/bin/env python3
"""
Launch data collector MCP server
Usage: python -m scripts.run_data_collector_mcp [--log-level INFO]
"""
import argparse
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

async def main():
    parser = argparse.ArgumentParser(description="Data Collector MCP Server")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    logger.info("Starting Data Collector MCP server...")
    
    try:
        from core.agents.data_collector.mcp_server import main as server_main
        await server_main()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())