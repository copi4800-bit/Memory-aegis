import { type AegisConfig, type CognitiveLayers, DEFAULT_AEGIS_CONFIG } from "./models.js";

export type AegisPreset = "minimal" | "balanced" | "max-memory" | "local-safe";

export const AEGIS_PRESETS: Record<AegisPreset, Partial<AegisConfig>> = {
  "minimal": {
    enabledLayers: ["elephant", "salmon", "dragonfly"],
    maxNodesPerSearch: 20,
    retrievalMaxHops: 2,
    archiveEnabled: true,
    archiveAfterDays: 30,
  },
  "balanced": {
    ...DEFAULT_AEGIS_CONFIG,
    enabledLayers: [
      "elephant", "orca", "salmon", "dolphin",
      "dragonfly", "bowerbird", "meerkat", "zebra-finch",
    ],
  },
  "local-safe": {
    ...DEFAULT_AEGIS_CONFIG,
    enabledLayers: [
      "elephant", "orca", "salmon", "dolphin",
      "dragonfly", "bowerbird", "meerkat", "zebra-finch", "eagle",
    ],
    maxNodesPerSearch: 30,
    retrievalMaxHops: 3,
    archiveEnabled: true,
    archiveAfterDays: 60,
  },
  "max-memory": {
    ...DEFAULT_AEGIS_CONFIG,
    enabledLayers: [
      "elephant", "orca", "dolphin", "octopus", "chimpanzee",
      "sea-lion", "salmon", "nutcracker", "dragonfly",
      "bowerbird", "meerkat", "zebra-finch", "eagle",
      "scrub-jay", "weaver-bird", "chameleon",
    ] as CognitiveLayers[],
    maxNodesPerSearch: 100,
    retrievalMaxHops: 6,
  },
};

/**
 * Resolve config based on preset and user overrides.
 */
export function resolveConfig(presetName: AegisPreset = "balanced", overrides: Partial<AegisConfig> = {}): AegisConfig {
  const preset = AEGIS_PRESETS[presetName] || AEGIS_PRESETS["balanced"];
  return {
    ...DEFAULT_AEGIS_CONFIG,
    ...preset,
    ...overrides,
  };
}
