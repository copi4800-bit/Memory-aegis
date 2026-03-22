/**
 * Eagle Layer — Graph Analysis & Summary Engine.
 *
 * Giai đoạn 4.1: Eagle không chỉ vẽ graph, mà phải tự tóm:
 * - hotspot (subject nào đang phình)
 * - top conflict clusters
 * - supersede chain bất thường
 * - episode rối
 * - taxonomy health
 */

import type Database from "better-sqlite3";
import { TAXONOMY_CATEGORIES } from "../core/models.js";

export interface GraphData {
  nodes: Array<{
    id: string;
    label: string;
    subject: string | null;
    type: string;
    status: string;
    importance: number;
  }>;
  links: Array<{
    source: string;
    target: string;
    type: string;
    weight: number;
  }>;
}

export interface EagleSummary {
  healthScore: number;
  hotspots: Array<{ subject: string; count: number }>;
  conflictClusters: Array<{ subject: string; count: number }>;
  supersedeStat: { total: number; ratio: number };
  taxonomyCoverage: { labeled: number; unlabeled: number; strayLabels: string[] };
  warnings: string[];
  recommendations: string[];
}

export class EagleEye {
  constructor(private db: Database.Database) {}

  /**
   * Chụp ảnh đồ thị bộ não (cho D3.js).
   */
  public captureSnapshot(limit = 2000): GraphData {
    const nodes = this.db.prepare(`
      SELECT id, content, canonical_subject, memory_type, status, importance
      FROM memory_nodes
      WHERE status IN ('active', 'superseded')
      ORDER BY created_at DESC
      LIMIT ?
    `).all(limit) as any[];

    const nodeIds = new Set(nodes.map((n: any) => n.id));

    const edges = this.db.prepare(`
      SELECT src_node_id, dst_node_id, edge_type, weight
      FROM memory_edges
      WHERE status = 'active'
    `).all() as any[];

    const conflicts = this.db.prepare(`
      SELECT node_id, json_extract(extension_json, '$.nodeBId') as target_id
      FROM drift_events
      WHERE resolved = 0 AND drift_type = 'contradiction'
    `).all() as any[];

    return {
      nodes: nodes.map((n: any) => ({
        id: n.id,
        label: n.content.substring(0, 50) + (n.content.length > 50 ? "..." : ""),
        subject: n.canonical_subject,
        type: n.memory_type,
        status: n.status,
        importance: n.importance,
      })),
      links: [
        ...edges
          .filter((e: any) => nodeIds.has(e.src_node_id) && nodeIds.has(e.dst_node_id))
          .map((e: any) => ({
            source: e.src_node_id,
            target: e.dst_node_id,
            type: e.edge_type,
            weight: e.weight,
          })),
        ...conflicts
          .filter((c: any) => c.target_id && nodeIds.has(c.node_id) && nodeIds.has(c.target_id))
          .map((c: any) => ({
            source: c.node_id,
            target: c.target_id,
            type: "contradiction",
            weight: 1.5,
          })),
      ],
    };
  }

  // ============================================================
  // Summary Mode (Giai đoạn 4.1)
  // ============================================================

