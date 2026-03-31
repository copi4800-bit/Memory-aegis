import pytest
import subprocess
import sys

from aegis_py.app import AegisApp
from aegis_py.install_check import build_install_readiness_report
from aegis_py.mcp.server import AegisMCPServer

@pytest.fixture
def app(tmp_path):
    db_file = tmp_path / "user_surface.db"
    return AegisApp(db_path=str(db_file))

def test_simple_remember_and_recall(app):
    # 1. Remember
    resp = app.memory_remember("My favorite color is blue.")
    assert "ghi nhớ" in resp.lower()
    
    # 2. Recall
    resp = app.memory_recall("What is my favorite color?")
    assert "favorite color is blue" in resp.lower()

    stored = app.storage.fetch_one(
        "SELECT scope_type, scope_id, source_kind, source_ref FROM memories WHERE status = 'active' LIMIT 1"
    )
    assert stored is not None
    assert stored["scope_type"] == "agent"
    assert stored["scope_id"] == "default"
    assert stored["source_kind"] == "conversation"
    assert stored["source_ref"] == "consumer://default"

def test_simple_correct(app):
    # 1. Remember old fact
    app.memory_remember("My office is in Room 101.")
    
    # 2. Correct fact
    resp = app.memory_correct("Actually, my office is in Room 202.")
    assert "cập nhật" in resp.lower()
    
    # 3. Recall - should only show new fact
    resp = app.memory_recall("Where is my office?")
    assert "Room 202" in resp
    assert "Room 101" not in resp

def test_simple_forget(app):
    # 1. Remember
    app.memory_remember("The secret code is 1234.")
    
    # 2. Forget
    resp = app.memory_forget("secret code")
    assert "xóa" in resp.lower()
    
    # 3. Recall - should not find it
    resp = app.memory_recall("secret code")
    assert "không tìm thấy" in resp.lower()

    archived = app.storage.fetch_one(
        "SELECT metadata_json FROM memories WHERE status = 'archived' LIMIT 1"
    )
    assert archived is not None
    assert "forgotten_by_user_action" in archived["metadata_json"]


def test_simple_user_surface_via_mcp(tmp_path):
    server = AegisMCPServer(db_path=str(tmp_path / "user_surface_mcp.db"))

    assert "ghi nhớ" in server.memory_remember("I love chocolate cake.").lower()
    assert "chocolate cake" in server.memory_recall("What do I love?").lower()
    assert "cập nhật" in server.memory_correct("Actually, I prefer strawberry cheesecake.").lower()
    recall_after_correct = server.memory_recall("What dessert do I prefer?")
    assert "strawberry cheesecake" in recall_after_correct.lower()
    assert "xóa" in server.memory_forget("strawberry cheesecake").lower()
    assert "không tìm thấy" in server.memory_recall("strawberry cheesecake").lower()

    server.close()


def test_default_profile_uses_consumer_scope(app):
    app.memory_remember("I prefer direct answers.")

    profile = app.render_profile()

    assert "## Memory Profile: default (agent)" in profile
    assert "direct answers" in profile.lower()


