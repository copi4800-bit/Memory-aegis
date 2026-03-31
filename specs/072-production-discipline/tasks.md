# Tasks: Production Discipline

**Input**: Design documents from `/specs/072-production-discipline/`
**Prerequisites**: plan.md, spec.md

## Phase 1: Setup

- [x] T001 Create feature spec and plan in `specs/072-production-discipline/`
- [x] T002 Define the validation command set for the tranche

## Phase 2: Release Gate

- [x] T003 Add a single release gate checklist in `docs/RELEASE-GATE.md`
- [x] T004 Add a rollback checklist in `docs/ROLLBACK-CHECKLIST.md`

## Phase 3: Soak Practice

- [x] T005 Add a soak-test checklist in `docs/SOAK-TEST-CHECKLIST.md`

## Phase 4: Runbooks

- [x] T006 Add polling-stall runbook in `docs/runbooks/polling-stall.md`
- [x] T007 Add sync-failure runbook in `docs/runbooks/sync-failure.md`
- [x] T008 Add DB-lock runbook in `docs/runbooks/db-lock.md`
- [x] T009 Add restore-mismatch runbook in `docs/runbooks/restore-mismatch.md`
- [x] T010 Add duplicate-reply runbook in `docs/runbooks/duplicate-reply.md`

## Phase 5: Closeout

- [x] T011 Validate the referenced focused command set still runs green
- [x] T012 Record the stop condition: no further tranche should open unless runtime evidence reveals a new distinct risk class
