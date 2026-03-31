# Release Gate

Use this checklist before restarting the live gateway on the current deployment class.

## Stop Rule

If any step below fails, do not continue the release. Fix the issue or rollback.

## Gate

1. Confirm the worktree state is understood.
2. Run the focused validation suite:
   `PYTHONPATH=. .venv/bin/python -m pytest -q tests/acceptance tests/regression tests/test_observability_runtime.py tests/replication/test_sync.py`
3. If runtime code changed, run the higher-confidence supporting suite:
   `PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_v7_runtime.py tests/test_retrieval.py tests/test_storage.py tests/test_user_surface.py tests/test_workflow_governance.py tests/test_python_only_runtime_contract.py`
4. If host-side OpenClaw code changed, run the host build:
   `npm run build`
5. Verify the target backup path is writable and a fresh backup can be created if needed.
6. If sync-related code changed, run the targeted sync integration check:
   `PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_integration.py -k 'scope_policy_defaults_local_only_and_lists_explicit_sync_eligible or python_cli_sync_export_preview_import'`
7. Restart the service only after the above is green:
   `systemctl --user restart openclaw-gateway.service`
8. Verify post-restart health:
   `systemctl --user status openclaw-gateway.service`
9. Verify live runtime signal:
   - `memory-aegis-v7 registered` appears in service logs
   - no fresh `plugins.allow is empty` warning appears
   - one Telegram message round-trip succeeds

## Release Evidence

Record these before calling the release good:

- exact command set run
- pass/fail result
- service restart timestamp
- one live Telegram sanity-check timestamp
