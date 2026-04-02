from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [here.parent, here.parent.parent]
    for candidate in candidates:
        if (candidate / "aegis_py" / "app.py").exists():
            return candidate
    raise RuntimeError("Unable to locate the Aegis repository root.")


@dataclass
class GauntletResult:
    name: str
    category: str
    passed: bool
    details: dict[str, Any]


def build_grouped_summary(results: list[GauntletResult]) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[GauntletResult]] = {}
    for item in results:
        grouped.setdefault(item.category, []).append(item)
    summary: dict[str, dict[str, float | int]] = {}
    for category, items in grouped.items():
        total = len(items)
        passed = sum(1 for item in items if item.passed)
        summary[category] = {
            "scenario_count": total,
            "pass_rate": round(passed / total, 3),
        }
    return summary


def sync_fts(storage) -> None:
    storage.execute("DELETE FROM memories_fts")
    storage.execute(
        "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
    )


def run_core_truth_case(manager, pipeline, storage) -> GauntletResult:
    from aegis_py.retrieval.models import SearchQuery
    from aegis_py.storage.models import Memory

    manager.store(
        Memory(
            id="gauntlet_old_addr",
            type="semantic",
            content="The office address is 100 First Street.",
            subject="office.address",
            confidence=0.8,
            source_kind="manual",
            source_ref="gauntlet://old",
            scope_type="agent",
            scope_id="gauntlet_truth",
        )
    )
    manager.store(
        Memory(
            id="gauntlet_new_addr",
            type="semantic",
            content="Correction: the office address is now 200 Second Street.",
            subject="office.address",
            confidence=1.0,
            source_kind="manual",
            source_ref="gauntlet://new",
            scope_type="agent",
            scope_id="gauntlet_truth",
            metadata={"is_winner": True, "is_correction": True, "corrected_from": ["gauntlet_old_addr"]},
        )
    )
    storage.execute("UPDATE memories SET status = 'superseded' WHERE id = 'gauntlet_old_addr'")
    sync_fts(storage)

    query = SearchQuery(
        query="office address",
        scope_type="agent",
        scope_id="gauntlet_truth",
        include_global=False,
        min_score=-10.0,
    )
    setattr(query, "intent", "correction_lookup")
    results = pipeline.search(query)
    winner = results[0].memory.id if results else None
    return GauntletResult(
        name="core_truth_correction_chain",
        category="core_truth",
        passed=winner == "gauntlet_new_addr",
        details={"selected_id": winner, "expected_id": "gauntlet_new_addr"},
    )


def run_scale_case(manager, pipeline, storage) -> GauntletResult:
    from aegis_py.retrieval.models import SearchQuery
    from aegis_py.storage.models import Memory

    for index in range(1000):
        manager.store(
            Memory(
                id=f"gauntlet_noise_{index}",
                type="semantic",
                content=f"Noise memory {index} about office calendars and coffee.",
                subject="noise.batch",
                confidence=0.2,
                source_kind="manual",
                source_ref=f"gauntlet://noise/{index}",
                scope_type="agent",
                scope_id="gauntlet_scale",
            )
        )
    manager.store(
        Memory(
            id="gauntlet_scale_target",
            type="semantic",
            content="The deployment region is Singapore.",
            subject="deployment.region",
            confidence=0.95,
            source_kind="manual",
            source_ref="gauntlet://scale-target",
            scope_type="agent",
            scope_id="gauntlet_scale",
            metadata={"is_winner": True},
        )
    )
    sync_fts(storage)

    query = SearchQuery(
        query="deployment region",
        scope_type="agent",
        scope_id="gauntlet_scale",
        include_global=False,
        min_score=-10.0,
    )
    setattr(query, "intent", "correction_lookup")
    results = pipeline.search(query)
    winner = results[0].memory.id if results else None
    return GauntletResult(
        name="scale_noise_resilience",
        category="scale",
        passed=winner == "gauntlet_scale_target",
        details={"selected_id": winner, "noise_count": 1000},
    )


