import asyncio, sys
sys.path.insert(0, r'C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT')
from core.agents.supervisor import Supervisor
async def main():
    s = Supervisor(concurrency=2)
    res = await s.run_for_catalog([])
    print('OK', res)
if __name__ == '__main__':
    asyncio.run(main())
