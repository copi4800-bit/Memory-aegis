# State

## Current Position
- **Active Step**: The consumer-complete local-first baseline remains governed as complete through `050-consumer-closure-review` and `051-guided-host-integration`; `054-default-surface-consistency` preserves the bounded default path; `055-product-adoption-roadmap` defines the next product-facing strategy layer; `056-time-to-first-value` executes Tranche A; `057-product-storytelling` starts Tranche B; `058-demo-and-benchmark-presentation` completes the current demo/proof slice for Tranche B; `059-packaging-polish` completes the current shipping/presentation refinement slice; `060-integration-story` completes the current integrator-facing polish slice; `061-citation-and-grounding-story` closes the current productization tranche; `062-v4-to-v7-migration-roadmap` defines the migration strategy; `063-evidence-log-foundation` is implemented and validated; `064-internal-evidence-consumption` is implemented and validated; `065-promotion-gate-primitives` is implemented and validated; `066-formal-memory-state-machine` is implemented and validated; `067-state-aware-internal-retrieval` is implemented and validated; `068-state-aware-governed-operations` is implemented and validated; `.planning/PRODUCTION-EXCELLENCE-ROADMAP.md` is the active derivative execution order for post-capability production hardening.
- **Status**: `.planning/` remains a derivative GSD coordination layer. `specs/*` and `.specify/memory/constitution.md` remain the source of truth. The current repo state may still be described as consumer-complete for the current local-first deployment class, while `063` is landed as the compatibility-first storage foundation, `064` is landed as the internal-runtime evidence-consumption slice, `065` is landed as the narrow promotion-boundary slice, `066` is landed as the admission-aware state-model slice, `067` is landed as the bounded state-aware retrieval slice, and `068` is the next state-aware governed-operations slice for the v4-to-v7 path.