def run_adversarial_case(manager, pipeline, storage) -> GauntletResult:
    from aegis_py.retrieval.models import SearchQuery
    from aegis_py.storage.models import Memory

    manager.store(
        Memory(
            id="gauntlet_adversarial_flashy",
            type="semantic",
            content="launch date launch date launch date April 1 launch date!",
            subject="launch.date",
            confidence=0.15,
            source_kind="manual",
            source_ref="gauntlet://flashy",
            scope_type="agent",
            scope_id="gauntlet_adversarial",
        )
    )
    manager.store(
        Memory(
            id="gauntlet_adversarial_winner",
            type="semantic",
            content="The verified launch date is April 24.",
            subject="launch.date",
            confidence=0.98,
            source_kind="manual",
            source_ref="gauntlet://winner",
            scope_type="agent",
            scope_id="gauntlet_adversarial",
            metadata={"is_winner": True},
        )
    )
    for index in range(5):
        storage.execute(
            """
            INSERT INTO evidence_events (
                id, scope_type, scope_id, memory_id, source_kind, source_ref, raw_content, created_at
            ) VALUES (?, 'agent', 'gauntlet_adversarial', 'gauntlet_adversarial_winner', 'manual', 'gauntlet://winner', 'Verified launch plan', '2026-04-02T00:00:00+00:00')
            """,
            (f"gauntlet_adv_ev_{index}",),
        )
    sync_fts(storage)

    query = SearchQuery(
        query="launch date",
        scope_type="agent",
        scope_id="gauntlet_adversarial",
        include_global=False,
        min_score=-10.0,
    )
    setattr(query, "intent", "correction_lookup")
    results = pipeline.search(query)
    winner = results[0].memory.id if results else None
    return GauntletResult(
        name="adversarial_lexical_bait",
        category="adversarial",
        passed=winner == "gauntlet_adversarial_winner",
        details={"selected_id": winner},
    )


def run_product_readiness_case(app) -> GauntletResult:
    app.put_memory(
        "Use the nickname Hali in replies.",
        type="semantic",
        scope_type="agent",
        scope_id="gauntlet_product",
        source_kind="manual",
        source_ref="gauntlet://product",
        subject="user_nickname",
        confidence=0.9,
        metadata={"is_winner": True},
    )
    spotlight = app.spotlight(
        "nickname",
        scope_type="agent",
        scope_id="gauntlet_product",
        limit=1,
        intent="user_override_active",
    )
    result_count = int(spotlight.get("result_count", 0))
    selected = spotlight.get("results", [{}])[0].get("selected_memory") if result_count else None
    return GauntletResult(
        name="product_runtime_spotlight_surface",
        category="product_readiness",
        passed=result_count == 1 and selected == "Use the nickname Hali in replies.",
        details={"result_count": result_count, "selected_memory": selected},
    )


def run_scope_isolation_case(manager, pipeline, storage) -> GauntletResult:
    from aegis_py.retrieval.models import SearchQuery
    from aegis_py.storage.models import Memory

    manager.store(
        Memory(
            id="gauntlet_scope_a",
            type="semantic",
            content="The admin key is ALPHA-123.",
            subject="admin.key",
            confidence=0.9,
            source_kind="manual",
            source_ref="gauntlet://scope-a",
            scope_type="agent",
            scope_id="tenant_alpha",
            metadata={"is_winner": True},
        )
    )
    manager.store(
        Memory(
            id="gauntlet_scope_b",
            type="semantic",
            content="The admin key is BRAVO-999.",
            subject="admin.key",
            confidence=0.9,
            source_kind="manual",
            source_ref="gauntlet://scope-b",
            scope_type="agent",
            scope_id="tenant_bravo",
            metadata={"is_winner": True},
        )
    )
    sync_fts(storage)

    query = SearchQuery(
        query="admin key",
        scope_type="agent",
        scope_id="tenant_alpha",
        include_global=False,
        min_score=-10.0,
    )
    results = pipeline.search(query)
    selected = results[0].memory.content if results else None
    passed = bool(selected and "ALPHA-123" in selected and "BRAVO-999" not in selected)
    return GauntletResult(
        name="scope_isolation_attack",
        category="adversarial",
        passed=passed,
        details={"selected_memory": selected},
    )


