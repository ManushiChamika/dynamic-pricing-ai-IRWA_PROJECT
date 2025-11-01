import asyncio
import sys
import pytest

sys.path.insert(0, r'C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT')

import core.tool_registry as tr
from core.workflow_templates import collect_and_optimize_prelude
from core.agents.supervisor import Supervisor

class FailStartRegistry:
    async def execute_tool(self, name, **kwargs):
        if name == 'upsert_product':
            return {'ok': True}
        if name == 'start_data_collection':
            return {'ok': False, 'error': 'bad connector'}
        return {'ok': True}

class FailOptimizeRegistry:
    async def execute_tool(self, name, **kwargs):
        if name == 'upsert_product':
            return {'ok': True}
        if name == 'start_data_collection':
            return {'ok': True, 'job_id': 'job-1'}
        if name == 'get_job_status':
            return {'ok': True, 'job': {'status': 'DONE'}}
        if name == 'optimize_price':
            return {'status': 'error', 'reason': 'optimizer crash'}
        return {'ok': True}

@pytest.mark.asyncio
async def test_collect_prelude_failure():
    tr.get_tool_registry = lambda: FailStartRegistry()
    import core.workflow_templates as wt
    import core.agents.supervisor as sup
    wt.get_tool_registry = lambda: FailStartRegistry()
    sup.get_tool_registry = lambda: FailStartRegistry()
    res = await collect_and_optimize_prelude({'sku':'X'}, timeout_s=1, max_retries=1)
    assert res.get('ok') is False

@pytest.mark.asyncio
async def test_supervisor_handles_optimizer_failure():
    tr.get_tool_registry = lambda: FailOptimizeRegistry()
    import core.workflow_templates as wt
    import core.agents.supervisor as sup
    wt.get_tool_registry = lambda: FailOptimizeRegistry()
    sup.get_tool_registry = lambda: FailOptimizeRegistry()
    s = Supervisor(concurrency=1, use_templates=True)
    rows = [{'sku':'SKU2'}]
    res = await s.run_for_catalog(rows, timeout_s=1)
    assert res['count'] == 1
    item = list(res['items'].values())[0]
    # item should contain optimizer result and it should show the failure status
    assert 'optimizer' in item
    assert item['optimizer'].get('status') == 'error'
