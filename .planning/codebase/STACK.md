# Stack

## Core
- **Runtime**: Python 3.13.x
- **Language**: Python
- **Host Bootstrap**: TypeScript/Node only where OpenClaw still requires JS loading
- **Validation Runner**: pytest

## Storage
- **Database**: SQLite (local-first)
- **Search**: SQLite FTS5 (Full-Text Search)
- **Schema**: `aegis_py/storage/schema.sql`

## Dependencies
- `pydantic`
- `aiosqlite`
- `fastmcp`
- `pytest`
- `OpenClaw` host bootstrap contract
