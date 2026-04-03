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
- `062-v4-to-v10-migration-roadmap` is the next architectural strategy layer, turning `/home/hali/.openclaw/11.md` into an executable migration path instead of a rewrite note.
- `063-evidence-log-foundation` is the first implementation tranche from that roadmap, focused on immutable evidence storage and memory-to-evidence linkage without breaking the current runtime surface. It is now implemented and validated.
- `064-internal-evidence-consumption` is the next narrow tranche after `063`, focused on making evidence consumable through internal runtime helpers without yet opening admission gates, promotion validators, or a richer state model. It is now implemented and validated.
- `065-promotion-gate-primitives` is the next narrow tranche after `064`, focused on adding candidate-first promotion checks and bounded admission decisions before the later richer state-machine slice. It is now implemented and validated.
- `066-formal-memory-state-machine` is the next narrow tranche after `065`, focused on mapping admission outcomes into explicit internal states before later retrieval consumption work. It is now implemented and validated.
- `067-state-aware-internal-retrieval` is the next narrow tranche after `066`, focused on bounded retrieval and policy shaping that consumes `admission_state` without attempting a broad retrieval rewrite. It is now implemented and validated.
- `068-state-aware-governed-operations` is the next distinct tranche after `067`, focused on explanation-first governance and background-operation internals that consume state, promotion, and evidence together without broadening into a full autonomy rewrite. It is now implemented and validated.
- `074-v10-core-memory-dynamics` is the next bounded theory-to-runtime tranche after the current production-hardening wave, focused on executable v10-core signals, dynamic retrieval shaping, and one minimal hysteresis gate rather than a simulator-first redesign. It is now implemented as the first executable slice of the v10 theory documents.
- `075-truth-evaluation-gate` is the next bounded proof-and-discipline slice after the current spotlight work, focused on turning current-truth benchmark evidence into a governed release gate for the Aegis memory core.
- `076-truth-evaluation-report` is the next bounded proof-and-communication slice after the truth gate, focused on turning current-truth benchmark evidence into a readable release report.
- `078-grouped-truth-thresholds` is the next bounded proof-and-discipline slice after grouped reporting, focused on enforcing per-category truth bars for the Aegis core.
- `079-truth-scenario-catalog-and-trend` is the next bounded proof-and-communication slice after grouped thresholds, focused on making truth scenarios self-describing and trend-aware across releases.
- `080-truth-release-evidence-bundle` is the next bounded proof-packaging slice after trend reporting, focused on bundling truth evaluation outputs into one release-evidence manifest.
- `081-aegis-gauntlet` is the next bounded stress-validation slice after truth evidence packaging, focused on pushing Aegis across core truth, scale, adversarial, and product-readiness scenarios.
- `082-gauntlet-escalation` is the next bounded stress-hardening slice after the first gauntlet, focused on harsher scale, isolation, and recovery pressure.
- `083-gauntlet-operations-pressure` is the next bounded stress-operations slice after gauntlet escalation, focused on backup/restore and rebuild pressure.
- `084-ingest-pressure-gauntlet` is the next bounded stress-write-path slice after operations pressure, focused on measuring admission and no-op behavior under repetitive ingest pressure.
- `085-admission-policy-investigation` is the next bounded diagnostic slice after ingest pressure, focused on explaining repeated no-op and rejection behavior in the write path.
- `086-ingest-policy-readiness` is the next bounded verdict slice after admission investigation, focused on deciding when the current ingest policy is healthy enough to close for the present deployment class.
- `087-full-core-ux-showcase` is the next bounded final-form UX slice after ingest readiness, focused on revealing the whole Aegis core story through one first-class experience.
- `088-core-showcase-html-report` is the next bounded presentation-polish slice after the full-core UX showcase, focused on turning that same story into a polished local HTML artifact.
- `089-long-horizon-memory-survival-gauntlet` is the next bounded durability slice after the polished showcase work, focused on simulated 90-day and 1-year lifecycle survival under cleanup pressure.
- `090-truthkeep-vnext-architecture-consolidation` is the next bounded architecture-clarity slice after long-horizon durability, focused on defining TruthKeep's compact long-term module structure while keeping beast lore internal and preserving the public contract.
- `091-prehistoric-supreme-core-system` is the next bounded core-language slice after vNext architecture consolidation, focused on grounding all 23 beasts in a prehistoric `biology -> mathematics -> architecture` design system.
- `092-prehistoric-core-execution-priorities` is the next bounded execution-order slice after the prehistoric core definition, focused on choosing which prehistoric beasts should become executable core behavior first.
- `093-prehistoric-tranche-two-ingest-and-explainability` is the next bounded execution slice after the first prehistoric tranche, focused on Meganeura, Ammonite, and Paraceratherium in ingest and explainability seams.
- `094-prehistoric-tranche-three-retrieval-dominance` is the next bounded prehistoric execution slice after tranche two, focused on Utahraptor, Basilosaurus, and Pterodactyl in retrieval seams.
- `095-prehistoric-tranche-four-ingest-taxonomy` is the next bounded prehistoric execution slice after tranche three, focused on Dimetrodon, Chalicotherium, and Oviraptor in ingest and taxonomy seams.
- `096-prehistoric-tranche-five-hygiene-resilience` is the next bounded prehistoric execution slice after tranche four, focused on Diplocaulus, Smilodon, and Glyptodon in hygiene seams.
- `097-prehistoric-tranche-six-storage-topology` is the next bounded prehistoric execution slice after tranche five, focused on Deinosuchus, Titanoboa, and Megarachne in storage seams.
- `098-prehistoric-tranche-seven-scope-identity-boundary` is the next bounded prehistoric execution slice after tranche six, focused on Argentinosaurus, Dire Wolf, and Megatherium in scope, profile, and boundary seams.
- `099-prehistoric-depth-elevation-roadmap` is the next bounded post-rollout audit slice after full 23-beast execution coverage, focused on classifying depth and choosing the best beasts to deepen next.
- `PRODUCTION-EXCELLENCE-ROADMAP.md` is the current derivative execution note for turning the already-working v10 runtime into a more predictable, observable, and recoverable production system without reopening broad capability scope.
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
13. Treat `062-v4-to-v10-migration-roadmap` as the next architecture-planning target after the current productization wave closes.
14. Treat `063-evidence-log-foundation` as the landed storage foundation for the v4-to-v10 path.
15. Treat `064-internal-evidence-consumption` as landed evidence-readiness work after `063`.
16. Treat `065-promotion-gate-primitives` as landed admission-foundation work after `064`.
17. Treat `066-formal-memory-state-machine` as landed state-foundation work after `065`.
18. Treat `067-state-aware-internal-retrieval` as landed retrieval-readiness work after `066`.
19. Treat `068-state-aware-governed-operations` as implemented and validated architecture work after `067`.
20. Keep the next architecture slice narrower than a full v10 rewrite: only broaden autonomy if bounded state-aware governance proves insufficient.
21. Treat `.planning/PRODUCTION-EXCELLENCE-ROADMAP.md` as the execution order for post-capability hardening work: hardening first, observability second, production discipline third.
22. Treat `074-v10-core-memory-dynamics` as the bounded post-hardening architecture slice for executable memory dynamics rather than opening a theory-heavy simulator rewrite.
23. Treat `075-truth-evaluation-gate` as the next bounded release-discipline slice for current-truth behavior after the spotlight benchmark baseline.
24. Treat `076-truth-evaluation-report` as the next bounded release-evidence slice after the truth gate so core strength is easier to review and share.
25. Treat `078-grouped-truth-thresholds` as the next bounded release-discipline slice after grouped evaluation visibility so category regressions cannot hide behind a single overall pass.
26. Treat `079-truth-scenario-catalog-and-trend` as the next bounded release-evidence slice so truth evaluation explains what each scenario proves and how it changed over time.
27. Treat `080-truth-release-evidence-bundle` as the next bounded release-packaging slice so truth evaluation output can be reviewed from one manifest.
28. Treat `081-aegis-gauntlet` as the next bounded stress-validation slice for answering how complete Aegis looks under mixed product pressure.
29. Treat `082-gauntlet-escalation` as the next bounded stress-hardening slice for deciding whether Aegis can keep its quality under harsher product-like pressure.
30. Treat `083-gauntlet-operations-pressure` as the next bounded stress-operations slice for evaluating operational recovery confidence under the same gauntlet discipline.
31. Treat `084-ingest-pressure-gauntlet` as the next bounded stress-write-path slice for deciding whether Aegis ingest behavior under pressure looks healthy or suspicious.
32. Treat `085-admission-policy-investigation` as the next bounded diagnostic slice for explaining the observed ingest-pressure behavior before changing policy.
33. Treat `090-truthkeep-vnext-architecture-consolidation` as the next bounded architecture-definition slice for turning TruthKeep's strong core into a cleaner long-term module layout before a broad refactor begins.
34. Treat `091-prehistoric-supreme-core-system` as the next bounded core-language slice for formalizing the 23-beast system through biological edge, mathematical form, and architecture ownership.
35. Treat `092-prehistoric-core-execution-priorities` as the next bounded execution-order slice for picking the first prehistoric beasts that should land in real code.
36. Treat `093-prehistoric-tranche-two-ingest-and-explainability` as the next bounded prehistoric execution slice for extending the core with capture-span, canonicalization stability, and explainable provenance.
37. Treat `094-prehistoric-tranche-three-retrieval-dominance` as the next bounded prehistoric execution slice for lexical pursuit, semantic echo, and bounded graph overview.
38. Treat `095-prehistoric-tranche-four-ingest-taxonomy` as the next bounded prehistoric execution slice for feature separation, lane ecology fit, and taxonomy ordering.
39. Treat `096-prehistoric-tranche-five-hygiene-resilience` as the next bounded prehistoric execution slice for regeneration confidence, retirement pressure, and consolidation shell strength.
40. Treat `097-prehistoric-tranche-six-storage-topology` as the next bounded prehistoric execution slice for compaction pressure, index locality, and topology strength.
41. Treat `098-prehistoric-tranche-seven-scope-identity-boundary` as the final bounded prehistoric execution slice for scope geometry, identity persistence, and boundary admissibility.
42. Treat `099-prehistoric-depth-elevation-roadmap` as the next bounded audit slice for deciding how to turn full beast coverage into deeper runtime leverage.
43. Treat `100-prehistoric-depth-elevation-tranche-one` as the next bounded deepening slice for moving Argentinosaurus, Deinosuchus, and Titanoboa into practical showcase and operator surfaces.
44. Treat `101-prehistoric-depth-elevation-tranche-two` as the next bounded deepening slice for moving Megarachne, Dire Wolf, and Megatherium into stronger showcase, profile, and contract surfaces.
45. Treat `102-prehistoric-depth-elevation-tranche-three` as the next bounded deepening slice for moving Diplocaulus, Smilodon, and Glyptodon into stronger rebuild, doctor, and showcase surfaces.
46. Treat `103-prehistoric-depth-elevation-tranche-four` as the next bounded deepening slice for moving Meganeura, Utahraptor, and Basilosaurus into stronger ingest and retrieval surfaces.
47. Treat `104-prehistoric-depth-elevation-tranche-five` as the next bounded deepening slice for moving Pterodactyl and Oviraptor into stronger spotlight and showcase surfaces.
48. Treat `105-prehistoric-depth-elevation-tranche-six` as the next bounded deepening slice for moving Dimetrodon, Chalicotherium, and Ammonite into stronger ingest and showcase surfaces.
49. Treat `106-prehistoric-depth-elevation-tranche-seven` as the next bounded deepening slice for moving Meganeura, Paraceratherium, and Utahraptor into stronger ingest and explanation surfaces.
50. Treat `107-prehistoric-depth-elevation-tranche-eight` as the next bounded deepening slice for moving Chalicotherium, Ammonite, and Oviraptor into stronger decision-path and taxonomy-guidance surfaces.
51. Treat `108-prehistoric-depth-elevation-tranche-nine` as the next bounded deepening slice for moving Paraceratherium, Basilosaurus, and Pterodactyl into stronger retrieval and explanation narratives.
52. Treat `109-prehistoric-depth-audit-sync` as the bounded synchronization slice for reclassifying prehistoric runtime depth after tranches 104 through 108.
53. Treat `110-prehistoric-judged-recall-pressure` as the bounded deepening slice for moving key retrieval beasts into post-governance judged recall pressure.
54. Treat `111-prehistoric-core-closure-tranche-one` as the bounded closure slice for moving Meganeura, Dimetrodon, and Argentinosaurus into direct decision-path influence.
55. Treat `112-prehistoric-oviraptor-drift-guard` as the bounded closure slice for moving Oviraptor from taxonomy guidance into ingest and policy drift protection.

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
- The next architecture layer after productization is the v4-to-v10 migration roadmap, with `063-evidence-log-foundation` as the likely first implementation tranche.
- The active architecture tranche `063-evidence-log-foundation` is now landed and validated, establishing immutable evidence storage before any admission/state-machine redesign.
- The follow-on architecture tranche `064-internal-evidence-consumption` is now landed and validated, adding internal evidence lookup and coverage primitives before any promotion-gate or state-machine redesign.
- The follow-on architecture tranche `065-promotion-gate-primitives` is now landed and validated, adding candidate-first admission seams before the later richer state-machine redesign.
- The follow-on architecture tranche `066-formal-memory-state-machine` is now landed and validated, formalizing admission-aware states before later retrieval consumption work.
- The follow-on architecture tranche `067-state-aware-internal-retrieval` is now landed and validated, letting bounded retrieval and policy internals consume `admission_state` before any broader retrieval redesign.
- The next active architecture tranche after `067` was `068-state-aware-governed-operations`, which is now implemented and validated and lets governance and background-operation internals consume state, promotion, and evidence together before any broader autonomy redesign.
- Post-capability work should now prefer production-excellence slices over new feature breadth: correctness, observability, and recovery discipline should outrank speculative new tools.
- The next executable theory-derived slice is `074-v10-core-memory-dynamics`, which lands bounded evidence/support/conflict/trust/readiness scoring and one minimal hysteresis gate without reopening schema-heavy simulator work.


