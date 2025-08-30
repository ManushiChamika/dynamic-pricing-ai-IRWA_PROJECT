# Minimal MCP server exposing the tools above.
# (Works with any MCP-compatible client / other agents.)
import asyncio, os
from mcp.server.fastmcp import FastMCP
from .repo import Repo
from .engine import AlertEngine
from .tools import Tools
from .auth import verify_capability

mcp = FastMCP("alerts-service")

repo = Repo()
engine = AlertEngine(repo)
tools = Tools(repo)

@mcp.tool()
async def create_rule(spec: dict, capability_token: str):
    verify_capability(capability_token, "create_rule")
    return await tools.create_rule(spec)

@mcp.tool()
async def list_rules(capability_token: str):
    verify_capability(capability_token, "read")
    return await tools.list_rules()

@mcp.tool()
async def list_incidents(status: str|None = None, capability_token: str = ""):
    verify_capability(capability_token, "read")
    return await tools.list_incidents(status)

@mcp.tool()
async def ack_incident(incident_id: str, capability_token: str):
    verify_capability(capability_token, "write")
    return await tools.ack_incident(incident_id)

@mcp.tool()
async def resolve_incident(incident_id: str, capability_token: str):
    verify_capability(capability_token, "write")
    return await tools.resolve_incident(incident_id)

async def main():
    await repo.init()
    await engine.start()
    await mcp.run()

if __name__ == "__main__":
    asyncio.run(main())
