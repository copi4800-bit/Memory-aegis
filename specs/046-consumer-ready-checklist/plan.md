# Implementation Plan: Consumer Ready Checklist

**Branch**: `046-consumer-ready-checklist` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/046-consumer-ready-checklist/spec.md`

## Summary

Define a repo-native completion checklist for the question "is Aegis v4 actually ready for non-technical users?" and assess the current codebase against that checklist using concrete evidence. This feature is documentation and governance work, not a claim that the product is already complete.

## Technical Context

**Language/Version**: Markdown feature artifacts, existing Python 3.13.x and TypeScript codebase as evidence base  
**Primary Dependencies**: active `specs/*` artifacts, `.specify/memory/constitution.md`, `aegis_py` runtime surfaces, existing tests  
**Storage**: N/A for the artifact itself; current engine remains SQLite-backed  
**Testing**: repo evidence review, targeted validation references, optional prerequisite check  
**Target Platform**: current OpenClaw and MCP local-first runtime  
**Project Type**: product-readiness governance and assessment artifact  
**Performance Goals**: N/A  
**Constraints**: must not confuse implemented engine capability with consumer-product completeness; must cite real repo evidence; must stay inside Spec Kit as the source of truth  
**Scale/Scope**: one feature artifact set covering current readiness state and next tranches

## Constitution Check

- **Local-First Memory Engine**: Pass. The checklist explicitly judges whether the current local-first runtime is sufficient for end users without requiring hosted dependencies.
- **Brownfield Refactor Over Rewrite**: Pass. This feature records readiness against the current brownfield codebase rather than proposing a rewrite.
- **Explainable Retrieval Is Non-Negotiable**: Pass. The checklist preserves explainability as part of any consumer-ready claim rather than trading it away for a thinner UX.
- **Safe Memory Mutation By Default**: Pass. The checklist treats correction, forgetting, and recovery safety as qualifying gates.
- **Measured Simplicity**: Pass. The feature reduces ambiguity by replacing vague "complete" claims with bounded criteria and tranche sequencing.

## Project Structure

### Documentation (this feature)

```text
specs/046-consumer-ready-checklist/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
aegis_py/
├── app.py
├── cli.py
└── mcp/server.py

src/
├── aegis-manager.ts
├── cli/setup.ts
└── ux/onboarding.ts

tests/
├── test_user_surface.py
├── test_integration.py
└── test_release_workflow.py

specs/
├── 038-simple-user-surface/
├── 041-completion-program/
└── 045-health-and-degraded-runtime/
```

**Structure Decision**: This feature does not add runtime code. It uses existing Python surfaces, TypeScript compatibility paths, tests, and feature history as the evidence base for the readiness judgment.

## Checklist

| ID | Checklist Item | Qualifies As Consumer-Ready When | Current State | Evidence |
|----|----------------|----------------------------------|---------------|----------|
| CRC-001 | Simple everyday verbs | A non-technical user can remember, recall, correct, and forget information through stable user-facing flows | `MET` | [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py#L780), [tests/test_user_surface.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_user_surface.py#L13) |
| CRC-002 | Stable local runtime | Core memory behavior works offline with local SQLite and validated runtime health reporting | `MET` | [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py#L362), [specs/045-health-and-degraded-runtime/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/045-health-and-degraded-runtime/plan.md#L62) |
| CRC-003 | Human-readable diagnostics | User-facing status and error explanations are primarily understandable without developer concepts | `MET` | Default status is now plain-language first in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py#L947), [aegis_py/cli.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/cli.py#L17), and plugin `memory_stats` content in [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts#L534) |
| CRC-004 | Real onboarding path | First-run setup for non-technical users uses the active production runtime and is not merely a developer self-test | `MET` | Active path now runs Python onboarding through [aegis_py/cli.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/cli.py#L17) and [src/cli/setup.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/cli/setup.ts#L48); legacy TS onboarding remains non-authoritative in [src/ux/onboarding.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/ux/onboarding.ts#L30) |
| CRC-005 | No dependency on retired paths | End-user readiness does not rely on the retired TS engine or compatibility stubs | `MET` | retired paths now fail clearly as explicit stubs in [src/aegis-manager.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/aegis-manager.ts#L1) and [src/ux/onboarding.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/ux/onboarding.ts#L1) rather than appearing to be active product paths |
| CRC-006 | Safe recovery for ordinary users | Backup and restore exist with enough guidance and surface simplicity for non-technical recovery flows | `MET` | Recovery and doctor flows are now summary-first in [aegis_py/cli.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/cli.py#L17) with supporting summaries in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py#L998), while structured payloads remain available explicitly |
| CRC-007 | Guided host integration | The plugin/bootstrap path exposes the Python-owned runtime without making the user understand internal architecture | `MET` | the plugin manifest now declares an explicit ordinary-user default path and advanced-tool separation in [openclaw.plugin.json](/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json), aligned with [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) |
| CRC-008 | Evidence-backed completion claim | A "100% complete" claim is allowed only after explicit closure review against a completion contract | `MET` | [specs/041-completion-program/roadmap.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/041-completion-program/roadmap.md#L13) |

## Current Assessment

The current repo is best described as:

- **engine-ready** for local-first memory operations
- **developer-ready** for integration and maintenance workflows
- **consumer-ready** for the current local-first deployment class

Closure review status:

- `050-consumer-closure-review` now records a final `GO` decision on the consumer-complete claim for the current local-first deployment class.

## Follow-Up Tranches

### Tranche A: Production Onboarding For Non-Technical Users

Goal: replace the current self-test style setup with a live onboarding path on top of the Python-owned runtime.

Includes:

- one active onboarding flow owned by Python or a thin host wrapper over Python
- first-run checks for DB creation, write test, recall test, and health summary
- plain-language guidance when setup fails

### Tranche B: Consumer-Safe Everyday Surface

Goal: reduce the default user experience to a narrow set of understandable actions and outputs.

Includes:

- keep `remember`, `recall`, `correct`, `forget`, and status as the primary user verbs
- hide advanced scope and sync controls from the default path
- return user-facing messages first, machine-readable detail second

### Tranche C: Consumer Recovery And Trust Surface

Goal: make backup, restore, diagnostics, and health understandable and safe for ordinary users.

Includes:

- plain-language health summaries over the existing health contract
- guided backup/restore flows with safer defaults
- user-facing explanation for degraded versus broken state

### Tranche D: Closure Review For Consumer Completeness

Goal: decide whether Aegis may be called consumer-ready after the earlier tranches land.

Includes:

- compare implemented state against this checklist
- close any remaining partial or missing items
- make an explicit go/no-go decision on the completion claim

## Complexity Tracking

No constitution violations currently require exception handling.
