import type Database from "better-sqlite3";
import { nowISO } from "../core/id.js";
import {
  TAXONOMY_V1,
  TAXONOMY_CATEGORIES,
  TAXONOMY_MIGRATION_MAP,
  type TaxonomyCategory,
} from "../core/models.js";

/**
 * Bowerbird Layer — Taxonomy Classifier & Migrator (v4.0)
 *
 * Phân loại memory nodes theo Generic Taxonomy v1 (frozen).
 * Hỗ trợ migrate từ nhãn cũ sang taxonomy mới.
 *
 * Hardening additions:
 * - Confidence scoring cho mỗi classification
 * - Fallback bucket "knowledge.fact" chỉ khi confidence >= 0.3
 * - Anti-jitter: không relabel nếu node đã có subject và confidence cũ cao hơn
 * - classifyWithConfidence() trả về { category, confidence }
 */
export interface ClassifyResult {
  category: TaxonomyCategory | null;
  confidence: number; // 0.0 - 1.0
}

export class BowerbirdTaxonomist {
  constructor(private db: Database.Database) {}

  // ============================================================
  // A. Classify — Dán nhãn mới cho node chưa có subject
  // ============================================================

  /**
   * Quét và phân loại tất cả các node active chưa có canonical_subject.
   * Hardened: Chỉ gán khi confidence >= MIN_CLASSIFY_CONFIDENCE.
   */
  static readonly MIN_CLASSIFY_CONFIDENCE = 0.3;

  public classifyAllUnknownNodes(): number {
    const nodes = this.db.prepare(`
      SELECT id, content, memory_type FROM memory_nodes
      WHERE status = 'active' AND canonical_subject IS NULL
    `).all() as Array<{ id: string; content: string; memory_type: string }>;

    if (nodes.length === 0) return 0;

    let count = 0;

    const updateStmt = this.db.prepare(`
      UPDATE memory_nodes
      SET canonical_subject = ?, taxonomy_confidence = ?, updated_at = ?
      WHERE id = ?
    `);

    const eventStmt = this.db.prepare(`
      INSERT INTO memory_events (id, event_type, node_id, payload_json, created_at)
      VALUES (lower(hex(randomblob(16))), 'taxonomy_classified', ?, ?, ?)
    `);

    this.db.transaction(() => {
      for (const node of nodes) {
        const result = this.classifyWithConfidence(node.content, node.memory_type);
        if (result.category && result.confidence >= BowerbirdTaxonomist.MIN_CLASSIFY_CONFIDENCE) {
          const now = nowISO();
          updateStmt.run(result.category, result.confidence, now, node.id);
          eventStmt.run(node.id, JSON.stringify({
            assigned: result.category,
            confidence: result.confidence,
          }), now);
          count++;
        }
      }
    })();

    return count;
  }

  /**
   * Reclassify: Phân loại lại các node đã có subject nhưng confidence thấp.
   * Anti-jitter: chỉ relabel nếu new confidence > old confidence + 0.1.
   */
  public reclassifyLowConfidence(threshold = 0.5): number {
    const nodes = this.db.prepare(`
      SELECT id, content, memory_type, canonical_subject, taxonomy_confidence
      FROM memory_nodes
      WHERE status = 'active'
        AND canonical_subject IS NOT NULL
        AND (taxonomy_confidence IS NULL OR taxonomy_confidence < ?)
    `).all(threshold) as Array<{
      id: string; content: string; memory_type: string;
      canonical_subject: string; taxonomy_confidence: number | null;
    }>;

    if (nodes.length === 0) return 0;

    let count = 0;
    const updateStmt = this.db.prepare(`
      UPDATE memory_nodes
      SET canonical_subject = ?, taxonomy_confidence = ?, updated_at = ?
      WHERE id = ?
    `);

    this.db.transaction(() => {
      for (const node of nodes) {
        const result = this.classifyWithConfidence(node.content, node.memory_type);
        if (!result.category) continue;

        const oldConf = node.taxonomy_confidence ?? 0;
        // Anti-jitter: chỉ relabel nếu confidence mới cao hơn đáng kể
        if (result.confidence > oldConf + 0.1) {
          updateStmt.run(result.category, result.confidence, nowISO(), node.id);
          count++;
        }
      }
    })();

    return count;
  }

