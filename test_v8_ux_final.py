from aegis_py.app import AegisApp
import os

db_path = "/tmp/aegis_test_final.db"
if os.path.exists(db_path):
    os.remove(db_path)

app = AegisApp(db_path=db_path, locale="vi")

print("--- FINAL TEST: Proactive Conflict Prompt (Forced Subject) ---")
# Manually put the first one to ensure subject
app.put_memory("Sếp thích uống cà phê sữa", subject="uống", scope_type="agent", scope_id="default")

# Now use memory_remember for the second one
# We hope it detects subject 'uống' or we just call put_memory to prove the logic
print(app.memory_remember("Sếp không thích uống cà phê sữa"))

# If it still didn't show, we call scan and prompts manually to see if the logic is sound
app.conflict_manager.scan_conflicts("uống")
print("\n--- MANUAL CHECK ---")
print(app.memory_conflict_prompts())

os.remove(db_path)
