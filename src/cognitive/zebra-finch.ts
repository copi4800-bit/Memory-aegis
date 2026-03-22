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

    // 2. Gom mảnh ngữ nghĩa (Subject Consolidation)
    // (Trong phiên bản này chúng ta mới chỉ làm auto-supersede, 
    // consolidation bằng LLM sẽ được cập nhật sau khi có bridge LLM)

    return report;
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
