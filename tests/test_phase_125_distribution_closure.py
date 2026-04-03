import json
import io

from aegis_py import cli
from aegis_py.app import AegisApp
from scripts import prove_it


def test_truthkeep_cli_remember_and_status_work(tmp_path, capsys):
    db_path = tmp_path / "phase125_cli.db"
    assert cli.main(["--db-path", str(db_path), "remember", "The release owner is Bao."]) == 0
    remember_out = capsys.readouterr().out
    assert remember_out.strip()

    assert cli.main(["--db-path", str(db_path), "status"]) == 0
    status_out = capsys.readouterr().out
    assert "State:" in status_out


def test_truthkeep_cli_field_snapshot_emits_json(tmp_path, capsys):
    db_path = tmp_path / "phase125_snapshot.db"
    assert cli.main(["--db-path", str(db_path), "remember", "Bao prefers black coffee."]) == 0
    capsys.readouterr()
    assert cli.main(["--db-path", str(db_path), "field-snapshot"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert "state_coverage" in payload
    assert "energy" in payload


def test_prove_it_summary_passes_and_confirms_correctness_behavior(tmp_path):
    summary = prove_it.build_proof_summary(db_path=str(tmp_path / "phase125_proof.db"))
    assert summary["passed"] is True
    assert summary["metrics"]["correction_top1_preserved"] is True
    assert summary["metrics"]["why_not_available"] is True


def test_cli_emit_output_survives_unicode_on_narrow_console():
    class NarrowConsole(io.StringIO):
        encoding = "cp1252"

        def write(self, text):
            text.encode(self.encoding)
            return super().write(text)

    class FallbackConsole(NarrowConsole):
        @property
        def buffer(self):
            return self

        def write(self, payload):
            if isinstance(payload, bytes):
                return super().write(payload.decode(self.encoding, errors="replace"))
            return super().write(payload)

        def flush(self):
            return None

    stream = FallbackConsole()
    cli.emit_output("đã ghi nhận thông tin này ạ.", stream=stream)
    assert "?" in stream.getvalue() or "đã" in stream.getvalue()


def test_memory_recall_does_not_leak_trust_prefix_token(tmp_path):
    app = AegisApp(str(tmp_path / "phase125_recall.db"))
    try:
        app.put_memory(
            "The release owner is Bao.",
            type="semantic",
            scope_type="agent",
            scope_id="default",
            source_kind="manual",
            source_ref="test://phase125-recall",
            subject="release.owner",
            confidence=0.95,
        )
        text = app.memory_recall("release owner bao", scope_type="agent", scope_id="default")
        assert "trust_prefix_uncertain" not in text
        assert "Bao" in text
    finally:
        app.close()
