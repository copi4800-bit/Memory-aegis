import json
import sqlite3
import unittest
from pathlib import Path

from aegis_py.app import AegisApp
from aegis_py.mcp.server import AegisMCPServer
from aegis_py.main import get_memory_profile, get_service_info, get_startup_probe, put_memory, search_memories
from aegis_py.surface import ADVANCED_OPERATIONS, DEFAULT_OPERATIONS
from aegis_py.tool_registry import TOOL_REGISTRY, registry_tool_names


class AppSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.db_path = "/tmp/aegis-app-surface.db"
        Path(self.db_path).unlink(missing_ok=True)
        self.app = AegisApp(db_path=self.db_path)
        self.server = AegisMCPServer(db_path=self.db_path)

    def tearDown(self):
        self.server.close()
        self.app.close()
        Path(self.db_path).unlink(missing_ok=True)

    def test_app_status_and_export_surfaces(self):
        self.app.put_memory(
            "Procedural deployment note.",
            type="procedural",
            scope_type="project",
            scope_id="P1",
        )
        status = self.app.status()
        self.assertEqual(status["db_path"], self.db_path)
        self.assertEqual(status["counts"]["active"], 1)
        self.assertEqual(status["health"]["state"], "HEALTHY")
        self.assertTrue(status["health"]["capabilities"]["local_store"])

        exported = self.app.export_memories("json")
        payload = json.loads(exported)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["type"], "procedural")

    def test_mcp_server_uses_app_contract(self):
        stored = self.server.memory_store(
            "semantic",
            "Aegis uses SQLite FTS5.",
            "technical.storage",
            scope_type="project",
            scope_id="aegis-v4",
            source_kind="manual",
            source_ref="spec",
        )
        self.assertIn("Stored semantic memory", stored)

        searched = self.server.memory_search("SQLite", scope_type="project", scope_id="aegis-v4")
        payload = json.loads(searched)
        self.assertEqual(payload[0]["memory"]["scope_id"], "aegis-v4")
        self.assertIn("reason", payload[0])
        self.assertIn("reasons", payload[0])
        self.assertIn("provenance", payload[0])

        status = json.loads(self.server.memory_status())
        self.assertEqual(status["counts"]["active"], 1)
        self.assertEqual(status["health_state"], "HEALTHY")

        stats_alias = json.loads(self.server.memory_stats())
        self.assertEqual(stats_alias["counts"]["active"], 1)
        self.assertEqual(stats_alias["health_state"], "HEALTHY")

    def test_mcp_search_fast_mode_returns_bounded_payload(self):
        self.server.memory_store(
            "semantic",
            "Aegis keeps a local-first retrieval contract.",
            "technical.retrieval",
            scope_type="project",
            scope_id="FAST1",
            source_kind="manual",
            source_ref="spec#fast",
        )

        searched = self.server.memory_search(
            "local-first",
            scope_type="project",
            scope_id="FAST1",
            retrieval_mode="fast",
        )
        payload = json.loads(searched)

        self.assertEqual(payload[0]["result_mode"], "fast")
        self.assertEqual(payload[0]["memory"]["scope_id"], "FAST1")
        self.assertEqual(payload[0]["conflict_status"], "none")
        self.assertNotIn("trust_state", payload[0])
        self.assertNotIn("trust_reason", payload[0])
        self.assertNotIn("reasons", payload[0])
        self.assertNotIn("retrieval_stage", payload[0])

    def test_main_module_functions_work_without_fastmcp(self):
        from aegis_py import main as main_module

        if main_module._app is not None:
            main_module._app.close()
        main_module._app = AegisApp(db_path=self.db_path)

        stored = put_memory("Remember KRAKEN.", scope_id="P1", session_id="S1")
        self.assertIn("Memory stored:", stored)

        searched = search_memories("KRAKEN", "P1")
        self.assertIn("KRAKEN", searched)

        profile = get_memory_profile("P1")
        self.assertIn("Memory Profile", profile)

        main_module._app.close()
        main_module._app = None

    def test_main_module_exposes_service_descriptor_and_startup_probe(self):
        from aegis_py import main as main_module

        if main_module._app is not None:
            main_module._app.close()
        main_module._app = AegisApp(db_path=self.db_path)

        service_info = get_service_info()
        startup_probe = get_startup_probe()

        self.assertEqual(service_info["backend"], "python")
        self.assertEqual(service_info["service"]["deployment_model"], "local_sidecar_process")
        self.assertEqual(service_info["service"]["preferred_transport"], "mcp_tool_process")
        self.assertIn("--service-info", service_info["startup_contract"]["service_info_command"])
        self.assertTrue(startup_probe["ready"])
        self.assertIn(startup_probe["health_state"], {"HEALTHY", "DEGRADED_SYNC"})

        main_module._app.close()
        main_module._app = None

    def test_main_module_handles_filtered_ingest_without_crashing(self):
        from aegis_py import main as main_module

        if main_module._app is not None:
            main_module._app.close()
        main_module._app = AegisApp(db_path=self.db_path)

        stored = put_memory("ok", scope_id="P1")
        self.assertEqual(stored, "No memory stored.")

        main_module._app.close()
        main_module._app = None

    def test_contributor_docs_reference_active_validation_and_speckit_layout(self):
        readme = Path("/home/hali/.openclaw/extensions/memory-aegis-v7/README.md").read_text(encoding="utf-8")
        plan = Path(
            "/home/hali/.openclaw/extensions/memory-aegis-v7/specs/002-benchmark-release-hardening/plan.md"
        ).read_text(encoding="utf-8")
        python_engine_plan = Path(
            "/home/hali/.openclaw/extensions/memory-aegis-v7/specs/005-python-only-engine/plan.md"
        ).read_text(encoding="utf-8")

        self.assertIn("PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests", readme)
        self.assertIn(".specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks", readme)
        self.assertIn("specs/046-consumer-ready-checklist/plan.md", readme)
        self.assertIn("Python-first contributor scripts", python_engine_plan)
        self.assertIn("## Validation Closeout", plan)
        self.assertIn("51 passed in", plan)

    def test_health_surface_reports_degraded_sync_without_blocking_local_runtime(self):
        self.app.set_scope_policy(
            "project",
            "P1",
            sync_policy="sync_eligible",
            sync_state="sync_error",
        )

        self.app.put_memory(
            "Local-first write should still succeed under degraded sync.",
            type="semantic",
            scope_type="project",
            scope_id="P1",
        )

        status = self.app.status()
        doctor = self.app.doctor()

        self.assertEqual(status["health"]["state"], "DEGRADED_SYNC")
        self.assertFalse(status["health"]["capabilities"]["optional_sync"])
        self.assertTrue(status["health"]["capabilities"]["local_store"])
        self.assertEqual(doctor["health_state"], "DEGRADED_SYNC")
        self.assertIn("sync_degraded", doctor["issues"])

    def test_degraded_sync_preserves_local_read_and_write_operations(self):
        self.app.set_scope_policy(
            "project",
            "P1",
            sync_policy="sync_eligible",
            sync_state="pending_sync",
        )

        stored = self.app.put_memory(
            "Offline-first search should still work while sync is degraded.",
            type="semantic",
            scope_type="project",
            scope_id="P1",
        )

        results = self.app.search_payload("offline-first", scope_type="project", scope_id="P1")
        status = self.app.status()
        doctor = self.app.doctor()

        self.assertIsNotNone(stored)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["memory"]["scope_id"], "P1")
        self.assertEqual(status["health"]["state"], "DEGRADED_SYNC")
        self.assertTrue(status["health"]["capabilities"]["local_search"])
        self.assertTrue(doctor["health"]["capabilities"]["local_store"])
        self.assertTrue(doctor["health"]["capabilities"]["local_search"])
        self.assertIn("sync_degraded", doctor["issues"])

    def test_search_payload_defaults_to_explain_and_fast_mode_stays_minimal(self):
        self.app.put_memory(
            "Explain mode should preserve ranking rationale while fast mode stays compact.",
            type="semantic",
            scope_type="project",
            scope_id="PFAST",
            source_kind="manual",
            source_ref="spec#payload",
        )

        explain_payload = self.app.search_payload(
            "ranking rationale",
            scope_type="project",
            scope_id="PFAST",
        )
        fast_payload = self.app.search_payload(
            "ranking rationale",
            scope_type="project",
            scope_id="PFAST",
            retrieval_mode="fast",
        )

        self.assertEqual(explain_payload[0]["result_mode"], "explain")
        self.assertIn("trust_state", explain_payload[0])
        self.assertIn("trust_reason", explain_payload[0])
        self.assertIn("reasons", explain_payload[0])
        self.assertIn("retrieval_stage", explain_payload[0])

        self.assertEqual(fast_payload[0]["result_mode"], "fast")
        self.assertEqual(fast_payload[0]["memory"]["scope_id"], "PFAST")
        self.assertNotIn("trust_state", fast_payload[0])
        self.assertNotIn("trust_reason", fast_payload[0])
        self.assertNotIn("reasons", fast_payload[0])
        self.assertNotIn("retrieval_stage", fast_payload[0])

    def test_health_surface_reports_broken_when_local_storage_fails(self):
        def broken_fetch_one(*_args, **_kwargs):
            raise sqlite3.OperationalError("database is unavailable")

        self.app.storage.fetch_one = broken_fetch_one  # type: ignore[method-assign]
        self.app.storage.list_scope_policies = broken_fetch_one  # type: ignore[method-assign]
        self.server.app.storage.fetch_one = broken_fetch_one  # type: ignore[method-assign]
        self.server.app.storage.list_scope_policies = broken_fetch_one  # type: ignore[method-assign]

        status = self.app.status()
        doctor = self.app.doctor()
        server_status = json.loads(self.server.memory_status())

        self.assertEqual(status["health"]["state"], "BROKEN")
        self.assertFalse(status["health"]["capabilities"]["local_store"])
        self.assertEqual(doctor["health_state"], "BROKEN")
        self.assertIn("local_storage_unavailable", doctor["issues"])
        self.assertEqual(server_status["health_state"], "BROKEN")

    def test_public_surface_declares_bounded_health_contract(self):
        payload = self.app.public_surface()

        self.assertIn("health_contract", payload)
        self.assertIn("consumer_contract", payload)
        self.assertIn("service_boundary", payload)
        self.assertEqual(
            payload["engine"]["health_states"],
            ["HEALTHY", "DEGRADED_SYNC", "BROKEN"],
        )
        self.assertIn("optional_sync", payload["health_contract"]["capabilities"])
        self.assertEqual(
            payload["consumer_contract"]["default_operations"],
            DEFAULT_OPERATIONS,
        )
        self.assertEqual(payload["consumer_contract"]["default_scope"]["scope_type"], "agent")
        self.assertEqual(payload["consumer_contract"]["default_scope"]["scope_id"], "default")
        self.assertEqual(payload["consumer_contract"]["default_provenance"]["source_kind"], "conversation")
        self.assertEqual(payload["consumer_contract"]["guided_hygiene"]["ordinary_use"], "background_or_triggered")
        self.assertEqual(payload["service_boundary"]["deployment_model"], "local_sidecar_process")
        self.assertEqual(payload["service_boundary"]["preferred_transport"], "mcp_tool_process")
        self.assertIn("--startup-probe", payload["service_boundary"]["startup_contract"]["startup_probe_command"])

    def test_readme_and_plugin_manifest_publish_same_health_contract(self):
        readme = Path("/home/hali/.openclaw/extensions/memory-aegis-v7/README.md").read_text(encoding="utf-8")
        manifest = json.loads(
            Path("/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json").read_text(encoding="utf-8")
        )
        payload = self.app.public_surface()

        manifest_health = manifest["healthContract"]

        self.assertEqual(manifest_health["states"], payload["engine"]["health_states"])
        self.assertEqual(manifest_health["capabilities"], payload["health_contract"]["capabilities"])
        self.assertIn("`HEALTHY`, `DEGRADED_SYNC`, and `BROKEN`", readme)
        self.assertIn("`health.state`, `health.issues`, and `health.capabilities`", readme)
        self.assertIn("default scope is `agent/default`", readme)
        self.assertIn("guided/background hygiene", readme)
        self.assertIn("local sidecar/service boundary", readme)
        self.assertIn("--service-info", readme)
        self.assertIn("--startup-probe", readme)
        self.assertIn("memory_stats", manifest_health["tools"])
        self.assertIn("memory_doctor", manifest_health["tools"])

    def test_plugin_manifest_default_tools_match_python_public_surface(self):
        manifest = json.loads(
            Path("/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json").read_text(encoding="utf-8")
        )
        payload = self.app.public_surface()

        self.assertEqual(
            manifest["consumerSurface"]["defaultTools"],
            DEFAULT_OPERATIONS,
        )

    def test_plugin_manifest_advanced_tools_match_python_public_surface(self):
        manifest = json.loads(
            Path("/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json").read_text(encoding="utf-8")
        )
        payload = self.app.public_surface()

        self.assertEqual(
            manifest["consumerSurface"]["advancedTools"],
            ADVANCED_OPERATIONS,
        )

    def test_public_surface_registry_size_matches_runtime_tool_registry(self):
        payload = self.app.public_surface()

        self.assertEqual(payload["consumer_contract"]["registry_size"], len(TOOL_REGISTRY))

    def test_plugin_manifest_tool_names_cover_runtime_registry(self):
        manifest = json.loads(
            Path("/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json").read_text(encoding="utf-8")
        )
        manifest_tool_names = {tool["name"] for tool in manifest["tools"]}

        self.assertTrue(set(registry_tool_names()).issubset(manifest_tool_names))

    def test_status_summary_uses_plain_language_for_everyday_users(self):
        self.app.put_memory(
            "Everyday status should stay readable.",
            type="semantic",
            scope_type="session",
            scope_id="default",
        )

        summary = self.app.status_summary()

        self.assertIn("Aegis Status", summary)
        self.assertIn("Aegis is ready and local memory is working normally.", summary)
        self.assertIn("Active memories: 1", summary)

    def test_status_summary_explains_degraded_state_without_calling_it_broken(self):
        self.app.set_scope_policy(
            "project",
            "P1",
            sync_policy="sync_eligible",
            sync_state="pending_sync",
        )

        summary = self.app.status_summary()

        self.assertIn("usable locally", summary)
        self.assertIn("DEGRADED_SYNC", summary)
        self.assertNotIn("not ready for safe memory use", summary)

    def test_status_includes_storage_section_for_operator_visibility(self):
        payload = self.app.status()

        self.assertIn("storage", payload)
        self.assertIn("allocated_bytes", payload["storage"])
        self.assertIn("rows", payload["storage"])
        self.assertIn("memories", payload["storage"]["rows"])

    def test_doctor_includes_storage_policy_and_footprint(self):
        payload = self.app.doctor()

        self.assertIn("storage", payload)
        self.assertIn("compaction_policy", payload["storage"])
        self.assertEqual(payload["storage"]["compaction_policy"]["archived_memory_days"], 30)
        self.assertIn("allocated_bytes", payload["storage"])

    def test_doctor_summary_warns_when_historical_rows_outgrow_live_memory(self):
        active = self.app.put_memory(
            "Active record for storage guidance.",
            type="semantic",
            scope_type="project",
            scope_id="GC",
            source_kind="manual",
            source_ref="surface://active",
        )
        archived = self.app.put_memory(
            "Archived record for storage guidance.",
            type="semantic",
            scope_type="project",
            scope_id="GC",
            source_kind="manual",
            source_ref="surface://archived",
        )
        self.assertIsNotNone(active)
        self.assertIsNotNone(archived)
        self.app.storage.execute(
            "UPDATE memories SET status = 'archived', archived_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (archived.id,),
        )
        for index in range(3):
            self.app.storage.execute(
                """
                INSERT INTO governance_events (
                    id, event_kind, scope_type, scope_id, memory_id, evidence_event_id, payload_json, created_at
                ) VALUES (?, 'surface_growth', 'project', 'GC', ?, NULL, '{}', CURRENT_TIMESTAMP)
                """,
                (f"gov_surface_{index}", archived.id),
            )

        summary = self.app.doctor_summary()

        self.assertIn("Historical rows", summary)
        self.assertIn("Run storage compaction soon.", summary)


if __name__ == "__main__":
    unittest.main()
