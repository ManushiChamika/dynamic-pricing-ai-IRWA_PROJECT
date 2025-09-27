#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root on path
sys.path.insert(0, os.path.abspath('.'))


def _read_jsonl(file: Path) -> List[Dict[str, Any]]:
    if not file.exists():
        return []
    out: List[Dict[str, Any]] = []
    with file.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def test_publish_writes_journal_once_and_dispatches_once() -> None:
    # Import locally to avoid side effects before truncation
    from core.agents.agent_sdk.bus_factory import get_bus
    import core.events.journal as journal

    topic = 'test.bus.journal.once'
    payload = {'x': 1}

    # Start from a clean slate for this topic
    try:
        if journal._JOURNAL_FILE.exists():  # type: ignore[attr-defined]
            # Filter out prior test records for stability
            prev = _read_jsonl(journal._JOURNAL_FILE)  # type: ignore[attr-defined]
            remaining = [r for r in prev if r.get('topic') != topic]
            with journal._JOURNAL_FILE.open('w', encoding='utf-8') as f:  # type: ignore[attr-defined]
                for r in remaining:
                    f.write(json.dumps(r, ensure_ascii=False) + '\n')
    except Exception:
        pass

    # Set up subscriber to count invocations
    calls: List[Dict[str, Any]] = []

    def _handler(msg):
        calls.append({'msg': msg})

    async def _run():
        bus = get_bus()
        bus.subscribe(topic, _handler)
        await bus.publish(topic, payload)
        # Yield control to allow any pending tasks to run
        await asyncio.sleep(0)

    asyncio.run(_run())

    # Validate subscriber dispatch count
    assert len(calls) == 1, f'expected 1 subscriber call, got {len(calls)}'

    # Validate journal append count for this topic
    recs = _read_jsonl(journal._JOURNAL_FILE)  # type: ignore[attr-defined]
    recs_for_topic = [r for r in recs if r.get('topic') == topic]
    assert len(recs_for_topic) == 1, f'expected 1 journal record for topic, got {len(recs_for_topic)}'


if __name__ == '__main__':
    test_publish_writes_journal_once_and_dispatches_once()
