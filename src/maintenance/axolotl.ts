import crypto from "node:crypto";
import type { Database } from "better-sqlite3";
import type { AegisConfig } from "../core/models.js";
import { nowISO } from "../core/id.js";

export class Axolotl {
  constructor(private db: Database, private config: AegisConfig) {}

  /**
   * Chặt đứt các nhánh dữ liệu phái sinh cũ để giải phóng không gian.
   */
  async pruneDerivedData(dryRun = false): Promise<number> {
    const jobId = crypto.randomUUID();
    const startedAt = nowISO();

    // Emit started event
    this.db.prepare(
      "INSERT INTO memory_events (id, event_type, payload_json, created_at) VALUES (?, ?, ?, datetime('now'))"
    ).run(crypto.randomUUID(), "derived_purge_started", JSON.stringify({ jobId, dryRun }));

    if (dryRun) {
      const countRow = this.db.prepare(`
        SELECT COUNT(*) as count FROM derived_relations
        WHERE confidence < 0.3 OR derivation_depth > 3
      `).get() as { count: number };
      return countRow.count;
    }

    // Track job in rebuild_jobs
    this.db.prepare(`
      INSERT INTO rebuild_jobs (id, job_type, status, started_at)
      VALUES (?, 'purge_derived', 'running', ?)
    `).run(jobId, startedAt);

    const result = this.db.prepare(`
      DELETE FROM derived_relations
      WHERE confidence < 0.3 OR derivation_depth > 3
    `).run();

    // Reset stale activation scores
    this.db.prepare(`
      UPDATE memory_nodes
      SET activation_score = 0
      WHERE last_access_at < date('now', '-30 days')
    `).run();

    const finishedAt = nowISO();
    const metrics = JSON.stringify({ deleted: result.changes });

    // Update job status
    this.db.prepare(`
      UPDATE rebuild_jobs SET status = 'completed', finished_at = ?, metrics_json = ?
      WHERE id = ?
    `).run(finishedAt, metrics, jobId);

    // Emit finished event
    this.db.prepare(
      "INSERT INTO memory_events (id, event_type, payload_json, created_at) VALUES (?, ?, ?, datetime('now'))"
    ).run(crypto.randomUUID(), "derived_purge_finished", JSON.stringify({ jobId, deleted: result.changes }));

    return result.changes;
  }

  /**
   * Tái sinh (Mọc lại) dữ liệu phái sinh từ các node quan trọng.
   */
  async regenerate(dryRun = false): Promise<{ createdRelations: number }> {
    const jobId = crypto.randomUUID();
    const startedAt = nowISO();

    // Emit started event
    this.db.prepare(
      "INSERT INTO memory_events (id, event_type, payload_json, created_at) VALUES (?, ?, ?, datetime('now'))"
    ).run(crypto.randomUUID(), "derived_rebuild_started", JSON.stringify({ jobId, dryRun }));

    if (dryRun) {
      const countRow = this.db.prepare(`
        SELECT COUNT(*) as count
        FROM memory_nodes a
        JOIN memory_nodes b ON a.canonical_subject = b.canonical_subject
        WHERE a.id < b.id
          AND a.memory_state = 'crystallized'
          AND NOT EXISTS (
            SELECT 1 FROM memory_edges
            WHERE (src_node_id = a.id AND dst_node_id = b.id)
               OR (src_node_id = b.id AND dst_node_id = a.id)
          )
      `).get() as { count: number };
      return { createdRelations: countRow.count };
    }

    // Track job
    this.db.prepare(`
      INSERT INTO rebuild_jobs (id, job_type, status, started_at)
      VALUES (?, 'rebuild_derived', 'running', ?)
    `).run(jobId, startedAt);

    const result = this.db.prepare(`
      INSERT INTO memory_edges (id, src_node_id, dst_node_id, edge_type, weight, confidence, created_at, updated_at)
      SELECT
        lower(hex(randomblob(16))),
        a.id,
        b.id,
        'auto_link',
        0.5,
        0.8,
        datetime('now'),
        datetime('now')
      FROM memory_nodes a
      JOIN memory_nodes b ON a.canonical_subject = b.canonical_subject
      WHERE a.id < b.id
        AND a.memory_state = 'crystallized'
        AND NOT EXISTS (
          SELECT 1 FROM memory_edges
          WHERE (src_node_id = a.id AND dst_node_id = b.id)
             OR (src_node_id = b.id AND dst_node_id = a.id)
        )
      LIMIT 100
    `).run();

    const finishedAt = nowISO();
    const metrics = JSON.stringify({ created: result.changes });

    this.db.prepare(`
      UPDATE rebuild_jobs SET status = 'completed', finished_at = ?, metrics_json = ?
      WHERE id = ?
    `).run(finishedAt, metrics, jobId);

    this.db.prepare(
      "INSERT INTO memory_events (id, event_type, payload_json, created_at) VALUES (?, ?, ?, datetime('now'))"
    ).run(crypto.randomUUID(), "derived_rebuild_finished", JSON.stringify({ jobId, created: result.changes }));

    return { createdRelations: result.changes };
  }
}