def test_simple_user_surface_via_cli_supports_positional_arguments(tmp_path):
    db_path = tmp_path / "user_surface_cli.db"
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    remembered = subprocess.run(
        [*cli, "remember", "I love chocolate cake."],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "ghi nhớ" in remembered.stdout.lower()

    recalled = subprocess.run(
        [*cli, "recall", "What do I love?"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "chocolate cake" in recalled.stdout.lower()

    corrected = subprocess.run(
        [*cli, "correct", "Actually, I prefer strawberry cheesecake."],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "cập nhật" in corrected.stdout.lower()

    forgotten = subprocess.run(
        [*cli, "forget", "strawberry cheesecake"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "xóa" in forgotten.stdout.lower()


def test_onboarding_reports_ready_for_fresh_runtime(app):
    report = app.onboarding()

    assert report["backend"] == "python"
    assert report["readiness"] == "READY"
    assert report["health_state"] == "HEALTHY"
    assert report["checks"]["database"]["ok"] is True
    assert report["checks"]["write_test"]["ok"] is True
    assert report["checks"]["recall_test"]["ok"] is True
    assert "Aegis is ready" in report["summary"]


def test_onboarding_reports_degraded_but_usable_local_runtime(app):
    app.set_scope_policy(
        "project",
        "P1",
        sync_policy="sync_eligible",
        sync_state="pending_sync",
    )

    report = app.onboarding()

    assert report["readiness"] == "READY"
    assert report["health_state"] == "DEGRADED_SYNC"
    assert any("usable locally" in entry for entry in report["guidance"])


def test_onboarding_cli_prints_plain_language_summary(tmp_path):
    db_path = tmp_path / "user_surface_onboarding.db"
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    completed = subprocess.run(
        [*cli, "onboarding", "--workspace-dir", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Aegis Setup Check" in completed.stdout
    assert "Readiness: READY" in completed.stdout


def test_onboarding_cli_supports_json_payload(tmp_path):
    db_path = tmp_path / "user_surface_onboarding_json.db"
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    completed = subprocess.run(
        [*cli, "onboarding", "--workspace-dir", str(tmp_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = __import__("json").loads(completed.stdout)
    assert payload["backend"] == "python"
    assert payload["readiness"] == "READY"


def test_aegis_setup_prints_first_value_next_steps(tmp_path):
    completed = subprocess.run(
        [sys.executable, "/home/hali/.openclaw/extensions/memory-aegis-v7/bin/aegis-setup"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "First value next steps:" in completed.stdout
    assert '-m aegis_py.cli remember "My favorite drink is jasmine tea."' in completed.stdout
    assert '-m aegis_py.cli recall "What is my favorite drink?"' in completed.stdout
    assert "-m aegis_py.cli status" in completed.stdout


def test_demo_first_memory_script_prints_short_success_story():
    completed = subprocess.run(
        [sys.executable, "/home/hali/.openclaw/extensions/memory-aegis-v7/scripts/demo_first_memory.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "## Aegis Demo: First Memory" in completed.stdout
    assert "[1] Setup" in completed.stdout
    assert "[2] Remember" in completed.stdout
    assert "[3] Recall" in completed.stdout
    assert "[4] Status" in completed.stdout
    assert "Health: HEALTHY" in completed.stdout
    assert "My favorite drink is jasmine tea." in completed.stdout
    assert "Active memories: 1" in completed.stdout
    assert "This demo proves the shortest local-first success path" in completed.stdout


def test_demo_integration_boundary_script_prints_service_boundary_story():
    completed = subprocess.run(
        [sys.executable, "/home/hali/.openclaw/extensions/memory-aegis-v7/scripts/demo_integration_boundary.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "## Aegis Demo: Integration Boundary" in completed.stdout
    assert "[1] Service Info" in completed.stdout
    assert "[2] Startup Probe" in completed.stdout
    assert "[3] Setup Tool" in completed.stdout
    assert "[4] Remember Tool" in completed.stdout
    assert "[5] Recall Tool" in completed.stdout
    assert "Deployment: local_sidecar_process" in completed.stdout
    assert "Transport: mcp_tool_process" in completed.stdout
    assert "Service state: READY" in completed.stdout
    assert "Health state: HEALTHY" in completed.stdout
    assert "navy blue" in completed.stdout
    assert "This demo shows the thin-host path" in completed.stdout


def test_demo_grounded_recall_script_prints_grounding_story():
    completed = subprocess.run(
        [sys.executable, "/home/hali/.openclaw/extensions/memory-aegis-v7/scripts/demo_grounded_recall.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "## Aegis Demo: Grounded Recall" in completed.stdout
    assert "[1] Provenance" in completed.stdout
    assert "[2] Trust" in completed.stdout
    assert "[3] Ranking Reasons" in completed.stdout
    assert "[4] Context Pack Evidence" in completed.stdout
    assert "[manual] docs/release-checklist.md" in completed.stdout
    assert "Trust state: strong" in completed.stdout
    assert "fts_match" in completed.stdout
    assert "scope_exact_match" in completed.stdout
    assert "Source: manual -> docs/release-checklist.md" in completed.stdout
    assert "This demo shows why the recall is grounded" in completed.stdout


def test_install_readiness_report_detects_runtime_and_plugin_prerequisites(tmp_path):
    report = build_install_readiness_report(tmp_path)

    assert report["checks"]["python"]["ok"] is True
    assert report["checks"]["sqlite_fts5"]["ok"] is True
    assert report["checks"]["node"]["id"] == "node"
    assert report["checks"]["npm"]["id"] == "npm"
    assert report["readiness"] in {"READY", "RUNTIME_READY_PLUGIN_INCOMPLETE"}
    python_guidance = report["checks"]["python"]["guidance"]
    assert python_guidance is None or "python3 -m venv .venv" in python_guidance


def test_install_readiness_report_distinguishes_plugin_gap(monkeypatch, tmp_path):
    import aegis_py.install_check as install_check

    monkeypatch.setattr(
        install_check,
        "check_command",
        lambda name, required_for: {
            "id": name,
            "ok": False,
            "required": False,
            "version": None,
            "summary": f"{name} not found",
            "guidance": f"Install {name} if you want the OpenClaw plugin/bootstrap path ({required_for}).",
        },
    )

    report = install_check.build_install_readiness_report(tmp_path)

    assert report["checks"]["python"]["ok"] is True
    assert report["checks"]["sqlite_fts5"]["ok"] is True
    assert report["readiness"] == "RUNTIME_READY_PLUGIN_INCOMPLETE"
    assert any("OpenClaw plugin/bootstrap path" in entry for entry in report["guidance"])


def test_status_cli_prints_plain_language_summary_by_default(tmp_path):
    db_path = tmp_path / "user_surface_status.db"
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    subprocess.run(
        [*cli, "remember", "I prefer concise answers."],
        check=True,
        capture_output=True,
        text=True,
    )

    completed = subprocess.run(
        [*cli, "status"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Aegis Status" in completed.stdout
    assert "Aegis is ready and local memory is working normally." in completed.stdout
    assert "Active memories: 1" in completed.stdout


def test_status_cli_supports_explicit_json_output(tmp_path):
    db_path = tmp_path / "user_surface_status_json.db"
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    completed = subprocess.run(
        [*cli, "status", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = __import__("json").loads(completed.stdout)
    assert payload["health_state"] == "HEALTHY"


def test_doctor_cli_prints_plain_language_summary(tmp_path):
    db_path = tmp_path / "user_surface_doctor.db"
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    completed = subprocess.run(
        [*cli, "doctor", "--workspace-dir", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Aegis Doctor" in completed.stdout
    assert "Aegis memory is operating normally." in completed.stdout


def test_doctor_cli_supports_explicit_json_output(tmp_path):
    db_path = tmp_path / "user_surface_doctor_json.db"
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    completed = subprocess.run(
        [*cli, "doctor", "--workspace-dir", str(tmp_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = __import__("json").loads(completed.stdout)
    assert payload["health_state"] == "HEALTHY"


def test_storage_footprint_cli_reports_plain_language_summary(tmp_path):
    db_path = tmp_path / "user_surface_storage.db"
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    completed = subprocess.run(
        [*cli, "storage-footprint"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Aegis Storage" in completed.stdout
    assert "Allocated storage:" in completed.stdout
    assert "Archived-memory retention:" in completed.stdout


def test_storage_compact_cli_supports_json_output(tmp_path):
    db_path = tmp_path / "user_surface_storage_compact.db"
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    completed = subprocess.run(
        [*cli, "storage-compact", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = __import__("json").loads(completed.stdout)
    assert "before" in payload
    assert "after" in payload
    assert "deleted" in payload


def test_backup_cli_prints_plain_language_recovery_summary(tmp_path):
    db_path = tmp_path / "user_surface_backup.db"
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    subprocess.run(
        [*cli, "remember", "Recovery summary test memory."],
        check=True,
        capture_output=True,
        text=True,
    )

    created = subprocess.run(
        [*cli, "backup-upload", "--workspace-dir", str(workspace_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Created a snapshot backup successfully." in created.stdout

    backup_dir = workspace_dir / ".aegis_py" / "backups"
    snapshot_path = next(backup_dir.glob("*.db"))
    preview = subprocess.run(
        [*cli, "backup-preview", "--snapshot-path", str(snapshot_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Aegis Restore Preview" in preview.stdout
    assert "This is a dry run for all local memory." in preview.stdout


def test_backup_cli_supports_explicit_json_output(tmp_path):
    db_path = tmp_path / "user_surface_backup_json.db"
    workspace_dir = tmp_path / "workspace-json"
    workspace_dir.mkdir()
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    created = subprocess.run(
        [*cli, "backup-upload", "--workspace-dir", str(workspace_dir), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = __import__("json").loads(created.stdout)
    assert payload["mode"] == "snapshot"
