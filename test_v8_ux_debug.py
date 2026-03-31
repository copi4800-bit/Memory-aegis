from aegis_py.app import AegisApp
import os

db_path = "/tmp/aegis_test_v8_ux_debug.db"
if os.path.exists(db_path):
    os.remove(db_path)

app = AegisApp(db_path=db_path, locale="vi")

print("--- DEBUG TEST 1: Correction Status ---")
app.put_memory("Sếp thích uống cà phê đen", subject="uống", scope_type="agent", scope_id="default")
app.put_memory(
    "Nhầm rồi, sếp thích uống cà phê sữa", 
    subject="uống", 
    scope_type="agent", 
    scope_id="default", 
    metadata={"is_correction": True}
)

# Check status of the first memory
rows = app.storage.fetch_all("SELECT id, content, status FROM memories")
for row in rows:
    print(f"ID: {row['id']}, Content: {row['content']}, Status: {row['status']}")

print("\n--- RECALL WITH EXPLAIN ---")
print(app.memory_recall("cà phê", retrieval_mode="explain"))

os.remove(db_path)
