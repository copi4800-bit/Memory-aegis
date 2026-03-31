from aegis_py.app import AegisApp


def test_acceptance_remember_and_recall_round_trip(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "acceptance-memory.db"))

    remembered = app.memory_remember("The deployment checklist owner is Linh.")
    recalled = app.memory_recall("Who owns the deployment checklist?")
    payload = app.search_payload(
        "deployment checklist owner",
        scope_type="agent",
        scope_id="default",
        limit=5,
    )

    assert "remembered" in remembered.lower()
    assert "deployment checklist owner is linh" in recalled.lower()
    assert len(payload) >= 1
    assert payload[0]["memory"]["scope_type"] == "agent"
    assert payload[0]["memory"]["scope_id"] == "default"
    assert payload[0]["memory"]["source_kind"] == "conversation"

    app.close()


def test_acceptance_correct_and_forget_keep_consumer_surface_working(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "acceptance-correct-forget.db"))

    app.memory_remember("The office Wi-Fi password is alpha.")
    corrected = app.memory_correct("The office Wi-Fi password is beta.")
    recalled = app.memory_recall("What is the office Wi-Fi password?")
    forgotten = app.memory_forget("office Wi-Fi password")
    after_forget = app.memory_recall("What is the office Wi-Fi password?")

    assert "updated" in corrected.lower() or "corrected" in corrected.lower() or "remembered" in corrected.lower()
    assert "beta" in recalled.lower()
    assert "forgot" in forgotten.lower() or "removed" in forgotten.lower()
    assert "don't recall" in after_forget.lower()

    app.close()
