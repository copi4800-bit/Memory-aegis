from types import SimpleNamespace

from aegis_py.memory.correction import resolve_correction_target


def test_resolve_correction_target_keeps_default_scope_when_nothing_matches():
    calls = []

    def search_fn(query, *, scope_id, scope_type, limit, fallback_to_or):
        calls.append((query, scope_type, scope_id, limit, fallback_to_or))
        return []

    target = resolve_correction_target(
        "No existing correction match",
        default_scope_type="agent",
        default_scope_id="default",
        scope_candidates=[("agent", "default"), ("session", "fallback")],
        search_fn=search_fn,
    )

    assert target.scope_type == "agent"
    assert target.scope_id == "default"
    assert target.subject is None
    assert target.old_memory_id is None
    assert len(calls) == 2


def test_resolve_correction_target_uses_first_matching_scope():
    matching_result = SimpleNamespace(memory=SimpleNamespace(id="old_1", subject="favorite.color"))

    def search_fn(query, *, scope_id, scope_type, limit, fallback_to_or):
        if (scope_type, scope_id) == ("agent", "preferred"):
            return [matching_result]
        return []

    target = resolve_correction_target(
        "Actually the favorite color is red",
        default_scope_type="agent",
        default_scope_id="default",
        scope_candidates=[("agent", "preferred"), ("session", "fallback")],
        search_fn=search_fn,
    )

    assert target.scope_type == "agent"
    assert target.scope_id == "preferred"
    assert target.subject == "favorite.color"
    assert target.old_memory_id == "old_1"
