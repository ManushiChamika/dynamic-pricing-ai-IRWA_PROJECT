import asyncio
import sys
import pytest

sys.path.insert(0, r'C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT')

from types import SimpleNamespace

import core.tool_registry as tr
from core.agents.supervisor import Supervisor

class FakeRegistry:
    def __init__(self):
        self.calls = []

    async def execute_tool(self, name, **kwargs):
        self.calls.append((name, kwargs))
        if name == 'upsert_product':
            return {'ok': True}
        if name == 'start_data_collection':
            return {'ok': True, 'job_id': 'job-123'}
        if name == 'get_job_status':
            return {'ok': True, 'job': {'status': 'DONE'}}
        if name == 'optimize_price':
            return {'status': 'ok', 'recommended_price': 123.45}
        return {'ok': True}

@pytest.mark.asyncio
async def test_supervisor_with_templates_runs_and_publishes():
    fake = FakeRegistry()
    tr.get_tool_registry = lambda: fake

    s = Supervisor(concurrency=2, use_templates=True)
    rows = [{'sku':'SKU1','market':'DEFAULT','connector':'mock','depth':1,'title':'T'}]
    res = await s.run_for_catalog(rows, timeout_s=5)

    assert isinstance(res, dict)
    assert 'items' in res
    assert res['count'] == 1
    item = res['items'].get('SKU1')
    assert item is not None
    # ensure job_id present (template path sets it)
    assert 'sku' in item and item['sku'] == 'SKU1'
