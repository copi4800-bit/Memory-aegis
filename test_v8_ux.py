from aegis_py.app import AegisApp
import os
from datetime import datetime

db_path = "/tmp/aegis_test_v8_ux.db"
if os.path.exists(db_path):
    os.remove(db_path)

app = AegisApp(db_path=db_path, locale="vi")

# 1. Test Correction & Why-not
print("--- TEST 1: Correction & Why-not ---")
# First record
app.put_memory("Sếp thích uống cà phê đen", subject="uống", scope_type="agent", scope_id="default")
# Second record (correction)
# Use put_memory with subject and metadata to force the transition
app.put_memory(
    "Nhầm rồi, sếp thích uống cà phê sữa", 
    subject="uống", 
    scope_type="agent", 
    scope_id="default", 
    metadata={"is_correction": True}
)

# Recall with explain mode
print(app.memory_recall("cà phê", retrieval_mode="explain"))

# 2. Test Health Snapshot
print("\n--- TEST 2: Memory Health ---")
now = datetime.now().isoformat()
fields = "id, content, subject, status, scope_type, scope_id, type, source_kind, source_ref, created_at, updated_at"
values = "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
app.storage.execute(
    f"INSERT INTO memories ({fields}) VALUES ({values})",
    ("mem_fake_1", "Sếp thích trà gừng", "uống", "active", "agent", "default", "episodic", "manual", "test", now, now)
)
app.storage.execute(
    f"INSERT INTO memories ({fields}) VALUES ({values})",
    ("mem_fake_2", "Sếp thích trà đào", "uống", "active", "agent", "default", "episodic", "manual", "test", now, now)
)

print(app.memory_health_summary())

os.remove(db_path)
