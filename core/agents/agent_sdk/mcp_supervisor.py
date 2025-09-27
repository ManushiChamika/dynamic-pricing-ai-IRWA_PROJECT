"""
MCP Server Supervisor Integration

Manages MCP server lifecycles, integrates with event bus, and provides
graceful startup/shutdown with backoff and retry logic.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from contextlib import asynccontextmanager

from .bus_factory import get_bus
from .mcp_client import shutdown_mcp_clients


@dataclass
class MCPServiceConfig:
    """Configuration for an MCP service."""
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    restart_policy: str = "on-failure"  # "always", "on-failure", "never"
    max_restarts: int = 3
    restart_delay: float = 1.0
    health_check_interval: float = 30.0
    startup_timeout: float = 10.0


class MCPServiceManager:
    """Manages individual MCP service lifecycle."""
    
    def __init__(self, config: MCPServiceConfig):
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.restart_count = 0
        self.last_restart = 0.0
        self.running = False
        self.health_task: Optional[asyncio.Task] = None
        
    async def start(self) -> bool:
        """Start the MCP service process."""
        if self.running:
            return True
            
        try:
            # Set up environment
            env = os.environ.copy()
            if self.config.env:
                env.update(self.config.env)
            
            # Start process
            self.process = await asyncio.create_subprocess_exec(
                self.config.command,
                *self.config.args,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for startup with timeout
            try:
                await asyncio.wait_for(self._wait_for_startup(), timeout=self.config.startup_timeout)
                self.running = True
                
                # Start health monitoring
                if self.config.health_check_interval > 0:
                    self.health_task = asyncio.create_task(self._health_monitor())
                
                # Publish service started event
                bus = get_bus()
                await bus.publish("mcp.service.started", {
                    "service": self.config.name,
                    "pid": self.process.pid,
                    "timestamp": time.time()
                })
                
                return True
                
            except asyncio.TimeoutError:
                await self.stop()
                return False
                
        except Exception as e:
            logging.error(f"Failed to start MCP service {self.config.name}: {e}")
            return False
    
    async def stop(self) -> None:
        """Stop the MCP service process."""
        self.running = False
        
        # Cancel health monitoring
        if self.health_task:
            self.health_task.cancel()
            try:
                await self.health_task
            except asyncio.CancelledError:
                pass
        
        # Terminate process
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
            
            # Publish service stopped event
            bus = get_bus()
            await bus.publish("mcp.service.stopped", {
                "service": self.config.name,
                "pid": self.process.pid,
                "timestamp": time.time()
            })
            
            self.process = None
    
    async def restart(self) -> bool:
        """Restart the MCP service with backoff logic."""
        if self.restart_count >= self.config.max_restarts:
            return False
        
        # Apply exponential backoff
        now = time.time()
        if self.last_restart > 0:
            delay = self.config.restart_delay * (2 ** self.restart_count)
            elapsed = now - self.last_restart
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
        
        await self.stop()
        self.restart_count += 1
        self.last_restart = time.time()
        
        # Publish restart event
        bus = get_bus()
        await bus.publish("mcp.service.restart", {
            "service": self.config.name,
            "attempt": self.restart_count,
            "timestamp": time.time()
        })
        
        return await self.start()
    
    async def _wait_for_startup(self) -> None:
        """Wait for service to be ready (basic implementation)."""
        # For now, just wait a short time - in production this would
        # attempt to connect and verify the service is responding
        await asyncio.sleep(1.0)
        
        if self.process and self.process.returncode is not None:
            raise RuntimeError(f"Service {self.config.name} exited during startup")
    
    async def _health_monitor(self) -> None:
        """Monitor service health and restart if needed."""
        while self.running:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                if not self.running:
                    break
                
                # Check if process is still alive
                if self.process and self.process.returncode is not None:
                    if self.config.restart_policy == "always" or (
                        self.config.restart_policy == "on-failure" and self.process.returncode != 0
                    ):
                        if not await self.restart():
                            break
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Health check failed for {self.config.name}: {e}")


class MCPSupervisor:
    """Supervisor for managing multiple MCP services."""
    
    def __init__(self):
        self.services: Dict[str, MCPServiceManager] = {}
        self.shutdown_event = asyncio.Event()
        self.bus = get_bus()
        
    def add_service(self, config: MCPServiceConfig) -> None:
        """Add an MCP service to be managed."""
        self.services[config.name] = MCPServiceManager(config)
    
    async def start_all(self) -> Dict[str, bool]:
        """Start all managed services."""
        results = {}
        
        # Start services in parallel
        start_tasks = {
            name: asyncio.create_task(service.start())
            for name, service in self.services.items()
        }
        
        for name, task in start_tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                logging.error(f"Failed to start service {name}: {e}")
                results[name] = False
        
        # Publish supervisor started event
        await self.bus.publish("mcp.supervisor.started", {
            "services": list(self.services.keys()),
            "results": results,
            "timestamp": time.time()
        })
        
        return results
    
    async def stop_all(self) -> None:
        """Stop all managed services."""
        self.shutdown_event.set()
        
        # Stop services in parallel
        stop_tasks = [
            asyncio.create_task(service.stop())
            for service in self.services.values()
        ]
        
        await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        # Clean up MCP client connections
        await shutdown_mcp_clients()
        
        # Publish supervisor stopped event
        await self.bus.publish("mcp.supervisor.stopped", {
            "services": list(self.services.keys()),
            "timestamp": time.time()
        })
    
    async def restart_service(self, service_name: str) -> bool:
        """Restart a specific service."""
        if service_name not in self.services:
            return False
        
        return await self.services[service_name].restart()
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services."""
        status = {}
        for name, service in self.services.items():
            status[name] = {
                "running": service.running,
                "restart_count": service.restart_count,
                "pid": service.process.pid if service.process else None,
                "last_restart": service.last_restart
            }
        return status
    
    @asynccontextmanager
    async def lifecycle(self):
        """Context manager for service lifecycle."""
        try:
            # Set up signal handlers for graceful shutdown
            if os.name != 'nt':  # Unix systems
                def signal_handler(signum, frame):
                    asyncio.create_task(self.stop_all())
                
                signal.signal(signal.SIGTERM, signal_handler)
                signal.signal(signal.SIGINT, signal_handler)
            
            # Start services
            results = await self.start_all()
            logging.info(f"MCP Supervisor started services: {results}")
            
            yield self
            
        finally:
            # Clean shutdown
            await self.stop_all()
            logging.info("MCP Supervisor shutdown complete")


# Default configurations for standard services
DEFAULT_SERVICES = {
    "data-collector": MCPServiceConfig(
        name="data-collector",
        command="python",
        args=["-u", "-m", "core.agents.data_collector.mcp_server"],
        env={"USE_MCP": "1"}
    ),
    "alert-service": MCPServiceConfig(
        name="alert-service", 
        command="python",
        args=["-u", "-m", "core.agents.alert_service.mcp_server"],
        env={"USE_MCP": "1"}
    ),
    "price-optimizer": MCPServiceConfig(
        name="price-optimizer",
        command="python", 
        args=["-u", "-m", "core.agents.price_optimizer.mcp_server"],
        env={"USE_MCP": "1"}
    )
}


def create_default_supervisor() -> MCPSupervisor:
    """Create supervisor with default service configurations."""
    supervisor = MCPSupervisor()
    
    for config in DEFAULT_SERVICES.values():
        supervisor.add_service(config)
    
    return supervisor