from __future__ import annotations

from collections import deque
from typing import Any


def summarize_local_graph(*, nodes: list[dict[str, Any]], links: list[dict[str, Any]]) -> dict[str, Any]:
    """Return bounded local-only graph diagnostics over SQLite-backed snapshots."""
    adjacency: dict[str, set[str]] = {}
    for node in nodes:
        adjacency.setdefault(node["id"], set())
    for link in links:
        source = link.get("source")
        target = link.get("target")
        if source not in adjacency or target not in adjacency:
            continue
        adjacency[source].add(target)
        adjacency[target].add(source)

    visited: set[str] = set()
    component_sizes: list[int] = []
    for node_id in adjacency:
        if node_id in visited:
            continue
        queue = deque([node_id])
        visited.add(node_id)
        size = 0
        while queue:
            current = queue.popleft()
            size += 1
            for neighbor in adjacency[current]:
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                queue.append(neighbor)
        component_sizes.append(size)

    degrees = sorted(
        (
            {"id": node_id, "degree": len(neighbors)}
            for node_id, neighbors in adjacency.items()
        ),
        key=lambda item: (-item["degree"], item["id"]),
    )
    return {
        "backend": "python",
        "analysis_mode": "local_only",
        "authoritative": False,
        "component_count": len(component_sizes),
        "largest_component": max(component_sizes, default=0),
        "top_degrees": degrees[:5],
    }