## Decisions
- **D-01**: Use standard `sqlite3` Python library for the storage layer.
- **D-02**: Follow refined schema from `11.md` (metadata_json, scope_id, source_ref).
- **D-03**: Prioritize suggestion-first conflict handling (no auto-archive for now).
- **D-04**: Standardize repository workflow as `GSD + Spec Kit`.
- **D-05**: `specs/*` and `.specify/memory/constitution.md` override `.planning/*` when they disagree.
- **D-06**: `Oracle Beast` focuses on query expansion for semantic recall.
- **D-07**: `Weaver Beast` and `Librarian Beast` manage semantic deduplication and merging.
- **D-08**: `Meerkat` and `Consolidator Beast` will implement a temporal-preference policy for automated fact correction.
- **D-09**: Tranche A (`042`) enforced strict provenance tracking via node identity and manual conflict resolution rather than silent multi-node merging. It is now successfully implemented and validated.
- **D-10**: Tranche B (`043`) successfully enforced explicit `PolicyMatrix` configurations to bound autonomous operations, complete with audit-first explanations and rollback paths.
- **D-11**: Tranche C (`044`) will adopt `PRAGMA user_version` for migrations and the native SQLite backup API to ensure safety at the engine level without heavy third-party ORMs.
- **D-12**: "100% complete" for the current wave means a fully green Python-owned runtime baseline first, then operational hardening. No new capability work should bypass red-test recovery.
- **D-13**: The validated runtime gaps presently in scope for `044` are semantic dedupe, semantic recall, trust/conflict shaping, Weaver auto-link and bounded multi-hop behavior, scoped backup preview/restore, and legacy schema repair.
- **D-14**: The canonical validation commands for `044` are `.venv/bin/python -m pytest -q tests` and `npm run test:bootstrap`.
- **D-15**: `044-production-hardening` is treated as operationally closed for the validated local-first baseline, with closure evidence recorded under `specs/044-production-hardening/closure.md`.
- **D-16**: The next bounded gap toward "100% complete" is explicit health-state modeling and degraded runtime semantics, which now live in `045-health-and-degraded-runtime`.
- **D-17**: `046-consumer-ready-checklist` is the governing readiness checklist for non-technical-user claims on the current local-first deployment class.
- **D-18**: `050-consumer-closure-review` records a final `GO` decision: Aegis v4 may be called consumer-complete for the current local-first deployment class.
- **D-19**: `051-guided-host-integration` closes the final host-surface and TS-era ambiguity blockers by defining the bounded consumer surface in `openclaw.plugin.json`, aligning `README.md`, and converting legacy TS onboarding into explicit failure stubs.
- **D-20**: Advanced operator tools remain present, but they no longer block the consumer-complete label because the manifest and README now separate them from the default ordinary-user path.
- **D-21**: Post-closure simplification work should land as narrow consistency slices that preserve the Python-owned consumer contract and keep shipped artifacts aligned with that contract, starting with `054-default-surface-consistency`.
- **D-22**: Future product-facing adoption work should be chosen from `.planning/AEGIS-ADOPTION-ROADMAP.md`, which defines the twelve tactics Aegis should borrow from Mem0, NeuralMemory, and strong RAG systems while preserving Aegis core invariants.
- **D-23**: The first adoption-roadmap execution tranche is `056-time-to-first-value`, centered on install, setup, first remember, and first recall for newcomers.
- **D-24**: The first Tranche B execution slice is `057-product-storytelling`, which should improve product comprehension before broader demo/benchmark packaging work.
- **D-25**: `058-demo-and-benchmark-presentation` adds one runnable demo and one benchmark summary grounded in current repo evidence, and is now treated as the completed demo/proof slice for the current Tranche B wave.
- **D-26**: `059-packaging-polish` makes the shipped release bundle and package reflect the same Python-first newcomer path as the repo itself by shipping setup, demo, and quickstart artifacts together.
- **D-27**: `060-integration-story` makes the thin-host boundary easier to adopt by shipping one runnable integration demo and one README quickstart tied to `--service-info`, `--startup-probe`, and `--tool`.
- **D-28**: `061-citation-and-grounding-story` closes the current productization tranche by making provenance, ranking reasons, and trust shape easy to demonstrate through one runnable grounding demo and one README trust section.
- **D-29**: `062-v4-to-v7-migration-roadmap` converts `/home/hali/.openclaw/11.md` into a tranche-based migration path; the first implementation-ready tranche is `063-evidence-log-foundation`.
- **D-30**: `063-evidence-log-foundation` should be treated as a compatibility-first storage tranche: add immutable evidence logging and evidence linkage before opening promotion gates or a richer v7 state machine.
- **D-31**: `063-evidence-log-foundation` is now implemented and validated: SQLite evidence events are append-only, canonical ingest persists raw evidence, direct storage writes backfill evidence linkage, rebuild can backfill legacy memories, and the Python plus host contract suites are green.
- **D-32**: The tranche immediately after `063` should stay narrower than a full promotion gate: `064-internal-evidence-consumption` should add internal evidence lookup and coverage helpers before admission control or richer state work.
- **D-33**: `064-internal-evidence-consumption` is now implemented and validated: runtime-owned helper paths can resolve linked evidence, summarize evidence coverage, and preserve current public retrieval/status contracts while Python and host contract suites remain green.
- **D-34**: The tranche immediately after `064` should introduce promotion-gate primitives before the richer state-machine slice: `065-promotion-gate-primitives` should add candidate-first admission seams without reopening retrieval rewrites.
- **D-35**: `065-promotion-gate-primitives` is now implemented and validated: canonical ingest builds internal memory candidates, evaluates bounded promotion decisions from evidence and admission signals, stores review-oriented contradiction hints without breaking public retrieval/status contracts, and the Python plus host contract suites are green.
- **D-36**: The tranche immediately after `065` should formalize admission-aware memory states before retrieval consumption work: `066-formal-memory-state-machine` should map promotion outcomes into explicit internal states without reopening retrieval rewrites.
- **D-37**: `066-formal-memory-state-machine` is now implemented and validated: admission-aware states are represented through stable internal contracts, canonical ingest maps promotion outcomes into explicit states, lifecycle compatibility is preserved, and Python plus host contract suites remain green.
- **D-38**: The tranche immediately after `066` should let retrieval and policy internals consume `admission_state` in bounded ways before any broader retrieval redesign: `067-state-aware-internal-retrieval` should stay shaping-first and compatibility-first.
- **D-39**: `067-state-aware-internal-retrieval` is now implemented and validated: retrieval internals consume `admission_state` for bounded filtering and trust shaping, draft/invalidated states stay out of active retrieval paths, hypothesized/consolidated states shape trust conservatively, and Python plus host contract suites remain green.
- **D-40**: The tranche immediately after `067` should let governance and background-operation internals consume state/evidence/promotion together in bounded ways before any broader autonomy redesign: `068-state-aware-governed-operations` should remain explanation-first and compatibility-first.
- **D-41**: Post-capability work should now optimize for production excellence over new feature breadth: correctness first, observability second, production discipline third.
- **D-42**: `072-production-discipline` is the intended stopping point for the current production-excellence wave; after it lands, further work should come only from new runtime evidence or a new deployment-class claim, not from opening more speculative tranches.
- **D-43**: `074-v8-core-memory-dynamics` is the first acceptable theory-to-runtime tranche after the v8 theory docs: it must stay executable, bounded, and explanation-first, using surrogate dynamic signals rather than reopening a simulator or schema-heavy redesign.

