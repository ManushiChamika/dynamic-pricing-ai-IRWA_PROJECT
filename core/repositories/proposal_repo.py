from datetime import datetime
from sqlalchemy import insert
from core.db import SessionLocal, PriceProposalRow

class ProposalRepo:
    def insert_proposal(self, p: dict) -> None:
        with SessionLocal() as db:
            db.execute(
                insert(PriceProposalRow).values(
                    sku=p["sku"],
                    proposed_price=p["proposed_price"],
                    current_price=p.get("current_price"),
                    margin=p["margin"],
                    algorithm=p.get("algorithm", "simple"),
                    ts_iso=(p["ts"].isoformat() if isinstance(p["ts"], datetime) else str(p["ts"])),
                )
            )
            db.commit()
