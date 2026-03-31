# Roadmap

`.planning/ROADMAP.md` is a coordination summary only.

## Current Milestone Position

The current local-first completion wave is closed.

- `046-consumer-ready-checklist` defined the governed readiness bar.
- `047-consumer-onboarding` landed the Python-owned first-run setup path.
- `048-consumer-everyday-surface` made default status and everyday output plain-language first.
- `049-consumer-recovery-trust` made backup, restore, and doctor surfaces trust-oriented for ordinary users.
- `050-consumer-closure-review` recorded the governing `GO` decision.
- `051-guided-host-integration` closed the final host-surface and TS-era ambiguity blockers.
- `054-default-surface-consistency` tightens the same bounded consumer path by removing residual default-surface drift such as `memory_setup` publishing inconsistently across source, MCP, and shipped artifacts.
- `055-product-adoption-roadmap` defines the next product-facing strategy layer: steal the best tactics from Mem0, NeuralMemory, and strong RAG systems without weakening Aegis core discipline.
- `056-time-to-first-value` is the first execution slice from that roadmap, focused on beginner quickstart, setup, and first remember/recall success.
- `057-product-storytelling` is the first Tranche B slice, focused on making the README easier to understand and easier to repeat as a product story.
- `058-demo-and-benchmark-presentation` completes the next Tranche B slice, adding one runnable demo and one benchmark summary that are easy to point to.
- `059-packaging-polish` is the next product-polish slice, focused on making the shipped bundle and package feel unpack-and-try friendly.
- `060-integration-story` is the current integration/polish slice, focused on making the thin-host service boundary easy to demo and easy to copy.
- `061-citation-and-grounding-story` is the tranche-closing trust slice, focused on making provenance, ranking reasons, and trust shape easy to demo and easy to explain.
- `062-v4-to-v7-migration-roadmap` is the next architectural strategy layer, turning `/home/hali/.openclaw/11.md` into an executable migration path instead of a rewrite note.
- `063-evidence-log-foundation` is the first implementation tranche from that roadmap, focused on immutable evidence storage and memory-to-evidence linkage without breaking the current runtime surface. It is now implemented and validated.
- `064-internal-evidence-consumption` is the next narrow tranche after `063`, focused on making evidence consumable through internal runtime helpers without yet opening admission gates, promotion validators, or a richer state model. It is now implemented and validated.
- `065-promotion-gate-primitives` is the next narrow tranche after `064`, focused on adding candidate-first promotion checks and bounded admission decisions before the later richer state-machine slice. It is now implemented and validated.
- `066-formal-memory-state-machine` is the next narrow tranche after `065`, focused on mapping admission outcomes into explicit internal states before later retrieval consumption work. It is now implemented and validated.
- `067-state-aware-internal-retrieval` is the next narrow tranche after `066`, focused on bounded retrieval and policy shaping that consumes `admission_state` without attempting a broad retrieval rewrite. It is now implemented and validated.
- `068-state-aware-governed-operations` is the next distinct tranche after `067`, focused on explanation-first governance and background-operation internals that consume state, promotion, and evidence together without broadening into a full autonomy rewrite. It is now implemented and validated.
- `074-v8-core-memory-dynamics` is the next bounded theory-to-runtime tranche after the current production-hardening wave, focused on executable v8-core signals, dynamic retrieval shaping, and one minimal hysteresis gate rather than a simulator-first redesign. It is now implemented as the first executable slice of the v8 theory documents.
- `PRODUCTION-EXCELLENCE-ROADMAP.md` is the current derivative execution note for turning the already-working v7 runtime into a more predictable, observable, and recoverable production system without reopening broad capability scope.
- `072-production-discipline` is the bounded final tranche in that production-excellence wave, focused on release gate, soak practice, rollback, and runbooks rather than further capability or planning sprawl.

## Governing Outcome

- Aegis v4 may now be called **consumer-complete for the current local-first deployment class**.
- This claim is governed by `specs/046-consumer-ready-checklist/plan.md` and `specs/050-consumer-closure-review/plan.md`.
- This file is derivative only. If it disagrees with `specs/*`, `specs/*` wins.

## Current Priority

