"""
Shared health tools for MCP servers.
"""
import time
from datetime import datetime, timezone
from typing import Dict, Any
import asyncio

# Server start time for uptime calculation
_server_start_time = time.time()

def get_server_uptime() -> float:
    """Get server uptime in seconds."""
    return time.time() - _server_start_time

async def ping() -> Dict[str, Any]:
    """Basic connectivity test."""
    return {
        "ok": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

async def version() -> Dict[str, Any]:
    """Server version information.""" 
    return {
        "ok": True,
        "version": "1.0.0",
        "build": "dev",
        "commit": "unknown"
    }

async def health(service_name: str, check_dependencies: bool = True) -> Dict[str, Any]:
    """Detailed health status with dependency checks."""
    status = "healthy"
    dependencies = {}
    
    if check_dependencies:
        # Add service-specific dependency checks here
        if service_name == "data-collector":
            try:
                # Test database connection
                from .repo import DataRepo
                repo = DataRepo()
                await repo.init()
                dependencies["database"] = "ok"
            except Exception:
                dependencies["database"] = "error" 
                status = "degraded"
                
        elif service_name == "alerts":
            try:
                from .repo import Repo
                repo = Repo()
                await repo.init()
                dependencies["database"] = "ok"
            except Exception:
                dependencies["database"] = "error"
                status = "degraded"
                
        elif service_name == "price-optimizer":
            # No external dependencies for now
            dependencies["internal"] = "ok"
    
    return {
        "ok": status in ["healthy", "degraded"],
        "status": status,
        "version": "1.0.0",
        "uptime_seconds": get_server_uptime(),
        "dependencies": dependencies
    }