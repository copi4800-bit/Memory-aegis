# Structure

## Root
- `aegis_py/`: canonical engine implementation
- `specs/`: feature source of truth
- `.specify/`: Spec Kit templates and constitution
- `.planning/`: GSD orchestration notes
- `index.ts`: transitional host bootstrap entry
- `package.json`: current host packaging metadata

## Canonical Source
- `aegis_py/app.py`: local orchestration surface
- `aegis_py/mcp/server.py`: tool-facing Python adapter
- `aegis_py/main.py`: lightweight runtime entrypoints
- `aegis_py/storage/`: persistence
- `aegis_py/retrieval/`: search and benchmarking
- `aegis_py/hygiene/`: lifecycle maintenance
- `aegis_py/conflict/`: conflict handling
- `aegis_py/preferences/`: style/profile extraction

## Transitional Source
- `src/`: legacy host/bootstrap modules pending removal or quarantine under feature `005`
- `test/`: repository-level host/bootstrap regression coverage

## Testing
- `tests/`: canonical Python regression suite
- `test/`: transitional host/bootstrap-facing tests
