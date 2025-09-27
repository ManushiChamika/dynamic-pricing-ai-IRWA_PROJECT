from __future__ import annotations

import asyncio
from pathlib import Path as _Path0
import sys as _Sys0

# Ensure repo root on sys.path for module imports
_root0 = _Path0(__file__).resolve().parents[1]
if str(_root0) not in _Sys0.path:
    _Sys0.path.insert(0, str(_root0))

from core.agents.governance_execution_agent import GovernanceExecutionAgent
from core.observability.logging import init_logging, new_correlation_id, get_logger


async def main() -> None:
    init_logging(agent_name="governance-execution-agent")
    new_correlation_id()
    log = get_logger("runner")

    agent = GovernanceExecutionAgent()
    await agent.start()
    log.info("agent_started", message="GovernanceExecutionAgent started. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        log.info("agent_stopping")
    finally:
        await agent.stop()
        log.info("agent_stopped")


if __name__ == "__main__":
    asyncio.run(main())

