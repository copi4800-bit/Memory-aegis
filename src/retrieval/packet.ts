import type { MemoryNode, MemoryType } from "../core/models.js";
import { truncate } from "../core/normalize.js";

/**
 * OpenClaw-compatible MemorySearchResult.
 * Matches the interface exactly from openclaw/src/memory/types.ts
 */
export interface MemorySearchResult {
  path: string;
  startLine: number;
  endLine: number;
  score: number;
  snippet: string;
  source: "memory" | "sessions";
  citation?: string;
}

export interface PacketCandidate {
  node: MemoryNode;
  score: number;
  explanation: string;
  hopCount?: number;
  matchedEntities?: string[];
  inferredVia?: string;
  /** Phase 4.3: Detailed signal breakdown for explainability */
  signals?: RetrievalSignals;
}

/**
 * Phase 4.3: Explainable Retrieval — full signal breakdown.
 * Mỗi result có thể giải thích gọn lý do nó được chọn.
 */
export interface RetrievalSignals {
  lexicalHit: number;       // FTS5 score
  semanticRescue: number;   // Dragonfly rescue score (0 nếu không rescue)
  graphActivation: number;  // Orca spreading activation score
  procedureBonus: number;   // Weaver Bird bonus
  episodeBoost: number;     // Scrub Jay episode sibling boost
  policyPriority: number;   // Elephant override priority
  entityOverlap: number;    // Dolphin entity matching
  retention: number;        // Memory decay/retention score
  scopeFit: number;         // Session/scope matching
  rescueStrategy?: "direct" | "synonym" | "trigram"; // Dragonfly strategy used
}

/**
 * Convert an Aegis v3 node to an OpenClaw MemorySearchResult.
 */
export function toMemorySearchResult(
  node: MemoryNode,
  score: number,
  explanation: string,
): MemorySearchResult {
  return {
    path: node.source_path ?? `aegis://${node.memory_type}/${node.id}`,
    startLine: node.source_start_line ?? 0,
    endLine: node.source_end_line ?? 0,
    score: clampScore(score),
    snippet: truncate(node.content, 500),
    source: mapScope(node.scope),
    citation: formatCitation(node, explanation),
  };
}

/**
 * Stage 7: Assemble the final memory packet.
 *
 * - Elephant overrides always come first (score = 1.0)
 * - Then ranked candidates sorted by score
 * - Deduplication by path
 * - Respects maxResults limit
 */
export function assemblePacket(
  candidates: PacketCandidate[],
  elephantOverrides: PacketCandidate[],
  maxResults: number,
): MemorySearchResult[] {
  const packet: MemorySearchResult[] = [];
  const seenPaths = new Set<string>();

  // Elephant overrides first
  for (const override of elephantOverrides) {
    if (packet.length >= maxResults) break;
    const result = toMemorySearchResult(override.node, 1.0, "safety_override");
    if (seenPaths.has(result.path)) continue;
    seenPaths.add(result.path);
    packet.push(result);
  }

  // Ranked candidates
  for (const candidate of candidates) {
    if (packet.length >= maxResults) break;
    const result = toMemorySearchResult(
      candidate.node,
      candidate.score,
      candidate.explanation,
    );
    if (seenPaths.has(result.path)) continue;
    seenPaths.add(result.path);
    packet.push(result);
  }

  return packet;
}

// --- Helpers ---

function clampScore(score: number): number {
  return Math.max(0, Math.min(1, score));
}

function mapScope(scope: string | null): "memory" | "sessions" {
  return scope === "session" ? "sessions" : "memory";
}

function formatCitation(node: MemoryNode, explanation: string): string {
  const prefix = `[${node.memory_type}]`;
  const subject = node.canonical_subject ? ` ${node.canonical_subject}` : "";
  const state = node.memory_state !== "volatile" ? ` (${node.memory_state})` : "";
  return `${prefix}${subject}${state} — ${explanation}`;
}

/**
 * Build human-readable explanation for why a result was included.
 * Phase 4.3: Enhanced with full signal breakdown.
 */
export function buildExplanation(candidate: PacketCandidate): string {
  const parts: string[] = [];
  const s = candidate.signals;

  // Safety override — highest priority
  if (candidate.node.memory_type === "trauma" || candidate.node.memory_type === "invariant") {
    parts.push("safety override");
  }

  if (s) {
    // Signal-based explanation (Phase 4.3)
    if (s.lexicalHit > 0) parts.push(`lexical hit (${s.lexicalHit.toFixed(2)})`);
    if (s.semanticRescue > 0) {
      const strat = s.rescueStrategy ? ` via ${s.rescueStrategy}` : "";
      parts.push(`semantic rescue${strat} (${s.semanticRescue.toFixed(2)})`);
    }
    if (s.graphActivation > 0 && candidate.hopCount !== undefined && candidate.hopCount > 0) {
      parts.push(`graph hop ${candidate.hopCount} (${s.graphActivation.toFixed(2)})`);
    }
    if (s.entityOverlap > 0) {
      const entities = candidate.matchedEntities?.join(", ") || "";
      parts.push(`entity${entities ? ": " + entities : ""}`);
    }
    if (s.procedureBonus > 0) parts.push("procedure bonus");
    if (s.episodeBoost > 0) parts.push(`episode boost (${s.episodeBoost.toFixed(2)})`);
    if (s.policyPriority > 0) parts.push("policy priority");
  } else {
    // Legacy fallback
    if (candidate.hopCount !== undefined && candidate.hopCount > 0) {
      parts.push(`graph activation (hop ${candidate.hopCount})`);
    }
    if (candidate.matchedEntities && candidate.matchedEntities.length > 0) {
      parts.push("entity: " + candidate.matchedEntities.join(", "));
    }
  }

  if (candidate.node.memory_state === "crystallized") {
    parts.push("crystallized");
  }
  if (candidate.inferredVia) {
    parts.push("inferred via " + candidate.inferredVia);
  }

  return parts.join("; ") || "relevance match";
}

/**
 * Phase 4.2: Debug-level explanation for power users.
 * Returns full signal table as formatted text.
 */
export function buildDebugExplanation(candidate: PacketCandidate): string {
  const s = candidate.signals;
  if (!s) return buildExplanation(candidate);

  const lines = [
    `Node: ${candidate.node.id} (${candidate.node.memory_type})`,
    `Subject: ${candidate.node.canonical_subject ?? "(none)"}`,
    `State: ${candidate.node.memory_state} | Status: ${candidate.node.status}`,
    `Final Score: ${candidate.score.toFixed(4)}`,
    `--- Signals ---`,
    `  Lexical (FTS5):      ${s.lexicalHit.toFixed(3)}`,
    `  Semantic Rescue:     ${s.semanticRescue.toFixed(3)}${s.rescueStrategy ? ` (${s.rescueStrategy})` : ""}`,
    `  Graph Activation:    ${s.graphActivation.toFixed(3)}${candidate.hopCount ? ` (hop ${candidate.hopCount})` : ""}`,
    `  Entity Overlap:      ${s.entityOverlap.toFixed(3)}`,
    `  Procedure Bonus:     ${s.procedureBonus.toFixed(3)}`,
    `  Episode Boost:       ${s.episodeBoost.toFixed(3)}`,
    `  Policy Priority:     ${s.policyPriority.toFixed(3)}`,
    `  Retention:           ${s.retention.toFixed(3)}`,
    `  Scope Fit:           ${s.scopeFit.toFixed(3)}`,
  ];

  if (candidate.matchedEntities?.length) {
    lines.push(`  Matched Entities:    ${candidate.matchedEntities.join(", ")}`);
  }

  return lines.join("\n");
}
