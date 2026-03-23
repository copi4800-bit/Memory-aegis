import type Database from "better-sqlite3";
import crypto from "node:crypto";
import type { MemoryNode } from "../core/models.js";
import { normalizeVietnamese } from "../core/normalize-vi.js";

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
            if (conflict.includes("[HIGH]") || conflict.includes("[MEDIUM]")) {
              this.recordConflict(nodes[i].id, nodes[j].id, sub.canonical_subject, conflict);
            }
          }
        }
      }
    }

    return contradictions;
  }

  private extractMeaningfulTerms(text: string): Set<string> {
    const STOPWORDS = new Set([
      "và", "hoặc", "của", "với", "trong", "ngoài", "từ", "đến", "theo",
      "bằng", "này", "kia", "đây", "đó", "rất", "quá", "hơn", "nhất",
      "the", "and", "or", "but", "for", "with", "that", "this", "from",
      "have", "has", "are", "was", "were", "been", "will", "would",
      "could", "should", "may", "might", "can", "also", "just", "more",
      "không", "có", "là", "một", "các", "những", "được", "khi", "nếu",
      "then", "when", "into", "than", "they", "them", "their",
    ]);

    const terms = new Set<string>();
    for (const w of text.toLowerCase().split(/[\s,.()\[\]{};:!?'"\/\\]+/)) {
      if (w.length <= 3 || STOPWORDS.has(w)) continue;
      terms.add(w);
      const norm = normalizeVietnamese(w);
      if (norm !== w) terms.add(norm); // add diacritic-free alias for synonym bridging
    }
    return terms;
  }

  /**
   * Returns true if any keyword appears within windowSize words of any shared term.
   */
  private isNegationNearTerm(
    text: string,
    keywords: string[],
    sharedTerms: string[],
    windowSize = 8,
  ): boolean {
    const words = text.toLowerCase().split(/[\s,.()\[\]{};:!?'"\/\\]+/).filter(Boolean);
    for (let i = 0; i < words.length; i++) {
      if (keywords.some(k => words[i].includes(k))) {
        const start = Math.max(0, i - windowSize);
        const end = Math.min(words.length - 1, i + windowSize);
        const window = words.slice(start, end + 1);
        if (sharedTerms.some(t => window.some(w => w.includes(t)))) {
          return true;
        }
      }
    }
    return false;
  }

  /**
   * Compute IDF-weighted score for a list of shared terms.
   * IDF(term) = log(totalNodes / (docsWithTerm + 1))
   * Rare terms score higher than common ones.
   */
  private computeIdfScore(sharedTerms: string[]): number {
    if (sharedTerms.length === 0) return 0;

    const totalRow = this.db.prepare(
      `SELECT COUNT(*) as total FROM memory_nodes WHERE status = 'active'`
    ).get() as { total: number };
    const totalNodes = Math.max(1, totalRow.total);

    let score = 0;
    for (const term of sharedTerms) {
      const freqRow = this.db.prepare(
        `SELECT COUNT(*) as freq FROM memory_nodes WHERE status = 'active' AND content LIKE ?`
      ).get(`%${term}%`) as { freq: number };
      const freq = Math.max(0, freqRow.freq);
      const idf = Math.log(totalNodes / (freq + 1));
      score += Math.max(0, idf); // IDF can be negative if term appears in most nodes — clamp to 0
    }

    return score;
  }

  /**
   * Heuristic conflict detection
   */
  private detectConflict(nodeA: MemoryNode, nodeB: MemoryNode): string | null {
    // Shared term gate: nodes must share vocabulary to potentially contradict
    const termsA = this.extractMeaningfulTerms(nodeA.content);
    const termsB = this.extractMeaningfulTerms(nodeB.content);
    const sharedTerms = [...termsA].filter(t => termsB.has(t));
    if (sharedTerms.length === 0) return null; // Fast exit: no overlap at all

    const IDF_THRESHOLD = 1.5; // ~2 moderately rare terms, or 1 very rare term
    const idfScore = this.computeIdfScore(sharedTerms);
    if (idfScore < IDF_THRESHOLD) return null;

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
      // Proximity check: negation near a shared term = high confidence
      const proximityA = this.isNegationNearTerm(contentA, negations, sharedTerms);
      const proximityB = this.isNegationNearTerm(contentB, negations, sharedTerms);
      const highConfidence = proximityA || proximityB;

      // Skip if no proximity match AND not enough shared terms
      if (!highConfidence && sharedTerms.length < 3) return null;

      const confidenceTag = highConfidence ? "[HIGH]" : "[MEDIUM]";

      const dateA = new Date(nodeA.created_at).getTime();
      const dateB = new Date(nodeB.created_at).getTime();
      const diffHours = Math.abs(dateA - dateB) / (1000 * 60 * 60);

      if (diffHours > 24) {
        const newer = dateA > dateB ? "A" : "B";
        return `${confidenceTag} Superseded candidate: Node ${newer} mới hơn ${diffHours.toFixed(1)} giờ.`;
      }

      if (nodeA.episode_id !== nodeB.episode_id) {
        return `${confidenceTag} Xung đột logic giữa Episode ${nodeA.episode_id} và ${nodeB.episode_id}`;
      }
      return `${confidenceTag} Xung đột logic trực tiếp`;
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
