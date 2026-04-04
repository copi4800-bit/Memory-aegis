import json
from pathlib import Path

from truthkeep import TruthKeep
from truthkeep import cli as truthkeep_cli
from truthkeep.install_check import build_install_readiness_report


def test_truthkeep_facade_auto_uses_truthkeep_default_db_name(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    facade = TruthKeep.auto()
    try:
        assert facade._app.db_path.endswith("truthkeep_v10.db")
    finally:
        facade._app.close()


def test_truthkeep_cli_module_exports_and_mcp_hint(capsys):
    assert truthkeep_cli.main(["--db-path", ":memory:", "mcp"]) == 0
    out = capsys.readouterr().out
    assert "truthkeep-mcp" in out
    assert "aegis-mcp" in out


def test_truthkeep_cli_field_snapshot_json_contract(capsys, tmp_path):
    db_path = tmp_path / "phase126.db"
    assert truthkeep_cli.main(["--db-path", str(db_path), "remember", "Bao owns the release checklist."]) == 0
    capsys.readouterr()
    assert truthkeep_cli.main(["--db-path", str(db_path), "field-snapshot"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert "state_coverage" in payload
    assert "energy" in payload


def test_truthkeep_install_check_report_has_workspace_and_readiness(tmp_path):
    report = build_install_readiness_report(tmp_path)
    assert report["workspace_dir"] == str(tmp_path)
    assert report["readiness"] in {"BLOCKED", "RUNTIME_READY_PLUGIN_INCOMPLETE", "READY"}
