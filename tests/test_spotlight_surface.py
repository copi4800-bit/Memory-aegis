from aegis_py.spotlight_surface import (
    build_spotlight_payload,
    build_spotlight_response,
    render_spotlight_text,
)
from aegis_py.surface import serialize_search_result
from aegis_py.mcp.server import AegisMCPServer
import json


def test_spotlight_surface_formats_truth_and_why_not(runtime_harness):
    from aegis_py.retrieval.models import SearchQuery
    from aegis_py.storage.models import Memory

    old_fact = Memory(
        id="spot_old",
        type="semantic",
        content="The maintenance window is Friday.",
        subject="maintenance_window",
        confidence=0.9,
        source_kind="manual",
        source_ref="test://old",
        scope_type="agent",
        scope_id="spotlight_test",
    )
    current_fact = Memory(
        id="spot_new",
        type="semantic",
        content="Correction: the maintenance window moved to Saturday.",
        subject="maintenance_window",
        confidence=1.0,
        source_kind="manual",
        source_ref="test://new",
        scope_type="agent",
        scope_id="spotlight_test",
        metadata={"is_winner": True, "is_correction": True, "corrected_from": ["spot_old"]},
    )

    runtime_harness.store(old_fact)
    runtime_harness.store(current_fact)
    runtime_harness.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = 'spot_old'")
    runtime_harness.sync_fts()

    query = SearchQuery(
        query="maintenance window",
        scope_type="agent",
        scope_id="spotlight_test",
        include_global=False,
        min_score=-10.0,
    )
    setattr(query, "intent", "correction_lookup")
    results = runtime_harness.pipeline.search(query)

    assert results
    payload = build_spotlight_payload(results[0])
    rendered = render_spotlight_text(results[0])
    serialized = serialize_search_result(results[0])

    assert payload["selected_memory"] == serialized["memory"]["content"]
    assert payload["truth_state"]["governance_status"] == "active"
    assert payload["truth_state"]["truth_role"] == "winner"
    assert any(item["id"] == "spot_old" for item in payload["why_not"])
    assert "[Selected Result]" in rendered
    assert "[Why Not]" in rendered

    response = build_spotlight_response(
        "maintenance window",
        results,
        scope_type="agent",
        scope_id="spotlight_test",
    )
    assert response["result_count"] == 1
    assert response["results"][0]["truth_state"]["truth_role"] == "winner"
    assert "[Selected Result]" in response["spotlight_text"]


def test_memory_spotlight_tool_returns_runtime_response(tmp_path):
    from aegis_py.storage.models import Memory

    db_path = tmp_path / "spotlight_tool.db"
    server = AegisMCPServer(db_path=str(db_path))
    try:
        old_stored = server.app.put_memory(
            "The deployment window is Monday.",
            type="semantic",
            scope_type="agent",
            scope_id="tool_scope",
            source_kind="manual",
            source_ref="test://tool-old",
            subject="deployment_window",
            confidence=0.9,
        )
        current_stored = server.app.put_memory(
            "Correction: the deployment window moved to Tuesday.",
            type="semantic",
            scope_type="agent",
            scope_id="tool_scope",
            source_kind="manual",
            source_ref="test://tool-new",
            subject="deployment_window",
            confidence=1.0,
            metadata={"is_winner": True, "is_correction": True},
        )
        assert old_stored is not None
        assert current_stored is not None
        server.app.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_stored.id,))
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        raw = server.run_tool(
            "memory_spotlight",
            {
                "query": "deployment window",
                "scope_type": "agent",
                "scope_id": "tool_scope",
                "include_global": False,
            },
        )
        payload = json.loads(raw)

        assert payload["result_count"] == 1
        assert payload["results"][0]["truth_state"]["governance_status"] == "active"
        assert "Correction: the deployment window moved to Tuesday." == payload["results"][0]["selected_memory"]
        assert "[Selected Result]" in payload["spotlight_text"]
    finally:
        server.close()


def test_memory_spotlight_tool_accepts_correction_intent(tmp_path):
    db_path = tmp_path / "spotlight_tool_intent.db"
    server = AegisMCPServer(db_path=str(db_path))
    try:
        old_stored = server.app.put_memory(
            "The release gate opens on Monday.",
            type="semantic",
            scope_type="agent",
            scope_id="intent_scope",
            source_kind="manual",
            source_ref="test://intent-old",
            subject="release_gate",
            confidence=0.9,
        )
        current_stored = server.app.put_memory(
            "Correction: the release gate opens on Wednesday.",
            type="semantic",
            scope_type="agent",
            scope_id="intent_scope",
            source_kind="manual",
            source_ref="test://intent-new",
            subject="release_gate",
            confidence=1.0,
            metadata={"is_winner": True, "is_correction": True},
        )
        assert old_stored is not None
        assert current_stored is not None
        server.app.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_stored.id,))
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        raw = server.run_tool(
            "memory_spotlight",
            {
                "query": "release gate",
                "scope_type": "agent",
                "scope_id": "intent_scope",
                "include_global": False,
                "intent": "correction_lookup",
            },
        )
        payload = json.loads(raw)

        assert payload["result_count"] == 1
        assert payload["results"][0]["truth_state"]["truth_role"] == "winner"
        assert payload["results"][0]["truth_state"]["governance_status"] == "active"
    finally:
        server.close()
