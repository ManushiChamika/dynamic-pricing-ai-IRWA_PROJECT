import sqlite3
import uuid
from datetime import datetime, timezone

alert_db = "app/alert.db"
auth_db = "data/auth.db"

conn_auth = sqlite3.connect(auth_db)
cursor_auth = conn_auth.cursor()
cursor_auth.execute("SELECT id FROM users WHERE email = 'demo@example.com'")
result = cursor_auth.fetchone()
conn_auth.close()

if not result:
    print("Demo user not found!")
    exit(1)

demo_user_id = result[0]
print(f"Demo user ID: {demo_user_id}")

conn_alert = sqlite3.connect(alert_db)
cursor_alert = conn_alert.cursor()

cursor_alert.execute("SELECT COUNT(*) FROM incidents WHERE owner_id = ?", (demo_user_id,))
existing_count = cursor_alert.fetchone()[0]
print(f"Existing alerts for demo user: {existing_count}")

incident_id = f"inc_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
now = datetime.now(timezone.utc).isoformat()

cursor_alert.execute("""
    INSERT INTO incidents (id, rule_id, sku, status, first_seen, last_seen, severity, title, group_key, fingerprint, owner_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    incident_id,
    "demo_alert",
    "DEMO-PRODUCT",
    "OPEN",
    now,
    now,
    "high",
    "Demo Alert: Price Drop Detected",
    f"DEMO-PRODUCT",
    f"demo_alert:Price Drop:DEMO-PRODUCT",
    demo_user_id
))

conn_alert.commit()
print(f"Created incident: {incident_id}")

cursor_alert.execute("SELECT id, owner_id, sku, status, severity, title FROM incidents WHERE owner_id = ?", (demo_user_id,))
incidents = cursor_alert.fetchall()
print(f"\nAll incidents for demo user:")
for inc in incidents:
    print(f"  {inc}")

conn_alert.close()
print("\n✅ Demo alert created successfully!")