  // ============================================================
  // B. Classify — Heuristic Taxonomy v1
  // ============================================================

  /**
   * Phân loại content thành Taxonomy v1 category.
   * Backwards-compatible wrapper — trả về category hoặc null.
   */
  public classify(content: string, memoryType?: string): TaxonomyCategory | null {
    return this.classifyWithConfidence(content, memoryType).category;
  }

  /**
   * Phân loại content với confidence score.
   *
   * Confidence tiers:
   * - 1.0: memory_type shortcut (chắc chắn từ hệ thống)
   * - 0.9: regex match rõ ràng (nhiều keyword cùng hit)
   * - 0.7: regex match đơn lẻ
   * - 0.3: fallback bucket (knowledge.fact)
   */
  public classifyWithConfidence(content: string, memoryType?: string): ClassifyResult {
    const t = content.toLowerCase();

    // --- Shortcut từ memory_type (confidence = 1.0) ---
    const typeMap: Record<string, TaxonomyCategory> = {
      trauma: "policy.safety",
      invariant: "policy.safety",
      identity: "identity.persona",
      procedural: "workflow.procedure",
      correction: "knowledge.lesson",
      tool_artifact: "technical.tooling",
      context_texture: "context.session",
      interaction_state: "context.session",
    };
    if (memoryType && typeMap[memoryType]) {
      return { category: typeMap[memoryType], confidence: 1.0 };
    }

    // --- Scored regex rules ---
    // Mỗi rule trả về category + base confidence.
    // Đếm số keyword match để boost confidence.
    const rules: Array<{ pattern: RegExp; category: TaxonomyCategory; base: number }> = [
      // Policy / Safety
      { pattern: /(?:must not|never do|không bao giờ|bắt buộc|cấm|forbidden|prohibited|security rule|safety|invariant|không được phép)/gi, category: "policy.safety", base: 0.7 },
      { pattern: /(?:always|luôn luôn|quy tắc|nguyên tắc|policy|directive|chỉ thị|phải luôn)/gi, category: "policy.directive", base: 0.7 },
      // Identity
      { pattern: /(?:tôi là|bạn là|my name|your name|persona|tính cách|vai trò|role is|i am a|you are a)/gi, category: "identity.persona", base: 0.7 },
      { pattern: /(?:phong cách|tone|style|giọng|ngôn ngữ|formality|cách nói|cách viết|verbose|concise)/gi, category: "identity.style", base: 0.7 },
      // Workflow
      { pattern: /(?:bước \d|step \d|cách làm|hướng dẫn|workflow|quy trình|how to|procedure|SOP|checklist)/gi, category: "workflow.procedure", base: 0.7 },
      { pattern: /(?:quyết định|đã chốt|decided|trade-?off|lý do chọn|reasoning|we chose|went with)/gi, category: "workflow.decision", base: 0.7 },
      // Technical
      { pattern: /(?:deploy|ci\/cd|docker|k8s|kubernetes|server|nginx|network|proxy|port\s\d+)/gi, category: "technical.infra", base: 0.7 },
      { pattern: /(?:database|db\s|schema|sql|migration|sqlite|query|table\b|index\b|foreign\skey|primary\skey|prisma|typeorm|create\stable|alter\stable|insert\sinto|select\s.*from)/gi, category: "technical.infra", base: 0.8 },
      { pattern: /(?:git\s|terminal|bash|ssh|apt|npm\s|yarn\s|pnpm|vitest|jest|playwright|compiler|cli|command line|vsc)/gi, category: "technical.tooling", base: 0.7 },
      { pattern: /(?:typescript|javascript|python|react|next\.?js|node\.?js|rust|golang|html|css|tailwind|vue|svelte|angular)/gi, category: "technical.stack", base: 0.85 },
      { pattern: /(?:architecture|pattern|microservice|design pattern|algorithm|thuật toán|logic|module|implementation|system design)/gi, category: "technical.logic", base: 0.65 },
      { pattern: /(?:function |const |let |var |class |interface |type\s|import |export |=>|def |async\s|await |return\s|if\s\(|else\s\{)/gi, category: "technical.code", base: 0.6 },

      // Context
      { pattern: /(?:project|dự án|timeline|deadline|stakeholder|sprint|milestone|release)/gi, category: "context.project", base: 0.7 },
      // Knowledge
      { pattern: /(?:bài học|lesson|post-?mortem|retrospective|rút kinh nghiệm|lần sau|next time)/gi, category: "knowledge.lesson", base: 0.75 },
      { pattern: /(?:tham khảo|reference|docs|documentation|link|url|xem thêm|see also|nguồn)/gi, category: "knowledge.reference", base: 0.65 },
    ];

    let bestResult: ClassifyResult = { category: null, confidence: 0 };

    for (const rule of rules) {
      const matches = t.match(rule.pattern);
      if (matches && matches.length > 0) {
        // Boost confidence khi nhiều keyword match (capped at 0.95)
        const multiMatchBonus = Math.min(0.25, (matches.length - 1) * 0.1);
        const conf = Math.min(0.95, rule.base + multiMatchBonus);
        if (conf > bestResult.confidence) {
          bestResult = { category: rule.category, confidence: conf };
        }
      }
    }

    if (bestResult.category) return bestResult;

    // --- Fallback: knowledge.fact nếu đủ dài (low confidence) ---
    if (t.length > 20) {
      return { category: "knowledge.fact", confidence: 0.3 };
    }

    return { category: null, confidence: 0 };
  }

  // ============================================================
  // C. Migrate — Chuyển nhãn cũ sang Taxonomy v1
  // ============================================================

  /**
   * Migrate tất cả nhãn cũ sang taxonomy v1.
   * Trả về số node đã migrate.
   */
  public migrateOldTaxonomy(): number {
    const oldLabels = Object.keys(TAXONOMY_MIGRATION_MAP);
    if (oldLabels.length === 0) return 0;

    let count = 0;
    const now = nowISO();

    const updateStmt = this.db.prepare(`
      UPDATE memory_nodes
      SET canonical_subject = ?, updated_at = ?
      WHERE id = ?
    `);

    const eventStmt = this.db.prepare(`
      INSERT INTO memory_events (id, event_type, node_id, payload_json, created_at)
      VALUES (lower(hex(randomblob(16))), 'taxonomy_migrated', ?, ?, ?)
    `);

    this.db.transaction(() => {
      for (const [oldLabel, newLabel] of Object.entries(TAXONOMY_MIGRATION_MAP)) {
        const nodes = this.db.prepare(`
          SELECT id FROM memory_nodes
          WHERE canonical_subject = ? AND status = 'active'
        `).all(oldLabel) as Array<{ id: string }>;

        for (const node of nodes) {
          updateStmt.run(newLabel, now, node.id);
          eventStmt.run(
            node.id,
            JSON.stringify({ from: oldLabel, to: newLabel }),
            now,
          );
          count++;
        }
      }
    })();

    return count;
  }

  // ============================================================
  // D. Stats — Báo cáo phân bổ taxonomy
  // ============================================================

  /**
   * Trả về phân bổ taxonomy hiện tại.
   */
  public taxonomyStats(): Array<{ subject: string; count: number }> {
    return this.db.prepare(`
      SELECT
        COALESCE(canonical_subject, '(unlabeled)') as subject,
        COUNT(*) as count
      FROM memory_nodes
      WHERE status = 'active'
      GROUP BY canonical_subject
      ORDER BY count DESC
    `).all() as Array<{ subject: string; count: number }>;
  }

  /**
   * Kiểm tra xem taxonomy có dùng đúng nhãn v1 không.
   * Trả về danh sách nhãn lạ (không thuộc v1).
   */
  public findStrayLabels(): string[] {
    const rows = this.db.prepare(`
      SELECT DISTINCT canonical_subject as subject
      FROM memory_nodes
      WHERE status = 'active' AND canonical_subject IS NOT NULL
    `).all() as Array<{ subject: string }>;

    return rows
      .map((r) => r.subject)
      .filter((s) => !TAXONOMY_CATEGORIES.includes(s as TaxonomyCategory));
  }
}
