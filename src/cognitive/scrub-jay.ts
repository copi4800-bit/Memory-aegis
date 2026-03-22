/**
 * Scrub Jay Layer — Episodic Memory Management.
 * 
 * Như loài chim giẻ cùi giấu thức ăn theo từng bối cảnh — 
 * lớp này quản lý các phiên làm việc (Episodes) để giữ 
 * cho bộ não có mạch tư duy nhất quán và giảm nhiễu.
 */

import type Database from "better-sqlite3";
import { newId, nowISO } from "../core/id.js";

export interface Episode {
  id: string;
  parent_id: string | null;
  type: string;
  status: "active" | "concluded" | "summarized";
  goal: string | null;
  context_summary: string | null;
  start_at: string;
  end_at: string | null;
  created_at: string;
}

export class ScrubJay {
  constructor(private db: Database.Database) {}

  /**
   * Bắt đầu một Episode mới (phiên làm việc mới).
   */
  public startEpisode(type = "chat", goal?: string): string {
    const id = `ep_${newId().substring(0, 8)}`;
    const now = nowISO();

    // Kết thúc các episode đang active cũ (nếu có) để tránh chồng chéo
    this.db.prepare("UPDATE episodes SET status = 'concluded', end_at = ? WHERE status = 'active'").run(now);

    this.db.prepare(`
      INSERT INTO episodes (id, type, status, goal, start_at, created_at)
      VALUES (?, ?, 'active', ?, ?, ?)
    `).run(id, type, goal || null, now, now);

    console.log(`🪶 Scrub Jay: Đã bắt đầu Episode mới [${id}] - Mục tiêu: ${goal || "Không xác định"}`);
    return id;
  }

  /**
   * Lấy ID của Episode đang hoạt động duy nhất.
   */
  public getActiveEpisodeId(): string | null {
    const row = this.db.prepare("SELECT id FROM episodes WHERE status = 'active' ORDER BY created_at DESC LIMIT 1").get() as { id: string } | undefined;
    return row?.id || null;
  }

  /**
   * Kết thúc Episode hiện tại.
   */
  public concludeEpisode(id: string, summary?: string): void {
    const now = nowISO();
    this.db.prepare(`
      UPDATE episodes 
      SET status = 'concluded', end_at = ?, context_summary = ? 
      WHERE id = ?
    `).run(now, summary || null, id);
    console.log(`🪶 Scrub Jay: Đã kết thúc Episode [${id}].`);
  }

  /**
   * Tự động dán nhãn context.session cho các node thuộc Episode này.
   */
  public labelEpisodeNodes(episodeId: string): number {
    const result = this.db.prepare(`
      UPDATE memory_nodes 
      SET canonical_subject = 'context.session' 
      WHERE episode_id = ? AND canonical_subject IS NULL
    `).run(episodeId);
    return result.changes;
  }
}
