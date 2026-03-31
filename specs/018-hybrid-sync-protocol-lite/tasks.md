# Tasks: Hybrid Sync Protocol Lite

**Input**: Design documents from `/specs/018-hybrid-sync-protocol-lite/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/018-hybrid-sync-protocol-lite/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/018-hybrid-sync-protocol-lite/spec.md) and [specs/018-hybrid-sync-protocol-lite/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/018-hybrid-sync-protocol-lite/plan.md)

## Phase 2: Sync Envelope Flows

- [x] T002 [US1] Add Python integration coverage for sync envelope export/preview/import in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T003 [US1] Add sync envelope export/preview/import to [aegis_py/operations.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/operations.py)
- [x] T004 [US2] Expose sync envelope flows in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py), [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py), and [aegis_py/cli.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/cli.py)

## Phase 3: Documentation

- [x] T005 [US2] Update [aegis_py/surface.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/surface.py) and [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) to describe sync protocol lite operations

## Phase 4: Polish

- [x] T006 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/018-hybrid-sync-protocol-lite/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/018-hybrid-sync-protocol-lite/plan.md)
- [x] T007 [FOUNDATION] Reconcile completion state in [specs/018-hybrid-sync-protocol-lite/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/018-hybrid-sync-protocol-lite/tasks.md)
