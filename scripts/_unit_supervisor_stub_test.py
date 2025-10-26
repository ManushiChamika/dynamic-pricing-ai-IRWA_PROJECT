import asyncio, sys
sys.path.insert(0, r'C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT')
from types import SimpleNamespace
import core.workflow_templates as wt
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

async def main():
    fake = FakeRegistry()
    # monkeypatch get_tool_registry used by both workflow_templates and supervisor
    import core.tool_registry as tr
    tr.get_tool_registry = lambda: fake

    s = Supervisor(concurrency=2, use_templates=True)
    rows = [{'sku':'SKU1','market':'DEFAULT','connector':'mock','depth':1,'title':'T'}]
    res = await s.run_for_catalog(rows, timeout_s=5)
    print('RESULT', res)

if __name__ == '__main__':
    asyncio.run(main())
