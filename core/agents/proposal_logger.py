"""
Proposal Logger Agent - Persists PRICE_PROPOSAL events to database

This agent subscribes to PRICE_PROPOSAL events on the event bus and writes
them to app/data.db:price_proposals table for tracking and audit purposes.
"""

from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic


class ProposalLogger:
    """Subscribes to PRICE_PROPOSAL events and persists them to database."""
    
    def __init__(self, db_path: Path | None = None):
        self.logger = logging.getLogger("proposal_logger")
        
        # Default to app/data.db
        if db_path is None:
            db_path = Path(__file__).resolve().parents[2] / "app" / "data.db"
        
        self.db_path = db_path
        self._callback = None
        
    async def start(self) -> None:
        """Start listening for PRICE_PROPOSAL events."""
        self._ensure_table_exists()
        
        async def on_proposal(proposal: Dict[str, Any]):
            try:
                self._persist_proposal(proposal)
            except Exception as e:
                self.logger.error(f"Failed to persist proposal: {e}", exc_info=True)
        
        self._callback = on_proposal
        get_bus().subscribe(Topic.PRICE_PROPOSAL.value, self._callback)
        self.logger.info("ProposalLogger started - subscribed to PRICE_PROPOSAL events")
        
    async def stop(self) -> None:
        """Stop listening (cleanup on shutdown)."""
        self._callback = None
        self.logger.info("ProposalLogger stopped")
    
    def _ensure_table_exists(self) -> None:
        """Ensure price_proposals table exists with correct schema."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS price_proposals (
                        id TEXT PRIMARY KEY,
                        sku TEXT NOT NULL,
                        proposed_price REAL NOT NULL,
                        current_price REAL,
                        margin REAL,
                        algorithm TEXT,
                        ts TEXT NOT NULL
                    )
                """)
                conn.commit()
                self.logger.info("Verified price_proposals table exists")
        except Exception as e:
            self.logger.error(f"Failed to ensure table exists: {e}", exc_info=True)
    
    def _persist_proposal(self, proposal: Dict[str, Any]) -> None:
        """Write a single proposal to the database."""
        try:
            # Extract fields from proposal event
            proposal_id = proposal.get("proposal_id", str(uuid.uuid4()))
            sku = proposal.get("sku") or proposal.get("product_id")
            proposed_price = proposal.get("proposed_price") or proposal.get("new_price")
            current_price = proposal.get("current_price") or proposal.get("previous_price") or proposal.get("old_price")
            margin = proposal.get("margin", 0.0)
            algorithm = proposal.get("algorithm", "unknown")
            ts = datetime.now(timezone.utc).isoformat()
            
            # Validate required fields
            if not sku or proposed_price is None:
                self.logger.warning(f"Skipping proposal with missing data: {proposal}")
                return
            
            # Insert into database
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT INTO price_proposals (id, sku, proposed_price, current_price, margin, algorithm, ts)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    proposal_id,
                    sku,
                    float(proposed_price),
                    float(current_price) if current_price is not None else None,
                    float(margin) if margin is not None else 0.0,
                    algorithm,
                    ts
                ))
                conn.commit()
            
            self.logger.info(
                f"Persisted proposal: {sku} {current_price} → {proposed_price} "
                f"(margin={margin:.2%}, algo={algorithm})"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to persist proposal {proposal}: {e}", exc_info=True)
