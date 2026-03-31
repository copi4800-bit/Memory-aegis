# Implementation Plan: Aegis Python CI And Release Packaging Hardening

**Branch**: `003-ci-release-hardening` | **Date**: 2026-03-23 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/003-ci-release-hardening/spec.md)
**Input**: Feature specification from `/specs/003-ci-release-hardening/spec.md`

## Summary

Turn the current local-only Aegis Python validation discipline into a repeatable CI and release-packaging workflow by wiring the canonical Python test command into repository automation, documenting release packaging steps, and recording release evidence in active `spec-kit` artifacts.

## Technical Context

**Language/Version**: Python 3.13.x and repository CI YAML workflows  
**Primary Dependencies**: Existing `pytest` suite, repository GitHub Actions workflow files, current documentation artifacts  
**Storage**: Local SQLite/FTS5 remains the validation target of the workflow  
**Testing**: Python regression suite under `tests/`, executed via the canonical `pytest` command  
**Target Platform**: GitHub-hosted CI for repository validation plus local maintainer environments for release packaging  
**Project Type**: Local library/plugin repo with Python engine and repository automation artifacts  
**Performance Goals**: CI should run the canonical Python validation flow reliably enough for routine repository changes without redefining engine semantics  
**Constraints**: Preserve the local-first engine posture, do not add cloud runtime dependencies to the engine, keep CI and release workflow aligned with active `spec-kit` artifacts  
**Scale/Scope**: One release-discipline feature wave covering CI validation, release packaging instructions, and release evidence tracking

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Local-First Memory Engine`: Pass. CI validates the local-first engine; it does not change the engine into a cloud-dependent service.
- `Brownfield Refactor Over Rewrite`: Pass. This feature works at repository automation and release discipline level.
- `Explainable Retrieval Is Non-Negotiable`: Pass. The canonical Python suite retains the retrieval benchmark and explanation checks already established.
- `Safe Memory Mutation By Default`: Pass. No lifecycle or hygiene semantics are expanded here.
- `Measured Simplicity`: Pass. The work is narrowly bounded to CI and release workflow hardening.

No constitutional violations are expected for this feature.

## Project Structure

### Documentation (this feature)

```text
specs/003-ci-release-hardening/
├── plan.md
├── spec.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
.github/
└── workflows/

README.md
AEGIS_PYTHON_SPEC.md
requirements.txt
tests/
```

**Structure Decision**: Keep the existing repository structure. This feature should primarily touch CI workflow files, packaging/release docs, and `spec-kit` planning artifacts rather than core engine modules.

## Phase Plan

### Phase 0 - Validation Workflow Inventory

Objective: Confirm the current canonical local validation command and identify what is still missing for CI and release packaging.

Current inventory on 2026-03-23:

- the canonical local Python validation command already exists in `README.md`
- a legacy TypeScript-oriented workflow exists at `.github/workflows/aegis-gate.yml`
- no dedicated Python CI workflow existed before this feature
- no dedicated Python release packaging helper existed before this feature

### Phase 1 - CI Validation Wiring

Objective: Define and implement the repository workflow that runs the canonical Python validation suite in CI.

Primary Files:

- [.github/workflows/aegis-python-validation.yml](/home/hali/.openclaw/extensions/memory-aegis-v7/.github/workflows/aegis-python-validation.yml)
- [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md)

Current status on 2026-03-23:

- repository-local Python CI workflow added at `.github/workflows/aegis-python-validation.yml`
- workflow contract is locked by `tests/test_release_workflow.py`
- remote GitHub execution is not yet verified because the repo has not been pushed upstream

### Phase 2 - Release Packaging Workflow

Objective: Document or script the release packaging steps that follow a successful validation pass.

Primary Files:

- [scripts/release-python-package.sh](/home/hali/.openclaw/extensions/memory-aegis-v7/scripts/release-python-package.sh)
- [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md)
- [AEGIS_PYTHON_SPEC.md](/home/hali/.openclaw/extensions/memory-aegis-v7/AEGIS_PYTHON_SPEC.md)

Current status on 2026-03-23:

- local source bundle helper added at `scripts/release-python-package.sh`
- bundle contents are locked by `tests/test_release_workflow.py`
- README and spec describe the packaging baseline as a local bundle workflow

### Phase 3 - Release Evidence Record

Objective: Capture what the CI and release workflow validate, and what gaps still remain after the feature scope completes.

Primary Files:

- [specs/003-ci-release-hardening/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/003-ci-release-hardening/plan.md)
- [specs/003-ci-release-hardening/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/003-ci-release-hardening/tasks.md)

## Complexity Tracking

No constitution violations currently require exception handling.

## Validation Closeout

Validation run completed on 2026-03-23 for feature `003-ci-release-hardening`.

Executed command:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests
```

Observed result:

- `53 passed in 1.00s`

Validated additions in this feature:

- repository-local Python CI workflow definition for the canonical validation command
- local release bundle helper for packaging the Python engine artifacts
- regression coverage proving the CI workflow and packaging helper remain present and correctly wired

Remaining gaps after this hardening wave:

- the Python CI workflow has not been executed on GitHub yet because the repo has not been pushed there
- release packaging is still a local source bundle workflow, not a package registry publishing pipeline
- branch/tag release discipline still needs a separate feature if it becomes part of the release bar
