import fs from "node:fs";
import path from "node:path";
import type { Database } from "better-sqlite3";
import type { AegisTelemetry } from "../core/models.js";

export class Honeybee {
  constructor(private db: Database, private workspaceDir: string) {}

  /**
   * Thu thập toàn bộ số liệu Telemetry từ DB và Filesystem.
   */
  async collect(): Promise<AegisTelemetry> {
    const dbPath = path.join(this.workspaceDir, "memory-aegis.db");
    const walPath = `${dbPath}-wal`;

    const dbStats = fs.existsSync(dbPath) ? fs.statSync(dbPath) : { size: 0 };
    const walStats = fs.existsSync(walPath) ? fs.statSync(walPath) : { size: 0 };

    const row = this.db.prepare("SELECT * FROM v_aegis_telemetry").get() as any;

    const growth24h = this.estimateGrowth(24);
    const growth7d = this.estimateGrowth(24 * 7);

    return {
      db_size_bytes: dbStats.size,
      wal_size_bytes: walStats.size,
      node_count_active: row.node_count_active || 0,
      node_count_superseded: row.node_count_superseded || 0,
      node_count_archived: row.node_count_archived || 0,
      edge_count: row.edge_count || 0,
      entity_count: row.entity_count || 0,
      event_count: row.event_count || 0,
      dedup_hit_count: row.dedup_hit_count || 0,
      derived_relation_count: row.derived_relation_count || 0,
      interaction_state_count: row.interaction_state_count || 0,
      unresolved_contradictions: row.unresolved_contradictions || 0,
      latest_backup_at: row.latest_backup_at,
      latest_archive_at: row.latest_archive_at,
      growth_24h_bytes: growth24h,
      growth_7d_bytes: growth7d,
    };
  }

  private estimateGrowth(hours: number): number {
    const since = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
    const row = this.db
      .prepare("SELECT COUNT(*) as count FROM memory_events WHERE created_at > ?")
      .get(since) as any;
    return (row.count || 0) * 1024;
  }

  // ============================================================
  // Human-friendly report (Giai đoạn 2.3)
  // ============================================================

