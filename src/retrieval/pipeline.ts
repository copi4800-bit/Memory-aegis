import type Database from "better-sqlite3";
import type { AegisConfig, MemoryNode } from "../core/models.js";
import { CONSTANTS } from "../core/models.js";
import { nowISO } from "../core/id.js";
import { fts5Search, findEntityMatches, type FtsResult } from "./fts-search.js";
import { spreadingActivation, assignInitialActivation } from "./graph-walk.js";
import { computeRetention, computeFinalScore, normalizeScores, computeScopeFit } from "./reranker.js";
import { assemblePacket, buildExplanation, type MemorySearchResult, type PacketCandidate, type RetrievalSignals } from "./packet.js";
import { findElephantOverrides } from "../cognitive/elephant.js";
import { resolveInheritedRules } from "../cognitive/sea-lion.js";
import { dedupByFingerprint } from "../cognitive/salmon.js";
import { DragonflySentry } from "./dragonfly.js";

export interface SearchOptions {
  maxResults?: number;
  minScore?: number;
  sessionKey?: string;
  scopeFilter?: string;
}

/**
 * Full 7-stage retrieval pipeline.
 *
 * Stage 1: FTS5 seed generation
 * Stage 2: Entity matching
 * Stage 3: Spreading activation (Orca)
 * Stage 4: Sea Lion inference (future)
 * Stage 5: Salmon identity (future)
 * Stage 6: Multi-signal reranking
 * Stage 7: Packetization → MemorySearchResult[]
 */
