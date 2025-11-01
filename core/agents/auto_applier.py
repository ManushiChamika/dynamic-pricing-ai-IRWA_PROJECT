from __future__ import annotations

import asyncio
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic
from core.agents.agent_sdk.events_models import PriceProposal
from core.agents.auto_applier_db import AutoApplierDB


class AutoApplier:
    """Governance & Execution Agent for PRICE_PROPOSAL events.

    Subscribes to PRICE_PROPOSAL and evaluates merchant guardrails stored in
    app/data.db `settings` table with keys:
      - auto_apply: 'true' | 'false'
      - min_margin: float as string
      - max_delta: float as string (relative allowed change vs current_price)

    Behavior:
      - Always logs a decision into app/data.db `decision_log` before applying
      - If auto-apply enabled and guardrails pass: apply to app/data.db/pricing_list
        and publish price.update with actor="governance".
      - If not enabled or guardrails fail: log AWAITING_MANUAL_APPROVAL, no apply.
    """

    def __init__(self) -> None:
        self._callback = None
        self._db = AutoApplierDB(self._settings_path())

    async def start(self) -> None:
        async def on_proposal(pp: PriceProposal):
            try:
                self._handle_proposal_nonblocking(pp)
            except Exception as e:
                try:
                    print(f"[AutoApplier] on_proposal error: {e}")
                except Exception:
                    pass

        self._callback = on_proposal
        get_bus().subscribe(Topic.PRICE_PROPOSAL.value, self._callback)
        print("AutoApplier: subscribed to PRICE_PROPOSAL")

    async def stop(self) -> None:
        # Best-effort: _AsyncBus in agent_sdk doesn't have unsubscribe; ignore
        self._callback = None

    # --------------- internals ---------------
    def _settings_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "app" / "data.db"

    def _market_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "app" / "data.db"



    def _handle_proposal_nonblocking(self, pp: PriceProposal) -> None:
        try:
            auto_apply, min_margin, max_delta = self._db.load_settings()
        except Exception as e:
            try:
                print(f"[AutoApplier] failed to load settings: {e}")
            except Exception:
                pass
            return

        current_price = float(pp.current_price) if pp.current_price is not None else 0.0
        proposed_price = float(pp.proposed_price)
        if current_price > 0:
            delta_pct = abs(proposed_price - current_price) / current_price
        else:
            delta_pct = 0.0
        margin_ok = float(pp.margin) >= min_margin
        delta_ok = delta_pct <= max_delta

        old_price_for_log = self._db.get_old_price(pp.sku)
        if not auto_apply or not (margin_ok and delta_ok):
            self._db.insert_decision(
                sku=pp.sku,
                old_price=old_price_for_log if old_price_for_log is not None else (pp.current_price if pp.current_price is not None else None),
                new_price=proposed_price,
                margin=float(pp.margin) if pp.margin is not None else None,
                algorithm=str(pp.algorithm) if pp.algorithm is not None else None,
                decision="AWAITING_MANUAL_APPROVAL",
                actor="governance",
                proposal_id=None,
            )
            return

        def _apply():
            market_db_path = self._market_path()
            proposal_id = self._db.get_proposal_id(pp.sku, proposed_price)
            backoff = [0.01, 0.02, 0.05, 0.1, 0.25, 0.5]
            committed = False
            for delay in backoff:
                success = self._db.apply_price_atomic(
                    market_db_path=market_db_path,
                    sku=pp.sku,
                    proposed_price=proposed_price,
                    margin=float(pp.margin) if pp.margin is not None else None,
                    algorithm=str(pp.algorithm) if pp.algorithm is not None else None,
                    proposal_id=proposal_id,
                    current_price=pp.current_price,
                )
                if success:
                    committed = True
                    break
                time.sleep(delay)
            if not committed:
                return

            # Publish schema-compliant price.update event after commit
            payload = {
                "proposal_id": proposal_id or str(uuid.uuid4()),
                "product_id": pp.sku,
                "final_price": proposed_price,
            }

            async def _pub():
                try:
                    await get_bus().publish(Topic.PRICE_UPDATE.value, payload)
                except Exception as e:
                    try:
                        print(f"[AutoApplier] publish PRICE_UPDATE failed: {e}")
                    except Exception:
                        pass

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_pub())
            except RuntimeError:
                threading.Thread(target=lambda: asyncio.run(_pub()), daemon=True).start()

        # Offload to background thread to avoid blocking the bus callback
        threading.Thread(target=_apply, daemon=True).start()
