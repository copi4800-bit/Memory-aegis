# Concerns

## Architectural Debt
- **Host Loader Constraint**: OpenClaw still appears to load the extension from `dist/index.js`, which may require a small JS bootstrap even after TS engine removal.
- **Legacy TS Engine Residue**: old modules under `src/` still exist in the repository and should be removed or quarantined as feature `005` progresses.

## Tech Risks
- **SQLite FTS5 Performance**: Ensuring FTS5 scaling with large memory sets.
- **Packaging Drift**: package metadata and runtime docs can drift if Python-first packaging is not kept aligned with the active specs.

## Scope Leakage
- Ensuring cross-project or cross-session memory remains strictly isolated (a core goal for v4).
