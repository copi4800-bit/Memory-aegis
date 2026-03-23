/**
 * Retention dynamics — state transition evaluation.
 */

import type Database from "better-sqlite3";
import type { MemoryNode, MemoryState } from "../core/models.js";
import { CONSTANTS } from "../core/models.js";
import { computeRetention } from "../retrieval/reranker.js";
import { nowISO, daysBetween } from "../core/id.js";
import crypto from "node:crypto";

interface StateTransition {
  newState: MemoryState;
  reason: string;
}

/**
 * Evaluate whether a node should transition to a different memory state.
 */
export function evaluateStateTransition(
  node: MemoryNode,
  retention: number,
): StateTransition | null {
  switch (node.memory_state) {
    case "volatile": {
      // Promote to stable
      if (
        node.recall_count >= CONSTANTS.STABLE_RECALL_THRESHOLD &&
        node.stability_score >= CONSTANTS.STABLE_STABILITY_THRESHOLD &&
        node.interference_score < CONSTANTS.STABLE_INTERFERENCE_MAX
      ) {
        return { newState: "stable", reason: "sufficient_reinforcement" };
      }
      // Suppress if decayed
      if (retention < CONSTANTS.VOLATILE_SUPPRESS_THRESHOLD) {
        return { newState: "suppressed", reason: "decay_below_threshold" };
      }
      break;
    }

    case "stable": {
      // Promote to crystallized
      if (
        node.recall_count >= CONSTANTS.CRYSTALLIZE_RECALL_THRESHOLD &&
        node.interference_score < CONSTANTS.CRYSTALLIZE_INTERFERENCE_MAX &&
        CONSTANTS.CRYSTALLIZATION_ELIGIBLE_TYPES.includes(node.memory_type)
      ) {
        return { newState: "crystallized", reason: "crystallization_criteria_met" };
      }
      // Demote if interference too high
      if (node.interference_score >= CONSTANTS.STABLE_INTERFERENCE_DEMOTE) {
        return { newState: "volatile", reason: "interference_demote" };
      }
      break;
    }

    case "crystallized":
      // Nearly permanent — no automatic transitions
      return null;

    case "suppressed": {
      // Reactivate if recalled again
      if (retention > CONSTANTS.REACTIVATE_THRESHOLD) {
        return { newState: "volatile", reason: "reactivated_by_recall" };
      }
      break;
    }
  }

  return null;
}

/**
 * Run state transitions for all active nodes.
 * Returns the number of nodes that changed state.
 */
export function runStateTransitions(db: Database.Database): number {
  const now = nowISO();
  let changed = 0;
  const BATCH_SIZE = 500;

  const selectBatch = db.prepare(`
    SELECT id, memory_state, memory_type, importance, salience, override_priority,
           recall_count, frequency_count, first_seen_at, last_seen_at, last_access_at,
           created_at, base_decay_rate, interference_score, stability_score
    FROM memory_nodes
    WHERE status = 'active' AND memory_state != 'archived'
    ORDER BY id
    LIMIT ${BATCH_SIZE} OFFSET ?
  `);

  const updateState = db.prepare(`
    UPDATE memory_nodes
    SET memory_state = ?, updated_at = ?, crystallized_at = CASE WHEN ? = 'crystallized' THEN ? ELSE crystallized_at END
    WHERE id = ?
  `);

  const insertEvent = db.prepare(`
    INSERT INTO memory_events (id, event_type, node_id, payload_json, created_at)
    VALUES (?, 'state_transition', ?, ?, ?)
  `);

  let offset = 0;
  let batch: MemoryNode[] = [];

  do {
    batch = selectBatch.all(offset) as MemoryNode[];

    const txn = db.transaction(() => {
      for (const node of batch) {
        const retention = computeRetention(node, now);
        const transition = evaluateStateTransition(node, retention);

        if (transition) {
          updateState.run(transition.newState, now, transition.newState, now, node.id);
          insertEvent.run(
            crypto.randomUUID(), node.id,
            JSON.stringify({ from: node.memory_state, to: transition.newState, reason: transition.reason }),
            now,
          );
          changed++;
        }
      }
    });

    txn();
    offset += BATCH_SIZE;
  } while (batch.length === BATCH_SIZE);

  return changed;
}

/**
 * Archive memories that have been suppressed for too long.
 */
export function archiveOldSuppressed(db: Database.Database): number {
  const now = nowISO();
  const cutoff = new Date(Date.now() - CONSTANTS.ARCHIVE_AFTER_DAYS * 24 * 60 * 60 * 1000).toISOString();

  const result = db.prepare(`
    UPDATE memory_nodes
    SET memory_state = 'archived', updated_at = ?
    WHERE memory_state = 'suppressed' AND updated_at < ?
  `).run(now, cutoff);

  return result.changes;
}
