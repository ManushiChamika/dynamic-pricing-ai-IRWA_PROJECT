#!/usr/bin/env python3
"""
CLI entrypoint for MCP servers with standardized configuration.
"""
import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

def setup_logging(level: str) -> None:
    """Setup structured logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

async def run_data_collector(args) -> None:
    """Run data collector MCP server."""
    from core.agents.data_collector.mcp_server import main
    await main()

async def run_alerts(args) -> None:
    """Run alerts MCP server."""
    from core.agents.alert_service.mcp_server import main
    await main()

async def run_price_optimizer(args) -> None:
    """Run price optimizer MCP server."""  
    from core.agents.price_optimizer.mcp_server import main
    await main()

def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(description="MCP Server Launcher")
    parser.add_argument(
        "service",
        choices=["data-collector", "alerts", "price-optimizer"],
        help="MCP service to run"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "websocket"],
        default="stdio",
        help="Transport protocol (default: stdio)"
    )
    parser.add_argument(
        "--host",
        default="localhost", 
        help="WebSocket host (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="WebSocket port (default: 8000)" 
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)"
    )
    parser.add_argument(
        "--env-file",
        help="Path to environment file"
    )
    return parser

def load_env_file(path: str) -> None:
    """Load environment variables from file."""
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

async def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Load environment file if specified
    if args.env_file:
        load_env_file(args.env_file)
    
    # Set transport environment variables
    if args.transport == "websocket":
        os.environ["MCP_TRANSPORT"] = "websocket"
        os.environ["MCP_HOST"] = args.host
        os.environ["MCP_PORT"] = str(args.port)
        logger.info(f"Starting {args.service} server on WebSocket {args.host}:{args.port}")
    else:
        os.environ["MCP_TRANSPORT"] = "stdio"
        logger.info(f"Starting {args.service} server on stdio transport")
    
    # Route to appropriate server
    try:
        if args.service == "data-collector":
            await run_data_collector(args)
        elif args.service == "alerts":
            await run_alerts(args)
        elif args.service == "price-optimizer":
            await run_price_optimizer(args)
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())