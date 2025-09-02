# core/agents/user_interact/hub.py
import asyncio
from core.bus import bus
from core.agents.pricing_optimizer import PricingOptimizerAgent
from core.agents.auto_applier import AutoApplier
from core.agents.user_interact.user_interaction_agent import USER_REQUEST, USER_REPLY

class OptimizerHub:
    def __init__(self):
        self._started = False

    async def start(self):
        if self._started: 
            return
        self._started = True

        # ensure AutoApplier is running so applied price hits DB + events
        try:
            self._aa = AutoApplier()
            await self._aa.start()
        except Exception:
            self._aa = None

        async def on_user_request(msg):
            sku = (msg or {}).get("sku")
            intent = (msg or {}).get("intent", "")
            if not sku:
                await bus.publish(USER_REPLY, {"status":"error","message":"Missing SKU"})
                return

            # Run the (sync) optimizer in a thread
            loop = asyncio.get_running_loop()
            agent = PricingOptimizerAgent()
            try:
                res = await loop.run_in_executor(
                    None,
                    lambda: agent.process_full_workflow(intent, sku)  # returns dict
                )
                if isinstance(res, dict) and res.get("status") == "success":
                    await bus.publish(USER_REPLY, {
                        "status":"success",
                        "sku": sku,
                        "price": res.get("price"),
                        "algorithm": res.get("algorithm"),
                    })
                else:
                    await bus.publish(USER_REPLY, {
                        "status":"error",
                        "message": str(res)
                    })
            except Exception as e:
                await bus.publish(USER_REPLY, {"status":"error","message": str(e)})

        bus.subscribe(USER_REQUEST, on_user_request)
