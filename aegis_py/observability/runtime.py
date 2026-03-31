import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any


logger = logging.getLogger("aegis.runtime.observability")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

_GLOBAL_RUNTIME_OBSERVABILITY: "RuntimeObservability | None" = None


def build_runtime_event(
    *,
    tool: str,
    result: str,
    scope_type: str | None = None,
    scope_id: str | None = None,
    session_id: str | None = None,
    latency_ms: float | None = None,
    error_code: str | None = None,
    backend: str = "python",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "backend": backend,
        "tool": tool,
        "scope_type": scope_type,
        "scope_id": scope_id,
        "session_id": session_id,
        "latency_ms": None if latency_ms is None else round(float(latency_ms), 3),
        "result": result,
        "error_code": error_code,
        "details": details or {},
    }
    return event


class RuntimeObservability:
    def __init__(self, *, recent_limit: int = 50):
        self._recent_limit = recent_limit
        self._recent_events: deque[dict[str, Any]] = deque(maxlen=recent_limit)
        self._counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._latencies: dict[str, list[float]] = defaultdict(list)

    def record(self, event: dict[str, Any]) -> dict[str, Any]:
        tool = str(event["tool"])
        result = str(event["result"])
        latency_ms = event.get("latency_ms")
        self._recent_events.append(event)
        self._counts[tool][result] += 1
        if latency_ms is not None:
            self._latencies[tool].append(float(latency_ms))
        logger.info(json.dumps(event, sort_keys=True))
        return event

    def observe(
        self,
        *,
        tool: str,
        result: str,
        scope_type: str | None = None,
        scope_id: str | None = None,
        session_id: str | None = None,
        latency_ms: float | None = None,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        backend: str = "python",
    ) -> dict[str, Any]:
        event = build_runtime_event(
            tool=tool,
            result=result,
            scope_type=scope_type,
            scope_id=scope_id,
            session_id=session_id,
            latency_ms=latency_ms,
            error_code=error_code,
            backend=backend,
            details=details,
        )
        return self.record(event)

    def snapshot(self) -> dict[str, Any]:
        tools: dict[str, dict[str, Any]] = {}
        for tool, results in self._counts.items():
            latencies = sorted(self._latencies.get(tool, []))
            entry = {
                "counts": dict(results),
                "total": sum(results.values()),
            }
            if latencies:
                mid = len(latencies) // 2
                entry["latency_ms"] = {
                    "min": latencies[0],
                    "p50": latencies[mid],
                    "max": latencies[-1],
                }
            else:
                entry["latency_ms"] = {}
            tools[tool] = entry
        return {
            "backend": "python",
            "tools": tools,
            "recent": list(self._recent_events),
        }


def get_global_runtime_observability() -> RuntimeObservability:
    global _GLOBAL_RUNTIME_OBSERVABILITY
    if _GLOBAL_RUNTIME_OBSERVABILITY is None:
        _GLOBAL_RUNTIME_OBSERVABILITY = RuntimeObservability()
    return _GLOBAL_RUNTIME_OBSERVABILITY


def reset_global_runtime_observability() -> None:
    global _GLOBAL_RUNTIME_OBSERVABILITY
    _GLOBAL_RUNTIME_OBSERVABILITY = RuntimeObservability()


def merge_observability_snapshots(*snapshots: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "backend": "python",
        "tools": {},
        "recent": [],
    }
    recent_events: list[dict[str, Any]] = []
    for snapshot in snapshots:
        for tool, entry in snapshot.get("tools", {}).items():
            target = merged["tools"].setdefault(tool, {"counts": {}, "total": 0, "latency_values": []})
            for result, count in entry.get("counts", {}).items():
                target["counts"][result] = target["counts"].get(result, 0) + count
            target["total"] += entry.get("total", 0)
            latency = entry.get("latency_ms", {})
            for key in ("min", "p50", "max"):
                if key in latency:
                    target["latency_values"].append(float(latency[key]))
        recent_events.extend(snapshot.get("recent", []))

    for tool, entry in merged["tools"].items():
        values = sorted(entry.pop("latency_values"))
        if values:
            mid = len(values) // 2
            entry["latency_ms"] = {
                "min": values[0],
                "p50": values[mid],
                "max": values[-1],
            }
        else:
            entry["latency_ms"] = {}

    recent_events.sort(key=lambda item: item.get("ts", ""))
    merged["recent"] = recent_events[-50:]
    return merged


class ObservedOperation:
    def __init__(
        self,
        observability: RuntimeObservability,
        *,
        tool: str,
        scope_type: str | None = None,
        scope_id: str | None = None,
        session_id: str | None = None,
    ):
        self._observability = observability
        self._tool = tool
        self._scope_type = scope_type
        self._scope_id = scope_id
        self._session_id = session_id
        self._started = time.perf_counter()

    def finish(
        self,
        *,
        result: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        scope_type: str | None = None,
        scope_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        latency_ms = (time.perf_counter() - self._started) * 1000.0
        return self._observability.observe(
            tool=self._tool,
            result=result,
            scope_type=scope_type if scope_type is not None else self._scope_type,
            scope_id=scope_id if scope_id is not None else self._scope_id,
            session_id=session_id if session_id is not None else self._session_id,
            latency_ms=latency_ms,
            error_code=error_code,
            details=details,
        )
