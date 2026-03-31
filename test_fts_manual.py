from aegis_py.app import AegisApp
import os

db_path = "/tmp/aegis_test_fts.db"
if os.path.exists(db_path):
    os.remove(db_path)

app = AegisApp(db_path=db_path)

app.storage.execute(
    "INSERT INTO memories (id, type, content, status, scope_type, scope_id, source_kind, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    ("mem1", "episodic", "Sếp thích cà phê đen", "superseded", "agent", "default", "manual", "now", "now")
)

# Test FTS MATCH
rows = app.storage.fetch_all(
    "SELECT m.id, m.status FROM memories m JOIN memories_fts fts ON m.id = fts.rowid WHERE memories_fts MATCH ?",
    ('"cà phê"',)
)
print(f"FTS results: {rows}")

os.remove(db_path)
