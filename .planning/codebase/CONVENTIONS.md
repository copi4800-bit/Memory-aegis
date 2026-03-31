# Conventions

## Workflow
- `specs/*` is the feature source of truth.
- `.planning/*` is a GSD orchestration layer only.
- `.specify/memory/constitution.md` is the repository governance baseline.
- Combined workflow contract: `specs/*` for feature truth and `.planning/*` for orchestration only.

## Coding Standards
- **Runtime Direction**: Python-first.
- **TypeScript**: Transitional host/bootstrap code only where still required.
- **Imports**: Direct file imports (`.js` extension in TS for ESM compatibility).
- **Async**: Pervasive use of `async/await`.
- **Error Handling**: Explicit try/catch in hooks to prevent crashing the host (OpenClaw).

## Naming
- **Python Surface**: `AegisApp` and MCP tool handlers are the canonical runtime names.
- **Bootstrap Surface**: any remaining host bootstrap should stay thin and avoid owning engine logic.
- **Subsystems**: Named after animals (WeaverBird, Meerkat, Bowerbird, Axolotl).
- **Tools**: Prefixed with `memory_` (e.g., `memory_search`).

## Commits
- Typically follows atomic commit patterns (feat, fix, refactor).
