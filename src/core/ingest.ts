import type Database from "better-sqlite3";
import { newId, nowISO } from "./id.js";
import { computeFingerprints, FINGERPRINT_VERSION } from "./fingerprint.js";
import { extractEntities, type ExtractedEntity } from "./entities.js";
import type { MemoryType } from "./models.js";

// --- Path Sanitization ---

/**
 * Normalize sourcePath to prevent traversal sequences from confusing classification.
 * Does NOT perform file I/O — only normalizes for pattern matching.
 */
function sanitizeSourcePath(sourcePath: string): string {
  return sourcePath
    .replace(/\\/g, "/")
    .split("/")
    .filter(segment => segment !== ".." && segment !== ".")
    .join("/");
}

// --- File Type Inference ---

interface IngestOptions {
  sourcePath: string;
  content: string;
  source: "memory" | "sessions";
  scope?: string;
  startLine?: number;
  endLine?: number;
}

/**
 * Infer memory_type from file path pattern.
 */
function inferMemoryType(sourcePath: string, source: string): MemoryType {
  const lower = sourcePath.toLowerCase();

  if (lower === "memory.md") return "identity";
  if (/memory\/\d{4}-\d{2}-\d{2}\.md$/.test(lower)) return "episodic";
  if (/memory\//.test(lower)) return "semantic_fact";
  if (source === "sessions") return "episodic";
  if (/\.(rule|policy)$/i.test(lower)) return "rule";
  if (/\.(proc|procedure)$/i.test(lower)) return "procedural";

  return "semantic_fact";
}

/**
 * Infer scope from source and path.
 */
function inferScope(sourcePath: string, source: string, explicit?: string): string {
  if (explicit) return explicit;
  if (source === "sessions") return "session";
  if (sourcePath.toLowerCase() === "memory.md") return "global";
  return "user";
}

// --- Dedup Check ---

interface DedupResult {
  action: "reuse" | "drift_detected" | "create_new";
  targetNodeId?: string;
  baselineFingerprintId?: string;
  matchType: "exact" | "normalized" | "structure" | "none";
}

function checkDedup(
  db: Database.Database,
  rawHash: string,
  normalizedHash: string,
  structureHash: string,
): DedupResult {
  // Exact match
  const exact = db.prepare(
    "SELECT node_id FROM fingerprints WHERE raw_hash = ?",
  ).get(rawHash) as { node_id: string } | undefined;

  if (exact) {
    return { action: "reuse", targetNodeId: exact.node_id, matchType: "exact" };
  }

  // Normalized match
  const normalized = db.prepare(
    "SELECT node_id FROM fingerprints WHERE normalized_hash = ?",
  ).get(normalizedHash) as { node_id: string } | undefined;

  if (normalized) {
    return { action: "reuse", targetNodeId: normalized.node_id, matchType: "normalized" };
  }

  // Structure match (drift)
  const structure = db.prepare(
    "SELECT node_id, id as fingerprint_id FROM fingerprints WHERE structure_hash = ? AND raw_hash != ?",
  ).get(structureHash, rawHash) as { node_id: string; fingerprint_id: string } | undefined;

  if (structure) {
    return {
      action: "drift_detected",
      targetNodeId: structure.node_id,
      baselineFingerprintId: structure.fingerprint_id,
      matchType: "structure",
    };
  }

  return { action: "create_new", matchType: "none" };
}

// --- Main Ingest ---

/**
 * Ingest a single content chunk into the Aegis v3 database.
 *
 * Steps:
 * 1. Compute fingerprints (Salmon)
 * 2. Check dedup — reuse existing node if match
 * 3. Create memory_node
 * 4. Create fingerprint record
 * 5. Extract entities → entities + entity_aliases
 * 6. Build co-occurrence edges
 * 7. Log ingest event
 *
 * Returns the node ID (new or reused).
 */
export function ingestChunk(db: Database.Database, opts: IngestOptions): string {
  const now = nowISO();
  const cleanPath = sanitizeSourcePath(opts.sourcePath);
  const memoryType = inferMemoryType(cleanPath, opts.source);
  const scope = inferScope(cleanPath, opts.source, opts.scope);

  // Step 1: Fingerprint
  const fp = computeFingerprints(opts.content);

  // Step 2: Dedup check
  const dedup = checkDedup(db, fp.rawHash, fp.normalizedHash, fp.structureHash);

  if (dedup.action === "reuse" && dedup.targetNodeId) {
    // Update frequency and last_seen
    db.prepare(`
      UPDATE memory_nodes
      SET frequency_count = frequency_count + 1,
          last_seen_at = ?,
          updated_at = ?
      WHERE id = ?
    `).run(now, now, dedup.targetNodeId);

    // Log dedup event
    const routeId = newId();
    db.prepare(`
      INSERT INTO dedup_routes (id, fingerprint_id, scope, target_node_id, reuse_action, created_at)
      VALUES (?, (SELECT id FROM fingerprints WHERE node_id = ? LIMIT 1), ?, ?, 'reuse', ?)
    `).run(routeId, dedup.targetNodeId, scope, dedup.targetNodeId, now);

    return dedup.targetNodeId;
  }

  // Step 3: Create memory node
  const nodeId = newId();

  // Default importance by type
  const importance = memoryType === "trauma" || memoryType === "invariant" ? 1.0
    : memoryType === "identity" ? 0.7
    : memoryType === "procedural" || memoryType === "rule" ? 0.5
    : 0.3;

  db.prepare(`
    INSERT INTO memory_nodes (
      id, memory_type, content, scope, status,
      importance, salience, memory_state,
      raw_hash, normalized_hash, structure_hash, fingerprint_version,
      frequency_count, first_seen_at, last_seen_at,
      created_at, updated_at,
      source_path, source_start_line, source_end_line
    ) VALUES (
      ?, ?, ?, ?, 'active',
      ?, 0.3, 'volatile',
      ?, ?, ?, ?,
      1, ?, ?,
      ?, ?,
      ?, ?, ?
    )
  `).run(
    nodeId, memoryType, opts.content, scope,
    importance,
    fp.rawHash, fp.normalizedHash, fp.structureHash, FINGERPRINT_VERSION,
    now, now,
    now, now,
    opts.sourcePath, opts.startLine ?? 0, opts.endLine ?? 0,
  );

  // Step 4: Fingerprint record
  const fpId = newId();
  db.prepare(`
    INSERT INTO fingerprints (id, node_id, raw_hash, normalized_hash, structure_hash, fingerprint_version, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).run(fpId, nodeId, fp.rawHash, fp.normalizedHash, fp.structureHash, FINGERPRINT_VERSION, now);

  // Step 5: Handle drift detection
  if (dedup.action === "drift_detected" && dedup.targetNodeId && dedup.baselineFingerprintId) {
    const driftId = newId();
    db.prepare(`
      INSERT INTO drift_events (
        id, node_id, baseline_fingerprint_id, current_fingerprint_id,
        drift_type, severity, detected_at
      ) VALUES (?, ?, ?, ?, 'content_changed', 'medium', ?)
    `).run(driftId, dedup.targetNodeId, dedup.baselineFingerprintId, fpId, now);
  }

  // Step 6: Extract entities
  const entities = extractEntities(opts.content);
  for (const entity of entities) {
    ensureEntity(db, entity, scope, nodeId, now);
  }

  // Step 7: Log event
  db.prepare(`
    INSERT INTO memory_events (id, event_type, node_id, scope, created_at)
    VALUES (?, 'ingest', ?, ?, ?)
  `).run(newId(), nodeId, scope, now);

  return nodeId;
}

/**
 * Ensure an entity and its alias exist, link the memory node to other nodes sharing this entity.
 */
function ensureEntity(
  db: Database.Database,
  entity: ExtractedEntity,
  scope: string,
  nodeId: string,
  now: string,
): void {
  // Find or create entity by canonical name
  let entityRow = db.prepare(
    "SELECT id FROM entities WHERE canonical_name = ? COLLATE NOCASE AND (scope = ? OR scope IS NULL)",
  ).get(entity.text, scope) as { id: string } | undefined;

  if (!entityRow) {
    // Check aliases
    const aliasRow = db.prepare(`
      SELECT e.id FROM entity_aliases a
      JOIN entities e ON a.entity_id = e.id
      WHERE a.alias_text = ? COLLATE NOCASE
    `).get(entity.text) as { id: string } | undefined;

    if (aliasRow) {
      entityRow = aliasRow;
    } else {
      // Create new entity
      const entityId = newId();
      db.prepare(`
        INSERT INTO entities (id, entity_type, canonical_name, scope, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'active', ?, ?)
      `).run(entityId, entity.type, entity.text, scope, now, now);

      // Create alias (canonical name is also an alias)
      db.prepare(`
        INSERT OR IGNORE INTO entity_aliases (id, entity_id, alias_text, alias_kind, confidence, created_at, updated_at)
        VALUES (?, ?, ?, 'canonical', ?, ?, ?)
      `).run(newId(), entityId, entity.text, entity.confidence, now, now);

      entityRow = { id: entityId };
    }
  }

  // Find other nodes that already mention this entity via mentions_entity self-edges
  const mentionEdges = db.prepare(`
    SELECT DISTINCT src_node_id FROM memory_edges
    WHERE edge_type = 'mentions_entity'
      AND status = 'active'
      AND json_extract(extension_json, '$.entity_id') = ?
      AND src_node_id != ?
  `).all(entityRow.id, nodeId) as Array<{ src_node_id: string }>;

  const relatedNodeIds = new Set(mentionEdges.map((r) => r.src_node_id));

  // Create bidirectional co-occurrence edges to related nodes
  for (const relatedId of relatedNodeIds) {
    // Check edge doesn't already exist
    const existing = db.prepare(`
      SELECT id FROM memory_edges
      WHERE ((src_node_id = ? AND dst_node_id = ?) OR (src_node_id = ? AND dst_node_id = ?))
        AND edge_type = 'co_entity'
        AND json_extract(extension_json, '$.entity_id') = ?
    `).get(nodeId, relatedId, relatedId, nodeId, entityRow.id) as { id: string } | undefined;

    if (!existing) {
      db.prepare(`
        INSERT INTO memory_edges (
          id, src_node_id, dst_node_id, edge_type, weight, confidence,
          scope, status, coactivation_count, created_at, updated_at, extension_json
        ) VALUES (?, ?, ?, 'co_entity', ?, ?, ?, 'active', 1, ?, ?, ?)
      `).run(
        newId(), nodeId, relatedId,
        entity.confidence * 0.5,
        entity.confidence,
        scope, now, now,
        JSON.stringify({ entity_id: entityRow.id, entity_name: entity.text }),
      );
    }
  }

  // Also create a node-to-entity reference edge (for entity lookups)
  db.prepare(`
    INSERT OR IGNORE INTO memory_edges (
      id, src_node_id, dst_node_id, edge_type, weight, confidence,
      scope, status, coactivation_count, created_at, updated_at, extension_json
    ) VALUES (?, ?, ?, 'mentions_entity', ?, ?, ?, 'active', 1, ?, ?, ?)
  `).run(
    newId(), nodeId, nodeId, // self-ref with entity info
    entity.confidence * 0.5,
    entity.confidence,
    scope, now, now,
    JSON.stringify({ entity_id: entityRow.id, entity_name: entity.text }),
  );
}

/**
 * Batch ingest multiple chunks in a single transaction.
 */
export function ingestBatch(
  db: Database.Database,
  chunks: IngestOptions[],
): string[] {
  const nodeIds: string[] = [];

  const run = db.transaction(() => {
    for (const chunk of chunks) {
      nodeIds.push(ingestChunk(db, chunk));
    }
  });

  run();
  return nodeIds;
}