def run_recovery_case(app) -> GauntletResult:
    app.put_memory(
        "The staging endpoint is staging.internal.local.",
        type="semantic",
        scope_type="agent",
        scope_id="gauntlet_recovery",
        source_kind="manual",
        source_ref="gauntlet://recovery",
        subject="staging.endpoint",
        confidence=0.9,
        metadata={"is_winner": True},
    )
    app.storage.execute("DELETE FROM memories_fts")
    app.storage.execute(
        "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
    )
    spotlight = app.spotlight(
        "staging endpoint",
        scope_type="agent",
        scope_id="gauntlet_recovery",
        limit=1,
    )
    result_count = int(spotlight.get("result_count", 0))
    selected = spotlight.get("results", [{}])[0].get("selected_memory") if result_count else None
    return GauntletResult(
        name="recovery_after_rebuild",
        category="product_readiness",
        passed=result_count == 1 and selected == "The staging endpoint is staging.internal.local.",
        details={"result_count": result_count, "selected_memory": selected},
    )


def run_backup_restore_case(app, workspace_dir: Path) -> GauntletResult:
    app.put_memory(
        "Primary support contact is Linh.",
        type="semantic",
        scope_type="agent",
        scope_id="gauntlet_backup",
        source_kind="manual",
        source_ref="gauntlet://backup/original",
        subject="support.contact",
        confidence=0.9,
        metadata={"is_winner": True},
    )
    backup = app.create_backup(mode="snapshot", workspace_dir=str(workspace_dir))
    snapshot_path = backup["path"]

    app.put_memory(
        "Primary support contact is Minh.",
        type="semantic",
        scope_type="agent",
        scope_id="gauntlet_backup",
        source_kind="manual",
        source_ref="gauntlet://backup/drift",
        subject="support.contact",
        confidence=0.5,
    )
    preview = app.preview_restore(snapshot_path, scope_type="agent", scope_id="gauntlet_backup")
    restore = app.restore_backup(snapshot_path, scope_type="agent", scope_id="gauntlet_backup")
    spotlight = app.spotlight(
        "support contact",
        scope_type="agent",
        scope_id="gauntlet_backup",
        limit=3,
    )
    selected = spotlight.get("results", [{}])[0].get("selected_memory") if spotlight.get("result_count") else None
    return GauntletResult(
        name="operations_backup_restore_scope",
        category="product_readiness",
        passed=(
            preview.get("preview", {}).get("records", 0) >= 1
            and restore.get("restored_records", 0) >= 1
            and selected == "Primary support contact is Linh."
        ),
        details={
            "backup_path": snapshot_path,
            "preview_records": preview.get("preview", {}).get("records", 0),
            "restored_records": restore.get("restored_records", 0),
            "selected_memory": selected,
        },
    )


def run_rebuild_pressure_case(app) -> GauntletResult:
    for index in range(25):
        app.put_memory(
            f"Operational note {index} for rebuild pressure.",
            type="semantic",
            scope_type="agent",
            scope_id="gauntlet_rebuild",
            source_kind="manual",
            source_ref=f"gauntlet://rebuild/{index}",
            subject="ops.note",
            confidence=0.4,
        )
    app.put_memory(
        "Canonical rebuild checkpoint is GREEN.",
        type="semantic",
        scope_type="agent",
        scope_id="gauntlet_rebuild",
        source_kind="manual",
        source_ref="gauntlet://rebuild/canonical",
        subject="ops.checkpoint",
        confidence=0.95,
        metadata={"is_winner": True},
    )
    rebuild = app.rebuild()
    spotlight = app.spotlight(
        "rebuild checkpoint",
        scope_type="agent",
        scope_id="gauntlet_rebuild",
        limit=1,
        intent="correction_lookup",
    )
    selected = spotlight.get("results", [{}])[0].get("selected_memory") if spotlight.get("result_count") else None
    return GauntletResult(
        name="operations_rebuild_pressure",
        category="product_readiness",
        passed=bool(rebuild.get("rebuilt")) and selected == "Canonical rebuild checkpoint is GREEN.",
        details={
            "rebuilt": rebuild.get("rebuilt"),
            "same_subject_links_added": rebuild.get("same_subject_links_added"),
            "selected_memory": selected,
        },
    )


