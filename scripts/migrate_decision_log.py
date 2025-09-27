import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "market.db"

def ensure_decision_log(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path.as_posix(), timeout=5.0, isolation_level=None)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=5000")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS decision_log (
              proposal_id TEXT PRIMARY KEY,
              product_id TEXT NOT NULL,
              previous_price REAL NOT NULL,
              proposed_price REAL NOT NULL,
              final_price REAL,
              status TEXT NOT NULL CHECK (status IN (
                'RECEIVED', 'APPROVED', 'REJECTED', 'APPLIED_AUTO', 'APPLY_FAILED', 'STALE'
              )),
              actor TEXT NOT NULL,
              reason TEXT,
              received_at TEXT NOT NULL,
              processed_at TEXT
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_decision_log_product_id ON decision_log(product_id)"
        )
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    print(f"Ensuring decision_log in {DB_PATH}")
    ensure_decision_log(DB_PATH)
    print("Done.")
