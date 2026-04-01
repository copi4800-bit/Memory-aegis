from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class AegisHealthSurface:
    """Health and status facade extracted from AegisApp."""

    def __init__(self, app: Any):
        self.app = app

    def doctor(self, workspace_dir: str | None = None) -> dict[str, Any]:
        effective_workspace = (
            Path(workspace_dir).expanduser()
            if workspace_dir
            else Path(self.app.db_path).expanduser().parent
        )
        health = self.app._runtime_health_snapshot(workspace_dir=effective_workspace)
        memory_count = self.app._safe_count("SELECT COUNT(*) AS count FROM memories")
        conflict_count = self.app._safe_count(
            "SELECT COUNT(*) AS count FROM conflicts WHERE status IN ('open', 'suggested')"
        )
        storage = self.safe_storage_footprint()
        storage_policy = self.app.storage_compaction_policy()
        historical_rows = (
            storage["rows"].get("evidence_events", 0)
            + storage["rows"].get("evidence_artifacts", 0)
            + storage["rows"].get("governance_events", 0)
            + storage["rows"].get("replication_audit_log", 0)
            + storage["rows"].get("autonomous_audit_log", 0)
            + storage["rows"].get("background_intelligence_runs", 0)
        )
        storage_health = {
            "allocated_bytes": storage["allocated_bytes"],
            "free_bytes": storage["free_bytes"],
            "memory_rows": storage["rows"].get("memories", 0),
            "historical_rows": historical_rows,
            "compaction_policy": storage_policy,
        }

        # v9 Intelligence Metrics
        v9_metrics = {
            "truth_alignment_score": 0.95, # Placeholder for actual benchmark result
            "conflict_load_index": min(1.0, conflict_count / 10.0),
            "correction_churn": self.app._safe_count("SELECT COUNT(*) FROM memories WHERE status = 'superseded' AND updated_at > datetime('now', '-7 days')"),
            "stale_pressure": self.app._safe_count("SELECT COUNT(*) FROM memories WHERE last_accessed_at < datetime('now', '-30 days')"),
        }

        return {
            "backend": "python",
            "status": health["state"].lower(),
            "health": health,
            "health_state": health["state"],
            "v9_intelligence": v9_metrics,
            "workspace": {"path": str(effective_workspace), "writable": health["workspace_writable"]},
            "database": {"path": self.app.db_path, "exists": health["database_exists"]},
            "counts": {
                "memories": memory_count,
                "open_conflicts": conflict_count,
            },
            "storage": storage_health,
            "issues": [issue["code"] for issue in health["issues"]],
        }

    def status(self) -> dict[str, Any]:
        health = self.app._runtime_health_snapshot()
        rows: dict[str, int] = {}
        try:
            counts = self.app.storage.fetch_all("SELECT status, COUNT(*) AS count FROM memories GROUP BY status")
            rows = {row["status"]: row["count"] for row in counts}
        except sqlite3.Error:
            rows = {}
        storage = self.safe_storage_footprint()
        return {
            "db_path": self.app.db_path,
            "counts": rows,
            "style_hint": self.app.style_tracker.get_style_hints(),
            "health": health,
            "health_state": health["state"],
            "storage": {
                "allocated_bytes": storage["allocated_bytes"],
                "free_bytes": storage["free_bytes"],
                "rows": storage["rows"],
            },
        }

    def status_summary(self) -> str:
        payload = self.status()
        health = payload["health"]
        counts = payload["counts"]
        active = counts.get("active", 0)
        health_state = health["state"]

        lines = ["## Aegis Status", ""]
        if health_state == "HEALTHY":
            lines.append("Aegis is ready and local memory is working normally.")
        elif health_state == "DEGRADED_SYNC":
            lines.append("Aegis is usable locally, but some optional sync-related features are degraded.")
        else:
            lines.append("Aegis is not ready for safe memory use right now because the local runtime is broken.")

        lines.extend(
            [
                "",
                f"Active memories: {active}",
                f"Health state: {health_state}",
                f"Allocated storage: {payload['storage']['allocated_bytes']} bytes",
            ]
        )

        if health_state == "DEGRADED_SYNC":
            lines.append("Local remember and recall still work.")
        if health_state == "BROKEN":
            lines.append("Fix the local database or workspace issue before relying on memory.")

        issue_codes = [issue["code"] for issue in health["issues"]]
        if issue_codes:
            lines.extend(["", "Current issues:"])
            lines.extend([f"- {code}" for code in issue_codes])

        return "\n".join(lines)

    def doctor_summary(self, workspace_dir: str | None = None) -> str:
        payload = self.doctor(workspace_dir=workspace_dir)
        health_state = payload["health_state"]
        lines = ["## Aegis Doctor", ""]

        if health_state == "HEALTHY":
            lines.append("Aegis memory is operating normally.")
        elif health_state == "DEGRADED_SYNC":
            lines.append("Aegis is usable locally, but some optional sync-related features are degraded.")
        else:
            lines.append("Aegis is not ready for safe memory use right now.")

        lines.extend(
            [
                "",
                f"Workspace: {payload['workspace']['path']}",
                f"Database: {payload['database']['path']}",
                f"Health state: {health_state}",
                f"Memories tracked: {payload['counts']['memories']}",
                f"Allocated storage: {payload['storage']['allocated_bytes']} bytes",
                f"Historical rows: {payload['storage']['historical_rows']}",
            ]
        )

        if payload["issues"]:
            lines.extend(["", "Current issues:"])
            lines.extend([f"- {issue}" for issue in payload["issues"]])

        if payload["storage"]["historical_rows"] > payload["counts"]["memories"]:
            lines.extend(["", "Storage guidance:", "- Historical rows are outgrowing live memory. Run storage compaction soon."])

        if health_state == "BROKEN":
            lines.extend(["", "Next step:", "- Fix the local database or workspace problem before relying on memory."])
        elif health_state == "DEGRADED_SYNC":
            lines.extend(["", "Next step:", "- Local memory still works. Review sync-related issues when convenient."])

        return "\n".join(lines)

    def safe_storage_footprint(self) -> dict[str, Any]:
        try:
            return self.app.storage_footprint()
        except sqlite3.Error:
            return {
                "db_path": self.app.db_path,
                "allocated_bytes": 0,
                "free_bytes": 0,
                "page_count": 0,
                "page_size": 0,
                "freelist_count": 0,
                "rows": {"memories": 0},
            }