  /**
   * Tạo báo cáo ngắn gọn cho người dùng thường.
   * Không dùng thuật ngữ kỹ thuật. Trả lời 5 câu hỏi:
   * 1. Đang nhớ tốt không?
   * 2. Vừa dọn bao nhiêu?
   * 3. Có conflict đáng chú ý không?
   * 4. Latency ổn không?
   * 5. Có gì cần biết không?
   */
  renderHumanReport(t: AegisTelemetry, taxonomyStats?: Array<{ subject: string; count: number }>): string {
    const mb = (bytes: number) => (bytes / (1024 * 1024)).toFixed(2);
    const total = t.node_count_active + t.node_count_superseded + t.node_count_archived;
    const lines: string[] = [];

    // --- Header ---
    lines.push("## Memory Aegis — Status Report");
    lines.push("");

    // --- 1. Đang nhớ tốt không? ---
    const healthScore = this.computeHealthScore(t);
    const healthIcon = healthScore >= 80 ? "OK" : healthScore >= 50 ? "Warning" : "Critical";
    const healthEmoji = healthScore >= 80 ? "+" : healthScore >= 50 ? "~" : "!";

    lines.push(`### Health: [${healthEmoji}] ${healthIcon} (${healthScore}/100)`);
    lines.push(`- Active memories: ${t.node_count_active}`);
    lines.push(`- DB size: ${mb(t.db_size_bytes)} MB`);
    lines.push("");

    // --- 2. Dọn dẹp ---
    if (t.node_count_superseded > 0 || t.node_count_archived > 0) {
      lines.push(`### Cleanup`);
      lines.push(`- ${t.node_count_superseded} outdated memories replaced`);
      lines.push(`- ${t.node_count_archived} old memories archived`);
      lines.push(`- ${t.dedup_hit_count} duplicates caught`);
      lines.push("");
    }

    // --- 3. Conflicts ---
    if (t.unresolved_contradictions > 0) {
      lines.push(`### Conflicts: ${t.unresolved_contradictions} unresolved`);
      lines.push(`- Run /memory-clean to auto-resolve safe conflicts`);
      lines.push("");
    }

    // --- 4. Growth ---
    if (t.growth_24h_bytes > 0 || t.growth_7d_bytes > 0) {
      lines.push(`### Growth`);
      lines.push(`- Last 24h: +${mb(t.growth_24h_bytes)} MB`);
      lines.push(`- Last 7d: +${mb(t.growth_7d_bytes)} MB`);
      lines.push("");
    }

    // --- 5. Taxonomy ---
    if (taxonomyStats && taxonomyStats.length > 0) {
      lines.push(`### Knowledge Distribution`);
      const topN = taxonomyStats.slice(0, 8);
      for (const s of topN) {
        const pct = total > 0 ? Math.round((s.count / total) * 100) : 0;
        const bar = "#".repeat(Math.max(1, Math.round(pct / 5)));
        lines.push(`- ${s.subject}: ${s.count} (${pct}%) ${bar}`);
      }
      if (taxonomyStats.length > 8) {
        lines.push(`- ... and ${taxonomyStats.length - 8} more categories`);
      }
      lines.push("");
    }

    // --- 6. Action items ---
    const actions: string[] = [];
    if (t.unresolved_contradictions > 3) actions.push("Review contradictions with /memory-clean");
    if (!t.latest_backup_at) actions.push("No backup found — run /memory-backup");
    if (t.node_count_active > 1000 && t.node_count_archived === 0) actions.push("Consider archiving old memories");

    if (actions.length > 0) {
      lines.push(`### Recommended Actions`);
      for (const a of actions) lines.push(`- ${a}`);
      lines.push("");
    }

    // --- Backup status ---
    lines.push(`### Backup`);
    lines.push(`- Last backup: ${t.latest_backup_at || "Never"}`);
    lines.push(`- Last archive: ${t.latest_archive_at || "Never"}`);

    return lines.join("\n");
  }

  /**
   * Health score: 0-100 dựa trên nhiều tín hiệu.
   */
  private computeHealthScore(t: AegisTelemetry): number {
    let score = 100;

    // Conflicts penalty
    if (t.unresolved_contradictions > 0) score -= Math.min(30, t.unresolved_contradictions * 5);

    // No backup penalty
    if (!t.latest_backup_at) score -= 10;

    // DB quá lớn
    if (t.db_size_bytes > 100 * 1024 * 1024) score -= 10; // >100MB

    // WAL quá lớn (chưa checkpoint)
    if (t.wal_size_bytes > 10 * 1024 * 1024) score -= 10; // >10MB

    // No active nodes
    if (t.node_count_active === 0) score -= 20;

    return Math.max(0, score);
  }

  /**
   * Render kỹ thuật cho power users (giữ lại bản cũ).
   */
  render(t: AegisTelemetry): string {
    const mb = (bytes: number) => (bytes / (1024 * 1024)).toFixed(2);

    return [
      "**Aegis v4 Honeybee Stats**",
      `- DB: ${mb(t.db_size_bytes)} MB (WAL: ${mb(t.wal_size_bytes)} MB)`,
      `- Nodes (Active/Superseded/Archive): ${t.node_count_active} / ${t.node_count_superseded} / ${t.node_count_archived}`,
      `- Edges: ${t.edge_count}`,
      `- Entities: ${t.entity_count}`,
      `- Events: ${t.event_count}`,
      `- Dedup Hits: ${t.dedup_hit_count}`,
      `- Derived Relations: ${t.derived_relation_count}`,
      `- Contradictions: ${t.unresolved_contradictions}`,
      `- Growth (24h/7d): +${mb(t.growth_24h_bytes)} MB / +${mb(t.growth_7d_bytes)} MB`,
      `- Last Backup: ${t.latest_backup_at || "N/A"}`,
      `- Last Archive: ${t.latest_archive_at || "N/A"}`,
    ].join("\n");
  }
}
