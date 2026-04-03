# State

## Current Position
- **Active Step**: The consumer-complete local-first baseline remains governed as complete through `050-consumer-closure-review` and `051-guided-host-integration`; `054-default-surface-consistency` preserves the bounded default path; `055-product-adoption-roadmap` defines the next product-facing strategy layer; `056-time-to-first-value` executes Tranche A; `057-product-storytelling` starts Tranche B; `058-demo-and-benchmark-presentation` completes the current demo/proof slice for Tranche B; `059-packaging-polish` completes the current shipping/presentation refinement slice; `060-integration-story` completes the current integrator-facing polish slice; `061-citation-and-grounding-story` closes the current productization tranche; `062-v4-to-v10-migration-roadmap` defines the migration strategy; `063-evidence-log-foundation` is implemented and validated; `064-internal-evidence-consumption` is implemented and validated; `065-promotion-gate-primitives` is implemented and validated; `066-formal-memory-state-machine` is implemented and validated; `067-state-aware-internal-retrieval` is implemented and validated; `068-state-aware-governed-operations` is implemented and validated; `086-ingest-policy-readiness` closes the current write-path verdict branch for the present deployment class; `090-truthkeep-vnext-architecture-consolidation` remains the active runtime-cleanup slice; `091-prehistoric-supreme-core-system` remains the active canonical core-language slice; `092-prehistoric-core-execution-priorities` is now the active execution-order slice for prehistoric operationalization; `.planning/PRODUCTION-EXCELLENCE-ROADMAP.md` remains the derivative execution order for post-capability production hardening.
- **Status**: `.planning/` remains a derivative GSD coordination layer. `specs/*` and `.specify/memory/constitution.md` remain the source of truth. The current repo state may still be described as consumer-complete for the current local-first deployment class, while `063` is landed as the compatibility-first storage foundation, `064` is landed as the internal-runtime evidence-consumption slice, `065` is landed as the narrow promotion-boundary slice, `066` is landed as the admission-aware state-model slice, `067` is landed as the bounded state-aware retrieval slice, and `068` is the next state-aware governed-operations slice for the v4-to-v10 path.

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
- **D-29**: `062-v4-to-v10-migration-roadmap` converts `/home/hali/.openclaw/11.md` into a tranche-based migration path; the first implementation-ready tranche is `063-evidence-log-foundation`.
- **D-30**: `063-evidence-log-foundation` should be treated as a compatibility-first storage tranche: add immutable evidence logging and evidence linkage before opening promotion gates or a richer v10 state machine.
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
- **D-43**: `074-v10-core-memory-dynamics` is the first acceptable theory-to-runtime tranche after the v10 theory docs: it must stay executable, bounded, and explanation-first, using surrogate dynamic signals rather than reopening a simulator or schema-heavy redesign.
- **D-44**: `075-truth-evaluation-gate` should formalize the current-truth spotlight benchmark as a governed release bar for Aegis core behavior before any broader “final form” claims.
- **D-45**: `076-truth-evaluation-report` should keep the JSON artifact canonical while adding a thin Markdown report for human review and release evidence.
- **D-46**: `078-grouped-truth-thresholds` should enforce per-category pass/visibility bars in the existing truth gate so category regressions fail fast.
- **D-47**: `079-truth-scenario-catalog-and-trend` should add machine-readable scenario meaning plus optional before-vs-current trend rendering without replacing the existing benchmark/gate flow.
- **D-48**: `080-truth-release-evidence-bundle` should package existing truth artifacts into one manifest without changing the underlying artifact contracts.
- **D-49**: `081-aegis-gauntlet` should remain deterministic and artifact-first: it should stress Aegis broadly without requiring long-lived infrastructure.
- **D-50**: `082-gauntlet-escalation` should stay deterministic while increasing pressure in three areas first: scale, isolation, and recovery.
- **D-51**: `083-gauntlet-operations-pressure` should focus next on backup/restore and rebuild-heavy pressure before any broader chaos or soak layer.
- **D-52**: `084-ingest-pressure-gauntlet` should treat repeated `ingest_rejected/no_op` signals as something to measure explicitly rather than hand-wave.
- **D-53**: `085-admission-policy-investigation` should explain write-path rejection/no-op behavior before any policy tuning is attempted.
- **D-54**: `086-ingest-policy-readiness` should only close the current admission branch if weak repetitive writes are explained by protective policy while strong distinct writes still admit cleanly.
- **D-55**: `090-truthkeep-vnext-architecture-consolidation` should define the target module layout, beast-taxonomy boundaries, and compatibility-first migration path before any broad architecture refactor begins.
- **D-56**: `091-prehistoric-supreme-core-system` should formalize the beast system only through the chain `biology -> mathematics -> architecture`; prehistoric metaphor may inspire algorithms, but math and verification remain authoritative.
- **D-57**: `092-prehistoric-core-execution-priorities` should operationalize the prehistoric core in a bounded order, starting with beasts that fit TruthKeep's current moat and current proof stack best.
- **D-58**: `093-prehistoric-tranche-two-ingest-and-explainability` should stay bounded to ingest richness, canonicalization stability, and explainability output instead of reopening broad retrieval redesign.
- **D-59**: `094-prehistoric-tranche-three-retrieval-dominance` should deepen retrieval through lexical, semantic, and graph seams without reopening unbounded traversal or broad search rewrites.
- **D-60**: `095-prehistoric-tranche-four-ingest-taxonomy` should deepen extraction, classification, and taxonomy cleanup without reopening broad ingest architecture.
- **D-61**: `096-prehistoric-tranche-five-hygiene-resilience` should deepen rebuild, retirement, and consolidation behavior through measurable hygiene signals rather than broad lifecycle redesign.
- **D-62**: `097-prehistoric-tranche-six-storage-topology` should deepen storage visibility through compaction, locality, and topology signals without reopening schema design.
- **D-63**: `098-prehistoric-tranche-seven-scope-identity-boundary` should close the prehistoric rollout through scope, profile, and boundary signals rather than opening new subsystem breadth.
- **D-64**: `099-prehistoric-depth-elevation-roadmap` should classify all 23 beasts by actual runtime depth before opening any further deepening tranches.
- **D-65**: `100-prehistoric-depth-elevation-tranche-one` should deepen the first three highest-ROI signal-surface beasts through existing storage/operator/showcase seams before opening any broader runtime redesign.
- **D-66**: After `100-prehistoric-depth-elevation-tranche-one`, the next deepening work should target the remaining weak prehistoric seams rather than reopening already-deepened beasts.
- **D-67**: `101-prehistoric-depth-elevation-tranche-two` should deepen topology, identity, and boundary surfaces through existing UX and contract seams before any broader enforcement redesign.
- **D-68**: `102-prehistoric-depth-elevation-tranche-three` should deepen rebuild, retirement guidance, and consolidation visibility through existing runtime seams before any broader lifecycle redesign.
- **D-69**: `103-prehistoric-depth-elevation-tranche-four` should deepen capture-span and retrieval-predator visibility through existing ingest, spotlight, and showcase seams before any broader retrieval redesign.

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
- Treat `062-v4-to-v10-migration-roadmap` as the next architecture strategy layer after the productization wave; use it to open `063-evidence-log-foundation` rather than jumping straight to a rewrite.
- Treat `063-evidence-log-foundation` as implemented foundation work rather than open planning.
- Treat `064-internal-evidence-consumption` as implemented evidence-readiness work rather than open planning.
- Treat `065-promotion-gate-primitives` as implemented admission-foundation work rather than open planning.
- Treat `066-formal-memory-state-machine` as implemented state-foundation work rather than open planning.
- Treat `067-state-aware-internal-retrieval` as implemented retrieval-readiness work rather than open planning.
- Treat `068-state-aware-governed-operations` as implemented and validated architecture work after `067`.
- Use `068` to make governance and operational internals state-aware without collapsing into a broad autonomy rewrite by default.
- Use `.planning/PRODUCTION-EXCELLENCE-ROADMAP.md` to sequence the next reliability work after `068`, starting with acceptance/regression hardening before observability and release-discipline work.
- Treat `074-v10-core-memory-dynamics` as the next executable architecture slice when opening the v10 theory documents: bounded evidence/support/conflict/trust/readiness scoring and one hysteresis gate are in scope; simulator-first work is not.
- Treat `075-truth-evaluation-gate` as the current proof-and-discipline slice for protecting spotlight truth behavior with one explicit pass/fail release gate.
- Treat `076-truth-evaluation-report` as the current release-evidence slice so spotlight truth behavior is easy to review, share, and archive.
- Treat `078-grouped-truth-thresholds` as the current release-discipline slice so grouped truth categories each clear their own governed bar.
- Treat `079-truth-scenario-catalog-and-trend` as the current release-evidence slice so truth reports explain scenario intent and movement over time.
- Treat `080-truth-release-evidence-bundle` as the current release-packaging slice so benchmark, gate, and report outputs can be consumed from one manifest.
- Treat `081-aegis-gauntlet` as the current stress-validation slice for determining whether Aegis behaves like a more complete memory product under mixed pressure.
- Treat `082-gauntlet-escalation` as the current stress-hardening slice for deciding whether the same quality survives under harsher product-like conditions.
- Treat `083-gauntlet-operations-pressure` as the current stress-operations slice for judging whether Aegis recovery paths behave like a trustworthy product.
- Treat `084-ingest-pressure-gauntlet` as the current stress-write-path slice for judging whether Aegis admission behavior under repetitive writes looks healthy.
- Treat `085-admission-policy-investigation` as the current diagnostic slice for turning that judgment into a clear technical explanation.
- Treat `090-truthkeep-vnext-architecture-consolidation` as the next architecture-definition slice for shaping the next TruthKeep refactor around compact runtime modules, internal beast taxonomy, and a compatibility-first migration path.
- Treat `091-prehistoric-supreme-core-system` as the next core-language slice for defining all 23 beasts as formal internal core forces instead of loose mythology.
- Treat `092-prehistoric-core-execution-priorities` as the next execution-order slice for deciding which prehistoric beasts should land in code first.
- Treat `093-prehistoric-tranche-two-ingest-and-explainability` as the next bounded prehistoric execution slice for landing Meganeura, Ammonite, and Paraceratherium in already-provable seams.
- Treat `094-prehistoric-tranche-three-retrieval-dominance` as the next bounded prehistoric execution slice for landing Utahraptor, Basilosaurus, and Pterodactyl in retrieval seams.
- Treat `095-prehistoric-tranche-four-ingest-taxonomy` as the next bounded prehistoric execution slice for landing Dimetrodon, Chalicotherium, and Oviraptor in write-path and taxonomy seams.
- Treat `096-prehistoric-tranche-five-hygiene-resilience` as the next bounded prehistoric execution slice for landing Diplocaulus, Smilodon, and Glyptodon in hygiene seams.
- Treat `097-prehistoric-tranche-six-storage-topology` as the next bounded prehistoric execution slice for landing Deinosuchus, Titanoboa, and Megarachne in storage seams.
- Treat `098-prehistoric-tranche-seven-scope-identity-boundary` as the final bounded prehistoric execution slice for landing Argentinosaurus, Dire Wolf, and Megatherium in runtime seams.
- Treat `099-prehistoric-depth-elevation-roadmap` as the next bounded post-rollout audit slice for deciding which beasts should be deepened first now that all 23 are executable.
- Treat `100-prehistoric-depth-elevation-tranche-one` as the next bounded deepening slice for turning Argentinosaurus, Deinosuchus, and Titanoboa into practical runtime surfaces.
- Treat `100-prehistoric-depth-elevation-tranche-one` as landed once showcase/storage surfaces and full-suite verification confirm those three beasts are no longer isolated reports.
- Treat `101-prehistoric-depth-elevation-tranche-two` as the next bounded deepening slice for moving Megarachne, Dire Wolf, and Megatherium into stronger runtime leverage.
- Treat `102-prehistoric-depth-elevation-tranche-three` as the next bounded deepening slice for moving Diplocaulus, Smilodon, and Glyptodon into stronger runtime leverage.
- Treat `103-prehistoric-depth-elevation-tranche-four` as the next bounded deepening slice for moving Meganeura, Utahraptor, and Basilosaurus into stronger runtime leverage.
- Treat `104-prehistoric-depth-elevation-tranche-five` as the next bounded deepening slice for moving Pterodactyl and Oviraptor into stronger runtime leverage.
- Treat `105-prehistoric-depth-elevation-tranche-six` as the next bounded deepening slice for moving Dimetrodon, Chalicotherium, and Ammonite into stronger runtime leverage.
- Treat `106-prehistoric-depth-elevation-tranche-seven` as the next bounded deepening slice for moving Meganeura, Paraceratherium, and Utahraptor into stronger runtime leverage.
- Treat `107-prehistoric-depth-elevation-tranche-eight` as the next bounded deepening slice for moving Chalicotherium, Ammonite, and Oviraptor into stronger runtime leverage.
- Treat `108-prehistoric-depth-elevation-tranche-nine` as the next bounded deepening slice for moving Paraceratherium, Basilosaurus, and Pterodactyl into stronger runtime leverage.
- Treat `109-prehistoric-depth-audit-sync` as the bounded synchronization slice for reclassifying prehistoric runtime depth after tranches 104 through 108.
- Treat `110-prehistoric-judged-recall-pressure` as the bounded deepening slice for moving key retrieval beasts into post-governance judged recall pressure.
- Treat `111-prehistoric-core-closure-tranche-one` as the bounded closure slice for moving Meganeura, Dimetrodon, and Argentinosaurus into direct decision-path influence.
- Treat `112-prehistoric-oviraptor-drift-guard` as the bounded closure slice for moving Oviraptor from taxonomy guidance into ingest and policy drift protection.
- Treat future work as net-new scope beyond the current local-first consumer-complete milestone rather than unfinished baseline completion work.


