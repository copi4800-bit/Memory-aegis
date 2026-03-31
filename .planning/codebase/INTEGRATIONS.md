# Integrations

## Internal Modules
- **AegisApp**: canonical orchestration surface
- **AegisMCPServer**: MCP-oriented tool adapter
- **StorageManager**: SQLite persistence and lifecycle-safe state mutation
- **SearchPipeline**: scoped, explainable retrieval
- **ConflictManager**: suggestion-first contradiction handling

## External
- **OpenClaw**: host environment; may still require a JS bootstrap entry
- **MCP (Model Context Protocol)**: local tool exposure for agents
- **FileSystem**: local SQLite DB and release packaging assets
