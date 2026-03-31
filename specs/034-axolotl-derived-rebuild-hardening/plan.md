# Implementation Plan: Axolotl Derived Rebuild Hardening

**Branch**: `034-axolotl-derived-rebuild-hardening` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/034-axolotl-derived-rebuild-hardening/spec.md)
**Input**: Feature specification from `/specs/034-axolotl-derived-rebuild-hardening/spec.md`

## Summary

Harden the Python rebuild flow so it regenerates missing derived `subject` and `summary` fields for active legacy rows before running existing link backfills.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/app.py`, `aegis_py/memory/extractor.py`, existing rebuild integration tests  
**Storage**: existing SQLite `memories.subject`, `memories.summary`, and `memory_links` tables  
**Testing**: canonical prerequisite check, `npm run lint`, `npm run test:bootstrap`, `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`  
**Constraints**: local-only deterministic derivation, preserve explicit non-empty metadata, keep rebuild conservative and non-destructive  

## Constitution Check

- `Local-First Memory Engine`: Pass.
- `Brownfield Refactor Over Rewrite`: Pass.
- `Explainable Retrieval Is Non-Negotiable`: Pass.
- `Safe Memory Mutation By Default`: Pass.
- `Measured Simplicity`: Pass.

## Design Direction

- add a rebuild-local hardening pass that only touches active rows missing `subject` and/or `summary`
- reuse the same deterministic extractor and subject normalization already used during ingest
- run metadata hardening before same-subject link backfill so legacy rows can regain current structure
- expose a small rebuild metric for recovered rows instead of broad new surface area

## Work Plan

1. reconcile `.planning/STATE.md` to feature `034-axolotl-derived-rebuild-hardening`
2. extend rebuild in `aegis_py/app.py` to backfill missing derived metadata before link backfill
3. add integration coverage proving rebuild backfills derived metadata and same-subject links while preserving explicit values
4. run canonical validation and record evidence
5. reconcile completion state in tasks

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`: pass
  - resolved `FEATURE_DIR` to `/home/hali/.openclaw/extensions/memory-aegis-v7/specs/034-axolotl-derived-rebuild-hardening`
  - reported `AVAILABLE_DOCS` containing `tasks.md`
- `npm run lint`: pass
- `npm run test:bootstrap`: pass, 17 tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`: pass, 94 passed in 2.96s