1. Preserve the Python-owned runtime boundary.
2. Avoid reopening retired TypeScript engine paths.
3. Keep the ordinary-user default surface narrow and explicit.
4. Treat new work as a new milestone, not as unfinished completion work for the current local-first baseline.
5. Prefer small consistency slices that keep the shipped default surface aligned with the Python-owned contract.
6. Use `.planning/AEGIS-ADOPTION-ROADMAP.md` to decide which product-facing improvements to pursue next.
7. Treat `056-time-to-first-value` as the next newcomer-facing implementation target.
8. Treat `057-product-storytelling` as the next comprehension/polish target after first value.
9. Treat `058-demo-and-benchmark-presentation` as the completed demoability/proof target for the current Tranche B wave.
10. Treat `059-packaging-polish` as the current shipping/presentation target.
11. Treat `060-integration-story` as the current integrator-facing polish target.
12. Treat `061-citation-and-grounding-story` as the tranche-closing trust target.
13. Treat `062-v4-to-v7-migration-roadmap` as the next architecture-planning target after the current productization wave closes.
14. Treat `063-evidence-log-foundation` as the landed storage foundation for the v4-to-v7 path.
15. Treat `064-internal-evidence-consumption` as landed evidence-readiness work after `063`.
16. Treat `065-promotion-gate-primitives` as landed admission-foundation work after `064`.
17. Treat `066-formal-memory-state-machine` as landed state-foundation work after `065`.
18. Treat `067-state-aware-internal-retrieval` as landed retrieval-readiness work after `066`.
19. Treat `068-state-aware-governed-operations` as implemented and validated architecture work after `067`.
20. Keep the next architecture slice narrower than a full v7 rewrite: only broaden autonomy if bounded state-aware governance proves insufficient.
21. Treat `.planning/PRODUCTION-EXCELLENCE-ROADMAP.md` as the execution order for post-capability hardening work: hardening first, observability second, production discipline third.
22. Treat `074-v8-core-memory-dynamics` as the bounded post-hardening architecture slice for executable memory dynamics rather than opening a theory-heavy simulator rewrite.

## Residual Notes

- Advanced operator and integration tools remain available, but they are no longer the default ordinary-user path.
- Any broader future claim should be framed explicitly as a new deployment-class or integration-class milestone.
- The next product-facing work should cite the adoption roadmap rather than adding polish work ad hoc.
- The immediate product-facing tranche is Tranche A: beginner time to first value.
- The immediate Tranche B slice is product storytelling and overview clarity.
- The current Tranche B demo/proof slice is demo and benchmark presentation, now grounded in repo-native scripts and tests.
- The current packaging-polish slice is making release artifacts reflect the same newcomer path as the repo docs.
- The current integration-story slice is making the thin-host service boundary easier to copy and prove.
- The current tranche-closing trust slice is making grounded recall easy to show through provenance and explainability output.
- The next architecture layer after productization is the v4-to-v7 migration roadmap, with `063-evidence-log-foundation` as the likely first implementation tranche.
- The active architecture tranche `063-evidence-log-foundation` is now landed and validated, establishing immutable evidence storage before any admission/state-machine redesign.
- The follow-on architecture tranche `064-internal-evidence-consumption` is now landed and validated, adding internal evidence lookup and coverage primitives before any promotion-gate or state-machine redesign.
- The follow-on architecture tranche `065-promotion-gate-primitives` is now landed and validated, adding candidate-first admission seams before the later richer state-machine redesign.
- The follow-on architecture tranche `066-formal-memory-state-machine` is now landed and validated, formalizing admission-aware states before later retrieval consumption work.
- The follow-on architecture tranche `067-state-aware-internal-retrieval` is now landed and validated, letting bounded retrieval and policy internals consume `admission_state` before any broader retrieval redesign.
- The next active architecture tranche after `067` was `068-state-aware-governed-operations`, which is now implemented and validated and lets governance and background-operation internals consume state, promotion, and evidence together before any broader autonomy redesign.
- Post-capability work should now prefer production-excellence slices over new feature breadth: correctness, observability, and recovery discipline should outrank speculative new tools.
- The next executable theory-derived slice is `074-v8-core-memory-dynamics`, which lands bounded evidence/support/conflict/trust/readiness scoring and one minimal hysteresis gate without reopening schema-heavy simulator work.
