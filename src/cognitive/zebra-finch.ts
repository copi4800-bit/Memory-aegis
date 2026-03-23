/**
 * Zebra Finch Layer — Semantic Consolidation & REM Sleep.
 * 
 * Như loài chim sẻ vằn mơ về bài hót — lớp này chạy ngầm để 
 * dọn dẹp các mâu thuẫn và nén các ký ức vụn vặt thành 
 * các Node luật (Invariant) sạch sẽ hơn.
 */

import type Database from "better-sqlite3";
import { newId, nowISO } from "../core/id.js";
import { MeerkatSentry } from "./meerkat.js";
import { normalizeVietnamese } from "../core/normalize-vi.js";

export interface ConsolidationReport {
  supersededCount: number;
  consolidatedCount: number;
  eventsLogged: number;
}

export class ZebraFinch {
  constructor(private db: Database.Database) {}

  /**
   * Chạy chu trình "Giấc mơ Sẻ Vằn" để tự động hóa dọn dẹp.
   */
  public async performRemSleep(): Promise<ConsolidationReport> {
    console.log("🎶 Zebra Finch: Bắt đầu 'mơ' về các ký ức để tối ưu hóa bộ não...");
    
    const report: ConsolidationReport = {
      supersededCount: 0,
      consolidatedCount: 0,
      eventsLogged: 0
    };

    // 1. Tự động thay thế (Auto-Supersede) dựa trên Meerkat Sentry
    const meerkat = new MeerkatSentry(this.db);
    const conflicts = meerkat.scan();

    for (const conflict of conflicts) {
      if (conflict.reason.includes("Superseded candidate")) {
        const success = this.applySupersede(conflict.nodeA, conflict.nodeB);
        if (success) report.supersededCount++;
      }
    }

    // 2. Jaccard near-duplicate consolidation (no LLM needed — pure set math)
    report.consolidatedCount = this.consolidateByJaccard();

    return report;
  }

  private extractTerms(text: string): Set<string> {
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

  private jaccardSimilarity(a: Set<string>, b: Set<string>): number {
    if (a.size === 0 && b.size === 0) return 1.0;
    if (a.size === 0 || b.size === 0) return 0.0;
    const intersection = [...a].filter(t => b.has(t)).length;
    const union = new Set([...a, ...b]).size;
    return intersection / union;
  }

  private consolidateByJaccard(): number {
    const JACCARD_THRESHOLD = 0.6;
    const now = nowISO();
    let merged = 0;

    // Get all subjects with 2+ active nodes
    const subjects = this.db.prepare(`
      SELECT canonical_subject
      FROM memory_nodes
      WHERE status = 'active'
        AND canonical_subject IS NOT NULL
        AND memory_state NOT IN ('crystallized', 'archived')
      GROUP BY canonical_subject
      HAVING COUNT(*) > 1
    `).all() as Array<{ canonical_subject: string }>;

    const getNodes = this.db.prepare(`
      SELECT id, content, created_at
      FROM memory_nodes
      WHERE canonical_subject = ? AND status = 'active'
        AND memory_state NOT IN ('crystallized', 'archived')
      ORDER BY created_at DESC
    `);

    for (const { canonical_subject } of subjects) {
      const nodes = getNodes.all(canonical_subject) as Array<{
        id: string; content: string; created_at: string;
      }>;

      // Compare all pairs — supersede older if Jaccard >= threshold
      const superseded = new Set<string>();

      for (let i = 0; i < nodes.length; i++) {
        if (superseded.has(nodes[i].id)) continue;
        const termsI = this.extractTerms(nodes[i].content);

        for (let j = i + 1; j < nodes.length; j++) {
          if (superseded.has(nodes[j].id)) continue;
          const termsJ = this.extractTerms(nodes[j].content);
          const similarity = this.jaccardSimilarity(termsI, termsJ);

          if (similarity >= JACCARD_THRESHOLD) {
            // nodes[i] is newer (ORDER BY created_at DESC), supersede nodes[j]
            this.db.transaction(() => {
              this.db.prepare(
                `UPDATE memory_nodes SET status = 'superseded', updated_at = ? WHERE id = ? AND status = 'active'`
              ).run(now, nodes[j].id);

              const edgeId = `edge_${newId().substring(0, 8)}`;
              this.db.prepare(`
                INSERT INTO memory_edges (id, src_node_id, dst_node_id, edge_type, weight, confidence, status, created_at, updated_at, extension_json)
                VALUES (?, ?, ?, 'supersedes', ?, 1.0, 'active', ?, ?, ?)
              `).run(edgeId, nodes[i].id, nodes[j].id, similarity, now, now,
                JSON.stringify({ reason: "Jaccard near-duplicate", similarity, mechanism: "jaccard_consolidation" }));

              this.db.prepare(
                `INSERT INTO memory_events (id, event_type, node_id, payload_json, created_at) VALUES (?, 'jaccard_consolidated', ?, ?, ?)`
              ).run(newId(), nodes[j].id, JSON.stringify({ superseded_by: nodes[i].id, similarity, subject: canonical_subject }), now);
            })();

            superseded.add(nodes[j].id);
            merged++;
          }
        }
      }
    }

    return merged;
  }

  /**
   * Thực hiện việc thay thế Node cũ bằng Node mới một cách an toàn.
   */
  private applySupersede(nodeAId: string, nodeBId: string): boolean {
    const now = nowISO();
    
    // Lấy thông tin 2 node để so sánh thời gian
    const nodes = this.db.prepare(`
      SELECT id, created_at FROM memory_nodes WHERE id IN (?, ?)
    `).all(nodeAId, nodeBId) as Array<{ id: string, created_at: string }>;

    if (nodes.length < 2) return false;

    const nodeA = nodes.find(n => n.id === nodeAId)!;
    const nodeB = nodes.find(n => n.id === nodeBId)!;

    const isANewer = new Date(nodeA.created_at) > new Date(nodeB.created_at);
    const newerId = isANewer ? nodeAId : nodeBId;
    const olderId = isANewer ? nodeBId : nodeAId;

    this.db.transaction(() => {
      // 1. Đánh dấu node cũ là superseded
      this.db.prepare(`
        UPDATE memory_nodes 
        SET status = 'superseded', updated_at = ? 
        WHERE id = ? AND status = 'active'
      `).run(now, olderId);

      // 2. Tạo liên kết 'supersedes' trong memory_edges để giữ provenance
      const edgeId = `edge_${newId().substring(0, 8)}`;
      this.db.prepare(`
        INSERT INTO memory_edges (
          id, src_node_id, dst_node_id, edge_type, weight, confidence, 
          status, created_at, updated_at, extension_json
        ) VALUES (?, ?, ?, 'supersedes', 1.0, 1.0, 'active', ?, ?, ?)
      `).run(edgeId, newerId, olderId, now, now, JSON.stringify({ 
        reason: "Auto-cleanup by Zebra Finch REM sleep",
        mechanism: "temporal_superseding"
      }));

      // 3. Ghi log sự kiện
      this.db.prepare(`
        INSERT INTO memory_events (id, event_type, node_id, payload_json, created_at)
        VALUES (?, 'auto_supersede', ?, ?, ?)
      `).run(newId(), olderId, JSON.stringify({ superseded_by: newerId }), now);
    })();

    return true;
  }
}
