import type Database from "better-sqlite3";
import crypto from "node:crypto";
import type { MemoryNode } from "../core/models.js";

/**
 * Meerkat Layer — Contradiction Sentry
 * Scans for logical inconsistencies across different episodes and subjects.
 * 
 * Nhiệm vụ: Tăng Trust cho bộ não bằng cách phát hiện các điểm "cắn nhau"
 * giữa bối cảnh hiện tại (Episode) và các quy tắc chung (Global).
 */
export class MeerkatSentry {
  constructor(private db: Database.Database) {}

  /**
   * Focuses on nodes with the same canonical_subject but potentially different contents.
   */
  public scan(): Array<{ nodeA: string; nodeB: string; reason: string }> {
    console.log("🦦 Meerkat: Đang quét mâu thuẫn theo biên giới Episode & Global Rules...");

    // 1. Tìm các chủ thể có mâu thuẫn tiềm năng
    const subjects = this.db.prepare(`
      SELECT canonical_subject, COUNT(*) as count 
      FROM memory_nodes 
      WHERE status = 'active' AND canonical_subject IS NOT NULL
      GROUP BY canonical_subject 
      HAVING count > 1
    `).all() as Array<{ canonical_subject: string }>;

    const contradictions: Array<{ nodeA: string; nodeB: string; reason: string }> = [];

    // Lấy ID của Episode đang hoạt động duy nhất
    const activeEpisode = this.db.prepare("SELECT id FROM episodes WHERE status = 'active' ORDER BY created_at DESC LIMIT 1").get() as { id: string } | undefined;

    for (const sub of subjects) {
      // CHỈ quét mâu thuẫn trong cùng bối cảnh (Episode) hoặc bối cảnh vs Global
      const nodes = this.db.prepare(`
        SELECT id, content, episode_id, created_at
        FROM memory_nodes 
        WHERE canonical_subject = ? 
        AND status = 'active'
        AND (
          episode_id = ? OR episode_id IS NULL
        )
      `).all(sub.canonical_subject, activeEpisode?.id || 'none') as Array<MemoryNode>;

      // 2. So sánh từng cặp Node trong bối cảnh đã lọc
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const conflict = this.detectConflict(nodes[i], nodes[j]);
          if (conflict) {
            const reason = `[${sub.canonical_subject}] ${conflict}`;
            contradictions.push({
              nodeA: nodes[i].id,
              nodeB: nodes[j].id,
              reason
            });
            this.recordConflict(nodes[i].id, nodes[j].id, sub.canonical_subject, conflict);
          }
        }
      }
    }

    return contradictions;
  }

  /**
   * Heuristic conflict detection
   */
  private detectConflict(nodeA: MemoryNode, nodeB: MemoryNode): string | null {
    const contentA = nodeA.content.toLowerCase();
    const contentB = nodeB.content.toLowerCase();

    // 1. Kiểm tra mâu thuẫn từ khóa (Negations vs Affirmations)
    const negations = ["không", "đừng", "cấm", "no", "never", "cannot", "must not", "forbidden", "bắt buộc không"];
    const affirmations = ["có", "nên", "cho phép", "allow", "yes", "can", "must", "required", "bắt buộc", "luôn luôn"];

    const aHasNeg = negations.some(n => contentA.includes(n));
    const bHasAff = affirmations.some(p => contentB.includes(p));
    
    const bHasNeg = negations.some(n => contentB.includes(n));
    const aHasAff = affirmations.some(p => contentA.includes(p));

    if ((aHasNeg && bHasAff) || (bHasNeg && aHasAff)) {
      // 2. Logic thời gian: Nếu một node mới hơn node kia đáng kể (> 24h)
      const dateA = new Date(nodeA.created_at).getTime();
      const dateB = new Date(nodeB.created_at).getTime();
      const diffHours = Math.abs(dateA - dateB) / (1000 * 60 * 60);

      if (diffHours > 24) {
        const newer = dateA > dateB ? "A" : "B";
        return `Có thể là bản cập nhật (Superseded candidate): Node ${newer} mới hơn ${diffHours.toFixed(1)} giờ.`;
      }

      if (nodeA.episode_id !== nodeB.episode_id) {
        return `Xung đột logic giữa Episode ${nodeA.episode_id} và ${nodeB.episode_id}`;
      }
      return "Xung đột logic trực tiếp";
    }

    // 3. Kiểm tra mâu thuẫn tần suất
    const frequencyAlways = ["luôn luôn", "mọi lúc", "always", "every time"];
    const frequencyNever = ["không bao giờ", "never", "none"];
    const frequencySometimes = ["thỉnh thoảng", "đôi khi", "sometimes", "occasionally"];

    const aAlways = frequencyAlways.some(f => contentA.includes(f));
    const bNever = frequencyNever.some(f => contentB.includes(f));
    const bSometimes = frequencySometimes.some(f => contentB.includes(f));

    if (aAlways && (bNever || bSometimes)) {
      return "Mâu thuẫn về tần suất hoạt động";
    }

    return null;
  }

  private recordConflict(nodeAId: string, nodeBId: string, subject: string, reason: string): void {
    const id = `drift_${crypto.randomUUID().substring(0, 8)}`;
    this.db.prepare(`
      INSERT OR IGNORE INTO drift_events (
        id, node_id, baseline_fingerprint_id, current_fingerprint_id,
        drift_type, severity, detected_at, extension_json
      ) VALUES (?, ?, ?, ?, 'contradiction', 'high', ?, ?)
    `).run(id, nodeAId, 'legacy_baseline', 'legacy_current', new Date().toISOString(), JSON.stringify({ reason, subject, nodeBId }));
  }
}