## Blockers
- No active blocker is currently known for the current local-first consumer-complete claim.
- Any future blocker would come from broadening the claim beyond the local-first deployment class or regressing the Python-owned public contract.

## Next Step
- Preserve the current Python-owned public contract and consumer/default host surface.
- Treat `054-default-surface-consistency` as the contract-stability layer for the bounded host/runtime path.
- Use `.planning/AEGIS-ADOPTION-ROADMAP.md`, `055-product-adoption-roadmap`, `056-time-to-first-value`, `057-product-storytelling`, and `058-demo-and-benchmark-presentation` as the completed product-facing baseline before opening the next polish slice.
- Treat `059-packaging-polish` as the current product-polish execution step for shipped artifacts.
- Treat `060-integration-story` as the current product-polish execution step for thin-host adoption.
- Treat `061-citation-and-grounding-story` as the tranche-closing trust step before stopping this productization wave.
- Treat `062-v4-to-v7-migration-roadmap` as the next architecture strategy layer after the productization wave; use it to open `063-evidence-log-foundation` rather than jumping straight to a rewrite.
- Treat `063-evidence-log-foundation` as implemented foundation work rather than open planning.
- Treat `064-internal-evidence-consumption` as implemented evidence-readiness work rather than open planning.
- Treat `065-promotion-gate-primitives` as implemented admission-foundation work rather than open planning.
- Treat `066-formal-memory-state-machine` as implemented state-foundation work rather than open planning.
- Treat `067-state-aware-internal-retrieval` as implemented retrieval-readiness work rather than open planning.
- Treat `068-state-aware-governed-operations` as implemented and validated architecture work after `067`.
- Use `068` to make governance and operational internals state-aware without collapsing into a broad autonomy rewrite by default.
- Use `.planning/PRODUCTION-EXCELLENCE-ROADMAP.md` to sequence the next reliability work after `068`, starting with acceptance/regression hardening before observability and release-discipline work.
- Treat `074-v8-core-memory-dynamics` as the next executable architecture slice when opening the v8 theory documents: bounded evidence/support/conflict/trust/readiness scoring and one hysteresis gate are in scope; simulator-first work is not.
- Treat future work as net-new scope beyond the current local-first consumer-complete milestone rather than unfinished baseline completion work.
