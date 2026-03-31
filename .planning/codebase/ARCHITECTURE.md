# Architecture

## System Design
- **Canonical Engine**: `aegis_py`
- **Persistence**: SQLite + FTS5 under `aegis_py/storage/`
- **Retrieval**: scoped and explainable search under `aegis_py/retrieval/`
- **Lifecycle**: hygiene and conflict flows under `aegis_py/hygiene/` and `aegis_py/conflict/`
- **Integration**: `aegis_py/app.py`, `aegis_py/main.py`, and `aegis_py/mcp/server.py`
- **Host Boundary**: `index.ts` is transitional bootstrap only while OpenClaw still loads JS entrypoints

## Key Abstractions
- **Memories**: `working`, `episodic`, `semantic`, `procedural`
- **Scopes**: explicit `scope_type` + `scope_id`
- **Provenance**: `source_kind`, `source_ref`, explanation payloads
- **Hooks**: OpenClaw lifecycle points bridged to Python where still needed
