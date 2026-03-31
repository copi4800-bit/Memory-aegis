# Implementation Plan: V4 To V7 Migration Roadmap

**Branch**: `062-v4-to-v7-migration-roadmap` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/062-v4-to-v7-migration-roadmap/spec.md`

## Summary

Turn `11.md` into an executable architecture roadmap for Aegis by mapping the proposed v7 design to the current v4 codebase, identifying real gaps, and ordering migration tranches that preserve the stable local-first runtime already shipped in OpenClaw.

## Technical Context

**Language/Version**: Markdown planning artifacts  
**Primary Dependencies**: `/home/hali/.openclaw/11.md`, `aegis_py/*`, `.planning/ROADMAP.md`, `.planning/STATE.md`, existing Spec Kit slices through `061`  
**Storage**: planning/docs only  
**Testing**: manual artifact review; optional future governance tests if this roadmap later becomes machine-checked  
**Target Platform**: maintainers and future implementation slices  
**Constraints**: must avoid rewrite framing; must preserve the current local-first runtime as the production baseline; must distinguish existing v4 subsystems from truly new v7 work  
**Scale/Scope**: one roadmap feature, one tranche model, and GSD state updates

## Constitution Check

- **Local-First Memory Engine**: Pass. The roadmap explicitly preserves local-first as an invariant.
- **Brownfield Refactor Over Rewrite**: Pass. The roadmap is specifically about migration by tranche, not replacement.
- **Explainable Retrieval Is Non-Negotiable**: Pass. Explainability remains a preserved invariant.
- **Safe Memory Mutation By Default**: Pass. The roadmap identifies validation/policy gating as a strengthening move, not a relaxation.
- **Measured Simplicity**: Pass. The roadmap keeps the current stable v4 boundary intact while sequencing deeper architectural work.

## Migration Reading

Primary architecture source:

- [/home/hali/.openclaw/11.md](/home/hali/.openclaw/11.md)

Key current v4 source areas that the roadmap must map:

- [app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py)
- [surface.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/surface.py)
- [storage/models.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/models.py)
- [storage/manager.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py)
- [memory/ingest.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/ingest.py)
- [retrieval/search.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py)
- [retrieval/contract.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/contract.py)
- [conflict/core.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/conflict/core.py)
- [hygiene/engine.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/hygiene/engine.py)
- [governance/automation.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/governance/automation.py)
- [governance/policy.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/governance/policy.py)
- [governance/rollback.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/governance/rollback.py)

## Tranche Hypothesis

The roadmap should validate or refine this likely sequence:

1. `Evidence Log Foundation`
2. `Promotion Gate And Admission Control`
3. `Formal Memory State Machine`
4. `Governed Background Intelligence Hardening`
5. `Storage Split And Specialized Retrieval Internals`

## Validation Plan

- Create a migration roadmap artifact that maps every major v7 block in `11.md` to concrete v4 modules and gap status.
- Define tranche ordering, dependencies, risks, invariants, and anti-goals.
- Update `.planning/ROADMAP.md` and `.planning/STATE.md` so this roadmap becomes the next architectural strategy layer after `061`.

## Expected Evidence

- one Spec Kit feature for the v4-to-v7 roadmap
- tranche ordering tied to real current modules
- first implementation-ready tranche identified
- planning layer updated to point future architecture work at this roadmap

## Complexity Tracking

No constitution violations currently require exception handling. The main risk is turning the proposal into rewrite language instead of migration language.