  /**
   * Phân tích sâu và trả về structured summary.
   */
  public summarize(): EagleSummary {
    const warnings: string[] = [];
    const recommendations: string[] = [];

    // --- Hotspots: subject nào đang phình ---
    const hotspots = this.db.prepare(`
      SELECT COALESCE(canonical_subject, '(unlabeled)') as subject, COUNT(*) as count
      FROM memory_nodes WHERE status = 'active'
      GROUP BY canonical_subject
      ORDER BY count DESC
      LIMIT 10
    `).all() as Array<{ subject: string; count: number }>;

    if (hotspots.length > 0 && hotspots[0].count > 50) {
      warnings.push(`Subject "${hotspots[0].subject}" has ${hotspots[0].count} nodes — consider splitting`);
    }

    // --- Conflict clusters: subject nào đang nhiều mâu thuẫn ---
    const conflictClusters = this.db.prepare(`
      SELECT
        COALESCE(mn.canonical_subject, '(unlabeled)') as subject,
        COUNT(*) as count
      FROM drift_events de
      JOIN memory_nodes mn ON de.node_id = mn.id
      WHERE de.resolved = 0 AND de.drift_type = 'contradiction'
      GROUP BY mn.canonical_subject
      ORDER BY count DESC
      LIMIT 5
    `).all() as Array<{ subject: string; count: number }>;

    if (conflictClusters.length > 0 && conflictClusters[0].count > 5) {
      warnings.push(`Subject "${conflictClusters[0].subject}" has ${conflictClusters[0].count} unresolved conflicts`);
      recommendations.push(`Run /memory-clean to auto-resolve conflicts in "${conflictClusters[0].subject}"`);
    }

    // --- Supersede stats ---
    const superseded = (this.db.prepare(
      "SELECT COUNT(*) as c FROM memory_nodes WHERE status = 'superseded'"
    ).get() as any).c || 0;
    const active = (this.db.prepare(
      "SELECT COUNT(*) as c FROM memory_nodes WHERE status = 'active'"
    ).get() as any).c || 0;
    const total = active + superseded;
    const ratio = total > 0 ? superseded / total : 0;

    if (ratio > 0.6) {
      warnings.push(`High supersede ratio (${(ratio * 100).toFixed(0)}%) — many memories being replaced`);
    }

    // --- Taxonomy coverage ---
    const labeled = (this.db.prepare(
      "SELECT COUNT(*) as c FROM memory_nodes WHERE status = 'active' AND canonical_subject IS NOT NULL"
    ).get() as any).c || 0;
    const unlabeled = (this.db.prepare(
      "SELECT COUNT(*) as c FROM memory_nodes WHERE status = 'active' AND canonical_subject IS NULL"
    ).get() as any).c || 0;

    if (unlabeled > labeled * 0.5) {
      recommendations.push(`${unlabeled} unlabeled nodes — run Bowerbird taxonomy classifier`);
    }

    // Stray labels (not in taxonomy v1)
    const allSubjects = this.db.prepare(`
      SELECT DISTINCT canonical_subject as subject
      FROM memory_nodes
      WHERE status = 'active' AND canonical_subject IS NOT NULL
    `).all() as Array<{ subject: string }>;
    const strayLabels = allSubjects
      .map((r) => r.subject)
      .filter((s) => !TAXONOMY_CATEGORIES.includes(s as any));

    if (strayLabels.length > 0) {
      recommendations.push(`${strayLabels.length} non-standard labels found — run taxonomy migration`);
    }

    // --- Edge health ---
    const mentionEdges = (this.db.prepare(
      "SELECT COUNT(*) as c FROM memory_edges WHERE status = 'active' AND edge_type = 'mentions_entity'"
    ).get() as any).c || 0;
    if (active > 0 && mentionEdges > active * 10) {
      warnings.push(`Entity mention edges (${mentionEdges}) >> active nodes (${active}) — graph is over-connected`);
      recommendations.push("Consider running Salmon dedup and Dolphin entity resolution");
    }

    // --- Health score ---
    let healthScore = 100;
    healthScore -= warnings.length * 10;
    healthScore -= Math.min(20, unlabeled);
    if (ratio > 0.5) healthScore -= 10;
    healthScore = Math.max(0, Math.min(100, healthScore));

    return {
      healthScore,
      hotspots,
      conflictClusters,
      supersedeStat: { total: superseded, ratio },
      taxonomyCoverage: { labeled, unlabeled, strayLabels },
      warnings,
      recommendations,
    };
  }

  /**
   * Render summary thành text report cho người dùng.
   */
  public renderSummary(summary?: EagleSummary): string {
    const s = summary ?? this.summarize();
    const lines: string[] = [];

    lines.push("### BÁO CÁO GIÁM SÁT TỪ ĐẠI BÀNG");
    lines.push("");

    // Health
    const icon = s.healthScore >= 80 ? "Khỏe mạnh" : s.healthScore >= 50 ? "Cần chú ý" : "Nguy kịch";
    lines.push(`**Sức khỏe bộ não:** ${s.healthScore}/100 — ${icon}`);
    lines.push("");

    // Hotspots
    if (s.hotspots.length > 0) {
      lines.push("**Top Subjects:**");
      for (const h of s.hotspots.slice(0, 5)) {
        lines.push(`- ${h.subject}: ${h.count} nodes`);
      }
      lines.push("");
    }

    // Conflicts
    if (s.conflictClusters.length > 0) {
      lines.push("**Conflict Clusters:**");
      for (const c of s.conflictClusters) {
        lines.push(`- ${c.subject}: ${c.count} conflicts`);
      }
      lines.push("");
    }

    // Cleanup efficiency
    lines.push(`**Cleanup Efficiency:** ${(s.supersedeStat.ratio * 100).toFixed(0)}% compressed (${s.supersedeStat.total} replaced)`);
    lines.push(`**Taxonomy Coverage:** ${s.taxonomyCoverage.labeled} labeled / ${s.taxonomyCoverage.unlabeled} unlabeled`);
    lines.push("");

    // Warnings
    if (s.warnings.length > 0) {
      lines.push("**Warnings:**");
      for (const w of s.warnings) lines.push(`- ${w}`);
      lines.push("");
    }

    // Recommendations
    if (s.recommendations.length > 0) {
      lines.push("**Recommendations:**");
      for (const r of s.recommendations) lines.push(`- ${r}`);
    }

    return lines.join("\n");
  }

  /**
   * Legacy analyze() — gọi summarize + render.
   */
  public analyze(): string {
    return this.renderSummary();
  }
}
