/**
 * Memory Aegis v4 — OpenClaw Plugin Entry Point.
 */

export { AegisMemoryManager, closeAllManagers } from "./aegis-manager.js";
export type { AegisConfig, CognitiveLayers, MemoryNode, MemoryEdge, TaxonomyCategory } from "./core/models.js";
export { DEFAULT_AEGIS_CONFIG, TAXONOMY_V1, TAXONOMY_CATEGORIES, TAXONOMY_MIGRATION_MAP } from "./core/models.js";

// Hooks
export { createSessionHooks } from "./hooks/session-hook.js";
export { createToolHooks } from "./hooks/tool-hook.js";
export { createMessageHooks } from "./hooks/message-hook.js";

// Cognitive layers (advanced usage)
export { microChunk, extractLandmarks } from "./cognitive/nutcracker.js";
export { resolveEntities, rebuildCoOccurrenceEdges, prewarm, consolidateSession } from "./cognitive/dolphin.js";
export { detectCorrection, computeBehavioralModifiers } from "./cognitive/chimpanzee.js";
export { upsertConcept, addInheritance, resolveInheritedRules, transitiveInference } from "./cognitive/sea-lion.js";
export { createPartition, subgraphSearch, autoPartition, upsertContextTexture, getContextTexture } from "./cognitive/octopus.js";
export { checkAntiRegression, findElephantOverrides, storeElephantMemory } from "./cognitive/elephant.js";
export { dedupByFingerprint, findDuplicateCluster } from "./cognitive/salmon.js";
export { BowerbirdTaxonomist, type ClassifyResult } from "./cognitive/bowerbird.js";
export { EagleEye, type EagleSummary } from "./cognitive/eagle.js";
export { ZebraFinch } from "./cognitive/zebra-finch.js";
export { WeaverBird, type BlueprintMeta } from "./cognitive/weaver-bird.js";
export { ChameleonBudgeter, type ZonePolicy, ZONE_POLICIES } from "./cognitive/chameleon.js";
export { DragonflySentry, type RescueResult } from "./retrieval/dragonfly.js";
export { type RetrievalSignals, buildDebugExplanation } from "./retrieval/packet.js";
export { Honeybee } from "./telemetry/honeybee.js";

// UX
export { buildMemoryProfile, renderProfile, type MemoryProfile } from "./ux/profile.js";
export { runOnboarding, type OnboardingResult } from "./ux/onboarding.js";

// Disaster Recovery
export { createSnapshot, exportLogicalData } from "./cognitive/tardigrade.js";
export { restoreFromSnapshot, rebuildIndexes } from "./cognitive/planarian.js";
export { BACKUP_SYNC_TOOLS } from "./cognitive/chimpanzee-tools.js";
