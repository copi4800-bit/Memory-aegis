/**
 * Background maintenance cycle.
 * Triggered by cron or manual `openclaw memory aegis maintenance`.
 */

import type Database from "better-sqlite3";
import { runStateTransitions, archiveOldSuppressed } from "./decay.js";
import { CONSTANTS, type AegisConfig } from "../core/models.js";
import { nowISO } from "../core/id.js";
import { Viper } from "../maintenance/viper.js";
import { LeafcutterAnt } from "../maintenance/leafcutter.js";
import { Axolotl } from "../maintenance/axolotl.js";
import { MeerkatSentry } from "../cognitive/meerkat.js";
import { ZebraFinch } from "../cognitive/zebra-finch.js";
import { BowerbirdTaxonomist } from "../cognitive/bowerbird.js";
import crypto from "node:crypto";

export interface MaintenanceReport {
  runId: string;
  stateTransitions: number;
  archived: number;
  ttlExpired: number;
  staleEdgesPruned: number;
  ftsOptimized: boolean;
  viperShedSkin: boolean;
  leafcutterArchivedEvents: number;
  axolotlPrunedDerived: number;
  meerkatContradictions: number;
  zebraFinchSuperseded: number;
  bowerbirdClassified: number;
  stepErrors: Record<string, string>;
}

/**
 * Run the full maintenance cycle.
 */
export async function runMaintenanceCycle(
  db: Database.Database,
  workspaceDir: string,
  config: AegisConfig
): Promise<MaintenanceReport> {
  const runId = crypto.randomUUID();
  const startedAt = nowISO();

  const report: MaintenanceReport = {
    runId,
    stateTransitions: 0,
    archived: 0,
    ttlExpired: 0,
    staleEdgesPruned: 0,
    ftsOptimized: false,
    viperShedSkin: false,
    leafcutterArchivedEvents: 0,
    axolotlPrunedDerived: 0,
    meerkatContradictions: 0,
    zebraFinchSuperseded: 0,
    bowerbirdClassified: 0,
    stepErrors: {},
  };

  db.prepare(
    "INSERT INTO memory_events (id, event_type, payload_json, created_at) VALUES (?, 'maintenance_started', ?, ?)"
  ).run(runId, JSON.stringify({ runId, startedAt }), startedAt);

  // -1. Bowerbird (Taxonomy Hardening - do it before Meerkat)
  try {
    const bowerbird = new BowerbirdTaxonomist(db);
    report.bowerbirdClassified = bowerbird.classifyAllUnknownNodes();
  } catch (err) {
    console.error("Bowerbird classification failed:", err);
    report.stepErrors["bowerbird"] = err instanceof Error ? err.message : String(err);
  }

  // 0. Meerkat Sentry (Contradiction Scanning)
  try {
    const meerkat = new MeerkatSentry(db);
    const conflicts = meerkat.scan();
    report.meerkatContradictions = conflicts.length;
  } catch (err) {
    console.error("Meerkat sentry scan failed:", err);
    report.stepErrors["meerkat"] = err instanceof Error ? err.message : String(err);
  }

  // 0.1 Zebra Finch (Semantic Consolidation / REM Sleep)
  try {
    const finch = new ZebraFinch(db);
    const result = await finch.performRemSleep();
    report.zebraFinchSuperseded = result.supersededCount;
  } catch (err) {
    console.error("Zebra Finch maintenance failed:", err);
    report.stepErrors["zebraFinch"] = err instanceof Error ? err.message : String(err);
  }

  // 1. Viper Shedding (Rotation & Hard Caps)
  try {
    const viper = new Viper(db, workspaceDir, config);
    await viper.shedSkin();
    report.viperShedSkin = true;
  } catch (err) {
    console.error("Viper maintenance failed:", err);
    report.stepErrors["viper"] = err instanceof Error ? err.message : String(err);
  }

  // 2. Leafcutter Ant (Cold Storage Archiving)
  try {
    const leafcutter = new LeafcutterAnt(db, workspaceDir, config);
    const result = await leafcutter.cleanAndArchive();
    report.leafcutterArchivedEvents = result.archivedEvents;
  } catch (err) {
    console.error("Leafcutter maintenance failed:", err);
    report.stepErrors["leafcutter"] = err instanceof Error ? err.message : String(err);
  }

  // 3. Axolotl Pruning (Derived Data Cleanup)
  try {
    const axolotl = new Axolotl(db, config);
    report.axolotlPrunedDerived = await axolotl.pruneDerivedData();
  } catch (err) {
    console.error("Axolotl maintenance failed:", err);
    report.stepErrors["axolotl"] = err instanceof Error ? err.message : String(err);
  }

  // 4. State transitions (volatile → stable → crystallized, suppress decayed)
  report.stateTransitions = runStateTransitions(db);

  // 5. Archive long-suppressed
  report.archived = archiveOldSuppressed(db);

  // 6. TTL cleanup (Nutcracker)
  const now = nowISO();
  const ttlResult = db.prepare(`
    UPDATE memory_nodes SET status = 'expired', updated_at = ?
    WHERE ttl_expires_at IS NOT NULL AND ttl_expires_at < ? AND status = 'active'
  `).run(now, now);
  report.ttlExpired = ttlResult.changes;

  // 7. Prune stale edges
  const staleCutoff = new Date(
    Date.now() - CONSTANTS.EDGE_STALE_DAYS * 24 * 60 * 60 * 1000,
  ).toISOString();

  // Weaken stale edges
  db.prepare(`
    UPDATE memory_edges
    SET weight = weight * ?, updated_at = ?
    WHERE last_activated_at < ? AND status = 'active'
  `).run(CONSTANTS.EDGE_DECAY_FACTOR, now, staleCutoff);

  // Remove near-zero weight edges
  const pruneResult = db.prepare(`
    DELETE FROM memory_edges
    WHERE weight < ? AND status = 'active' AND coactivation_count < ?
  `).run(CONSTANTS.EDGE_PRUNE_THRESHOLD, CONSTANTS.EDGE_PRUNE_MIN_COACTIVATION);
  report.staleEdgesPruned = pruneResult.changes;

  // 8. FTS5 optimize
  try {
    db.exec("INSERT INTO memory_nodes_fts(memory_nodes_fts) VALUES('optimize')");
    report.ftsOptimized = true;
  } catch (err) {
    report.ftsOptimized = false;
    report.stepErrors["ftsOptimize"] = err instanceof Error ? err.message : String(err);
    // Emit audit event — FTS index corruption is not silent
    try {
      db.prepare(
        "INSERT INTO memory_events (id, event_type, payload_json, created_at) VALUES (?, 'fts_optimize_failed', ?, ?)"
      ).run(
        crypto.randomUUID(),
        JSON.stringify({ error: err instanceof Error ? err.message : String(err) }),
        nowISO()
      );
    } catch { /* suppress secondary error to preserve primary */ }
  }

  const completedAt = nowISO();
  const hasErrors = Object.keys(report.stepErrors).length > 0;
  db.prepare(
    "INSERT INTO memory_events (id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)"
  ).run(
    crypto.randomUUID(),
    hasErrors ? "maintenance_failed" : "maintenance_completed",
    JSON.stringify({ runId, completedAt, stepErrors: report.stepErrors, stateTransitions: report.stateTransitions }),
    completedAt
  );

  return report;
}
