from typing import Optional

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - depends on optional runtime package
    FastMCP = None

from .app import AegisApp

mcp = FastMCP("Aegis Memory Console") if FastMCP is not None else None

# Global App Instance (Lazy initialization to ensure DB path is ready)
_app: Optional[AegisApp] = None

def get_app() -> AegisApp:
    global _app
    if _app is None:
        _app = AegisApp()
    return _app

def put_memory(content: str, type: str = "episodic", scope_id: str = "default", session_id: Optional[str] = None) -> str:
    """
    Ingests a new memory into the engine.
    - content: The factual content or message to remember.
    - type: 'episodic' (events), 'semantic' (facts), 'working' (tasks/temp).
    - scope_id: The project, user, or topic ID the memory belongs to.
    - session_id: (Optional) The current conversation session ID for signal tracking.
    """
    app = get_app()
    mem = app.put_memory(content, type=type, scope_id=scope_id, session_id=session_id)
    if mem is None:
        return "No memory stored."
    return f"Memory stored: {mem.id} ({mem.type})"

def search_memories(query: str, scope_id: str, limit: int = 5) -> str:
    """
    Retrieves relevant memories based on a query within a scope.
    """
    app = get_app()
    results = app.search(query, scope_id=scope_id, limit=limit)
    if not results:
        return "No relevant memories found."
    
    output = []
    for r in results:
        output.append(f"- [{r.memory.type}] {r.memory.content} (Score: {r.score:.2f})\n  Reason: {r.reason}")
    return "\n".join(output)

def get_memory_profile(scope_id: str) -> str:
    """
    Returns a human-readable summary of the learned interaction style and core facts for a scope.
    Use this to understand who you are talking to and how they like to interact.
    """
    app = get_app()
    return app.render_profile(scope_id)

def get_service_info() -> dict:
    """
    Returns the Python-owned local-service descriptor for thin hosts or operator tooling.
    """
    app = get_app()
    surface = app.public_surface()
    return {
        "backend": "python",
        "service": {
            "name": "Aegis Python MCP Service",
            "runtime_version": surface["engine"]["runtime_version"],
            "deployment_model": surface["service_boundary"]["deployment_model"],
            "preferred_transport": surface["service_boundary"]["preferred_transport"],
        },
        "startup_contract": surface["service_boundary"]["startup_contract"],
        "default_operations": surface["consumer_contract"]["default_operations"],
    }

def get_startup_probe() -> dict:
    """
    Returns a lightweight startup probe for process-managed local service usage.
    """
    app = get_app()
    doctor = app.doctor()
    ready = doctor["health_state"] in {"HEALTHY", "DEGRADED_SYNC"}
    return {
        "backend": "python",
        "ready": ready,
        "health_state": doctor["health_state"],
        "workspace": doctor["workspace"],
        "database": doctor["database"],
    }

def reinforce_fact(memory_id: str) -> str:
    """
    Manually increases the activation score of an existing memory.
    Use this when a piece of information is explicitly confirmed as important.
    """
    app = get_app()
    app.reinforce(memory_id)
    return f"Memory {memory_id} reinforced."

def end_current_session(session_id: str, scope_id: str):
    """
    Finalizes the current session: archives working memory and consolidates learned style signals.
    """
    app = get_app()
    app.end_session(session_id, scope_id, "session")
    return "Session finalized. Habits consolidated."

if mcp is not None:
    mcp.tool()(put_memory)
    mcp.tool()(search_memories)
    mcp.tool()(get_memory_profile)
    mcp.tool()(get_service_info)
    mcp.tool()(get_startup_probe)
    mcp.tool()(reinforce_fact)
    mcp.tool()(end_current_session)

if __name__ == "__main__":
    if mcp is None:
        raise SystemExit("fastmcp is not installed")
    mcp.run()