def run_ingest_pressure_case(app) -> GauntletResult:
    accepted = 0
    rejected = 0
    diagnostic_outcomes: dict[str, int] = {}
    blocked_reason_counts: dict[str, int] = {}
    for index in range(30):
        payload = {
            "content": f"Repeated ingest payload {index % 3} for admission pressure.",
            "type": "semantic",
            "scope_type": "agent",
            "scope_id": "gauntlet_ingest",
            "source_kind": "manual",
            "source_ref": f"gauntlet://ingest/{index}",
            "subject": "ingest.pressure",
            "confidence": 0.4 + (index % 3) * 0.1,
        }
        diagnostic = app.diagnose_ingest_attempt(**payload)
        diagnostic_outcome = str(diagnostic.get("outcome", "unknown"))
        diagnostic_outcomes[diagnostic_outcome] = diagnostic_outcomes.get(diagnostic_outcome, 0) + 1
        for reason in diagnostic.get("reasons", []):
            if isinstance(reason, str) and reason.startswith("blocked_"):
                blocked_reason_counts[reason] = blocked_reason_counts.get(reason, 0) + 1
        stored = app.put_memory(
            **payload,
        )
        if stored is None:
            rejected += 1
        else:
            accepted += 1
    app.put_memory(
        "Canonical ingest checkpoint is ACCEPTABLE.",
        type="semantic",
        scope_type="agent",
        scope_id="gauntlet_ingest",
        source_kind="manual",
        source_ref="gauntlet://ingest/canonical",
        subject="ingest.checkpoint",
        confidence=0.95,
        metadata={"is_winner": True},
    )
    spotlight = app.spotlight(
        "ingest checkpoint",
        scope_type="agent",
        scope_id="gauntlet_ingest",
        limit=1,
        intent="correction_lookup",
    )
    selected = spotlight.get("results", [{}])[0].get("selected_memory") if spotlight.get("result_count") else None
    passed = accepted > 0 and selected == "Canonical ingest checkpoint is ACCEPTABLE."
    return GauntletResult(
        name="ingest_pressure_admission_behavior",
        category="product_readiness",
        passed=passed,
        details={
            "accepted_writes": accepted,
            "rejected_or_noop_writes": rejected,
            "diagnostic_outcomes": diagnostic_outcomes,
            "blocked_reason_counts": blocked_reason_counts,
            "selected_memory": selected,
        },
    )


def write_artifact(repo_root: Path, results: list[GauntletResult]) -> Path:
    artifact_path = repo_root / ".planning" / "benchmarks" / "aegis_gauntlet_summary.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "benchmark": "aegis_gauntlet",
        "summary": {
            "scenario_count": len(results),
            "pass_rate": round(sum(1 for item in results if item.passed) / len(results), 3),
            "passed": all(item.passed for item in results),
        },
        "grouped_summary": build_grouped_summary(results),
        "scenarios": [
            {
                "name": item.name,
                "category": item.category,
                "passed": item.passed,
                "details": item.details,
            }
            for item in results
        ],
    }
    artifact_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return artifact_path


def main() -> int:
    repo_root = resolve_repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from aegis_py.app import AegisApp
    from aegis_py.memory.core import MemoryManager
    from aegis_py.retrieval.search import SearchPipeline
    from aegis_py.storage.manager import StorageManager

    with tempfile.TemporaryDirectory(prefix="aegis_gauntlet_") as tmp:
        db_path = str(Path(tmp) / "aegis_gauntlet.db")
        storage = StorageManager(db_path)
        manager = MemoryManager(storage)
        pipeline = SearchPipeline(storage)
        app = AegisApp(db_path)
        try:
            results = [
                run_core_truth_case(manager, pipeline, storage),
                run_scale_case(manager, pipeline, storage),
                run_adversarial_case(manager, pipeline, storage),
                run_scope_isolation_case(manager, pipeline, storage),
                run_product_readiness_case(app),
                run_recovery_case(app),
                run_backup_restore_case(app, Path(tmp)),
                run_rebuild_pressure_case(app),
                run_ingest_pressure_case(app),
            ]
        finally:
            app.close()
            storage.close()

    print("## Aegis Gauntlet")
    print()
    for item in results:
        print(f"- {item.name} [{item.category}]: {'PASS' if item.passed else 'FAIL'}")
        print(json.dumps(item.details, indent=2, ensure_ascii=False))
    print()
    artifact_path = write_artifact(repo_root, results)
    print(f"[Artifact] Wrote {artifact_path}")
    return 0 if all(item.passed for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