- Treat 113-prehistoric-core-completion-gate as the bounded closure slice for formally declaring the prehistoric rollout complete through a synced depth map and auditable gate.


- 114-prehistoric-total-core-deep-closure: completed, 23/23 core-deep, 100 tests passing.


- 115-turboquant-for-truthkeep-r-and-d: completed research phase, prototype candidate tier recommended next.


- 116-compressed-candidate-tier-spike: completed prototype, compressed prefilter integrated, 101 tests passing.


- 117-compressed-candidate-tier-benchmark: completed, compressed candidate yield benchmark passes, 102 tests passing.


- 118-persistent-compressed-tier-all-in-one: completed, persistent compressed tier landed, 105 tests passing.



- 119-software-level-compressed-tier-closure: completed, software-level compressed tier closed with status surface, gate, report, completion check, and 107 tests passing.


- 120-ux-equals-core-all-in-one: completed, experience brief product shell landed with MCP/plugin/demo/report coverage, and 109 tests passing.


- 121-consumer-shell-all-in-one: completed, consumer shell landed with onboarding/app/MCP/plugin/demo/report coverage, and 111 tests passing.


- 122-dashboard-shell-final-closure: completed, unified dashboard shell landed with app/MCP/plugin/demo/report coverage, and 113 tests passing.