57. Treat 113-prehistoric-core-completion-gate as the bounded closure slice for formally declaring the prehistoric rollout complete through a synced depth map and auditable gate.


- 114-prehistoric-total-core-deep-closure


- 115-turboquant-for-truthkeep-r-and-d


- 116-compressed-candidate-tier-spike


- 117-compressed-candidate-tier-benchmark


- 118-persistent-compressed-tier-all-in-one



- 119-software-level-compressed-tier-closure


- 120-ux-equals-core-all-in-one


- 121-consumer-shell-all-in-one


- 122-dashboard-shell-final-closure


- 123-mathematical-hybrid-governance-closure
- 124-v10-state-formal-fidelity: persist canonical v10 state, add backfill/refresh, and expose Xi(t) field snapshot.
- 125-distribution-closure: add standalone CLI, quickstart, and proof hub for public-first TruthKeep usage.

- 126-truthkeep-public-namespace-cleanup: make TruthKeep the default public namespace while keeping aegis_py as a compatibility layer.

- 127-ux-beyond-core-research: explain why current UX still trails the engine and define the next workflow-first UX wave.

- 128-workflow-shell-first-loop: add a workflow-first shell for remember, inspect, correct, and verify loops above the current report surfaces.

### Phase 1: ordinary operator split workflow UX

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 0
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 1 to break down)

- 129-ordinary-operator-split-workflow-ux: separate the narrow daily path from operator inspection and maintenance paths across the public TruthKeep UX surfaces.

### Phase 2: truth transition timeline UX

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 1
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 2 to break down)

- 130-truth-transition-timeline-ux: add a real truth transition timeline using winner/superseded state changes and governance pulse, then preview it inside workflow and dashboard shells.