export async function executeRetrievalPipeline(
  db: Database.Database,
  query: string,
  config: AegisConfig,
  opts: SearchOptions = {},
): Promise<MemorySearchResult[]> {
  const now = nowISO();
  const maxResults = opts.maxResults ?? CONSTANTS.DEFAULT_MAX_RESULTS;
  const minScore = opts.minScore ?? CONSTANTS.DEFAULT_MIN_SCORE;

  // === Stage 1: FTS5 seed generation ===
  let ftsResults = fts5Search(db, query);

  // === Stage 1b: Meganeura Rescue (100% Local Semantic-lite Fallback) ===
  // Hardened: chỉ chạy rescue nếu FTS hit yếu hoặc trống
  if (DragonflySentry.shouldRescue(ftsResults)) {
    try {
      const meganeura = new DragonflySentry(db);
      const isMaxMemory = config?.enabledLayers?.includes("chameleon");
      const dfResults = await meganeura.rescue(query, isMaxMemory ? 15 : 5);

      if (dfResults.length > 0) {
        console.log(`🦖 Meganeura Rescue: Bắt được ${dfResults.length} kết quả bằng fuzzy-lite & nội suy (Zero Ollama).`);
        ftsResults = dfResults;
      }
    } catch (err) {
      console.warn("Meganeura Rescue failed:", err);
    }
  }

  // === Stage 2: Entity matching ===
  const entityHits = findEntityMatches(db, query);

  // Combine into initial activation map
  const seeds = assignInitialActivation(ftsResults, entityHits);

  if (seeds.size === 0) return [];

  // === Stage 2b: Elephant override check ===
  const elephantOverrides: PacketCandidate[] = [];
  if (config?.enabledLayers?.includes("elephant")) {
    const overrides = findElephantOverrides(db, query, opts.sessionKey);
    for (const node of overrides) {
      elephantOverrides.push({
        node,
        score: 1.0,
        explanation: "safety_override",
      });
    }
  }

  // === Stage 3: Spreading activation (Orca) ===
  let activated = seeds;
  if (config?.enabledLayers?.includes("orca")) {
    activated = spreadingActivation(seeds, db, {
      maxHops: config.retrievalMaxHops,
      dampingFactor: config.dampingFactor,
      activationThreshold: CONSTANTS.DEFAULT_ACTIVATION_THRESHOLD,
      maxNodes: config.maxNodesPerSearch,
      scopeFilter: opts.scopeFilter,
    });
  }

  // === Stage 4: Sea Lion inference ===
  if (config?.enabledLayers?.includes("sea-lion")) {
    for (const [nodeId] of [...activated]) {
      const inferred = resolveInheritedRules(db, nodeId);
      for (const result of inferred) {
        if (!activated.has(result.dstNodeId)) {
          activated.set(result.dstNodeId, result.confidence * 0.5);
        }
      }
    }
  }

  // === Stage 5: Salmon identity resolution ===
  if (config?.enabledLayers?.includes("salmon")) {
    activated = dedupByFingerprint(db, activated);
  }

  // === Stage 6: Scrub Jay Episodic Boosting (Scrub Jay) ===
  const episodeBoostMap = new Map<string, number>();
  // We only do this if Scrub Jay (implied by episodes table existence) is active
  // or simply always check if episode_id exists.
  const activeEpisodes = new Set<string>();
  for (const [nodeId] of activated) {
    const node = getNode(db, nodeId);
    if (node?.episode_id) activeEpisodes.add(node.episode_id);
  }

  if (activeEpisodes.size > 0) {
    const findSiblings = db.prepare(`
      SELECT id, importance FROM memory_nodes 
      WHERE episode_id = ? AND status = 'active' AND id != ?
      LIMIT 10
    `);

    for (const epId of activeEpisodes) {
      // For each active episode, find a few siblings to boost context
      const siblings = findSiblings.all(epId, "") as Array<{ id: string, importance: number }>;
      for (const sib of siblings) {
        if (!activated.has(sib.id)) {
          // Boost sibling nodes with a fraction of episode strength
          episodeBoostMap.set(sib.id, 0.4 * (sib.importance || 0.5));
        }
      }
    }
    
    // Merge boosts into activated map
    for (const [sibId, boost] of episodeBoostMap) {
      activated.set(sibId, (activated.get(sibId) || 0) + boost);
    }
  }

  // === Stage 6.1: Multi-signal reranking ===
  const candidates: PacketCandidate[] = [];
  const ftsScoreMap = new Map(ftsResults.map((r) => [r.nodeId, r.score]));
  // Track which nodes came from Dragonfly rescue
  const rescueScoreMap = new Map<string, { score: number; strategy?: string }>();
  for (const r of ftsResults) {
    if ("rescueStrategy" in r) {
      rescueScoreMap.set(r.nodeId, { score: r.score, strategy: (r as any).rescueStrategy });
    }
  }

  for (const [nodeId, activationScore] of activated) {
    const node = getNode(db, nodeId);
    if (!node || node.status !== "active") continue;

    const retention = computeRetention(node, now);
    const ftsScore = ftsScoreMap.get(nodeId) ?? 0;
    const entityOverlap = entityHits.some((h) => h.nodeId === nodeId) ? 0.8 : 0;
    const scopeFit = computeScopeFit(node.scope, opts.sessionKey);
    const procedureBonus = node.memory_type === "procedural" || node.memory_type === "tool_artifact" ? 0.5 : 0;
    const episodeBoost = episodeBoostMap.get(nodeId) ?? 0;
    const rescueInfo = rescueScoreMap.get(nodeId);

    const finalScore = computeFinalScore(node, {
      ftsScore,
      activationScore,
      entityOverlap,
      retention,
      scopeFit,
      procedureBonus,
      overridePriority: node.override_priority,
    });

    // Phase 4.3: Populate retrieval signals for explainability
    const signals: RetrievalSignals = {
      lexicalHit: rescueInfo ? 0 : ftsScore,
      semanticRescue: rescueInfo?.score ?? 0,
      graphActivation: seeds.has(nodeId) ? 0 : activationScore,
      procedureBonus,
      episodeBoost,
      policyPriority: node.override_priority,
      entityOverlap,
      retention,
      scopeFit,
      rescueStrategy: rescueInfo?.strategy as RetrievalSignals["rescueStrategy"],
    };

    const candidate: PacketCandidate = {
      node,
      score: finalScore,
      explanation: "",
      hopCount: seeds.has(nodeId) ? 0 : undefined,
      matchedEntities: entityHits
        .filter((h) => h.nodeId === nodeId)
        .map(() => node.canonical_subject ?? ""),
      signals,
    };
    candidate.explanation = buildExplanation(candidate);
    candidates.push(candidate);
  }

  // Sort by score descending
  candidates.sort((a, b) => b.score - a.score);

  // Normalize scores to [0, 1]
  const rawScores = candidates.map((c) => c.score);
  const normalizedScores = normalizeScores(rawScores);
  for (let i = 0; i < candidates.length; i++) {
    candidates[i].score = normalizedScores[i];
  }

  // Filter by minScore
  const filtered = candidates.filter((c) => c.score >= minScore);

  // === Stage 7: Packetization ===
  const packet = assemblePacket(filtered, elephantOverrides, maxResults);

  // Post-retrieval: Update access metadata
  const touchNode = db.prepare(`
    UPDATE memory_nodes
    SET last_access_at = ?, recall_count = recall_count + 1, updated_at = ?
    WHERE id = ?
  `);

  const findNodeByPath = db.prepare(
    "SELECT id FROM memory_nodes WHERE source_path = ? AND status = 'active' LIMIT 1",
  );

  const touchTxn = db.transaction(() => {
    for (const result of packet) {
      const nodeId = extractNodeId(result.path);
      if (nodeId) {
        touchNode.run(now, now, nodeId);
      } else {
        // File-backed path — look up node by source_path
        const row = findNodeByPath.get(result.path) as { id: string } | undefined;
        if (row) touchNode.run(now, now, row.id);
      }
    }
  });
  touchTxn();

  return packet;
}

// --- Internal Helpers ---

function getNode(db: Database.Database, nodeId: string): MemoryNode | null {
  return (
    (db.prepare("SELECT * FROM memory_nodes WHERE id = ?").get(nodeId) as MemoryNode | undefined) ??
    null
  );
}

function extractNodeId(path: string): string | null {
  if (path.startsWith("aegis://")) {
    const parts = path.split("/");
    return parts[parts.length - 1] ?? null;
  }
  return null;
}