- 123-mathematical-hybrid-governance-closure: completed, mathematical hybrid fusion landed in retrieval and governed recall with UX surfacing, and 116 tests passing.
- 2026-04-03: Phase 124 landed. Canonical `v10_state` now persists at ingest, legacy rows can be refreshed/backfilled, and Xi(t) snapshot is exposed through operator and MCP surfaces. Full suite: 120 passed.
- 2026-04-03: Phase 125 landed. TruthKeep now has standalone CLI entry points, module entry paths, a five-minute quickstart, and a short proof flow. Full suite: 123 passed.

- 2026-04-03: Phase 126 started. TruthKeep public namespace cleanup is making TruthKeep the default package/setup/docs contract while preserving aegis_py compatibility.

- 2026-04-03: Phase 127 landed as research only. Conclusion: UX now has strong report surfaces, but still trails the core because it is report-shaped rather than workflow-shaped; the next UX wave should center a canonical workflow shell.

- 2026-04-03: Phase 128 landed. TruthKeep now has a workflow-first shell focused on remember -> inspect -> correct -> verify loops, with MCP/demo/report coverage. Full suite: 131 passed.

- 2026-04-03: Phase 129 landed. TruthKeep consumer/public surfaces now split ordinary mode from operator mode, narrowing the daily path while keeping deep inspection available. Full suite: 132 passed.

- 130-truth-transition-timeline-ux: timeline UX now uses governance events and memory state transitions to show how current truth displaced older facts.
