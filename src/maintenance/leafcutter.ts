import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import crypto from "node:crypto";
import { promisify } from "node:util";
import type { Database } from "better-sqlite3";
import type { AegisConfig } from "../core/models.js";

const gzip = promisify(zlib.gzip);

export class LeafcutterAnt {
  constructor(private db: Database, private workspaceDir: string, private config: AegisConfig) {}

  /**
   * Chạy quy trình thanh trừng rác và lưu trữ lạnh.
   */
  async cleanAndArchive(dryRun = false): Promise<{ archivedEvents: number; archiveFile?: string }> {
    if (this.config.archiveEnabled === false) {
      return { archivedEvents: 0 };
    }
    return this.archiveOldEvents(dryRun);
  }

  /**
   * Di chuyển các event cũ sang file nén có checksum.
   */
  private async archiveOldEvents(dryRun: boolean): Promise<{ archivedEvents: number; archiveFile?: string }> {
    const days = this.config.archiveAfterDays ?? 90;
    const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();

    // 1. Tìm các event cần archive
    const events = this.db.prepare(`
      SELECT * FROM memory_events
      WHERE created_at < ?
      ORDER BY created_at ASC
    `).all(cutoff) as any[];

    if (events.length === 0) return { archivedEvents: 0 };

    // 2. Emit archive_started event
    this.db.prepare(
      "INSERT INTO memory_events (id, event_type, payload_json, created_at) VALUES (?, ?, ?, datetime('now'))"
    ).run(crypto.randomUUID(), "archive_started", JSON.stringify({ count: events.length, cutoff, dryRun }));

    if (dryRun) {
      return { archivedEvents: events.length };
    }

    // 3. Chuẩn bị thư mục
    const archiveDir = path.join(this.workspaceDir, this.config.archiveDir ?? "archives", "events");
    if (!fs.existsSync(archiveDir)) {
      fs.mkdirSync(archiveDir, { recursive: true });
    }

    // 4. Tên file theo YYYY-MM
    const ym = new Date().toISOString().slice(0, 7);
    const fileName = `events-${ym}.jsonl.gz`;
    const filePath = path.join(archiveDir, fileName);

    // 5. Chuyển đổi sang JSONL và nén Gzip
    const jsonl = events.map(e => JSON.stringify(e)).join("\n");
    const compressed = await gzip(jsonl);

    // 6. Tính checksum SHA256
    const checksum = crypto.createHash("sha256").update(compressed).digest("hex");

    // 7. Ghi file
    fs.writeFileSync(filePath, compressed);

    // 8. Ghi log archive vào DB với checksum — cleanup file if DB insert fails
    const fromTs = events[0].created_at;
    const toTs = events[events.length - 1].created_at;
    const archiveId = crypto.randomUUID();

    try {
      this.db.prepare(`
        INSERT INTO archive_log (id, archive_kind, file_path, row_count, compressed_bytes, checksum, from_timestamp, to_timestamp, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
      `).run(archiveId, "events", fileName, events.length, compressed.length, checksum, fromTs, toTs);
    } catch (err) {
      // DB insert failed after file written — delete the orphaned file before re-throwing
      try { fs.unlinkSync(filePath); } catch { /* ignore cleanup error */ }
      throw err;
    }

    // 9. Xóa dữ liệu cũ trong DB (CHỈ sau khi đã ghi file + checksum thành công)
    const eventIds = events.map((e: any) => e.id);
    const batchSize = 500;
    for (let i = 0; i < eventIds.length; i += batchSize) {
      const batch = eventIds.slice(i, i + batchSize);
      const placeholders = batch.map(() => "?").join(",");
      this.db.prepare(`DELETE FROM memory_events WHERE id IN (${placeholders})`).run(...batch);
    }

    // 10. Emit archive_completed
    this.db.prepare(
      "INSERT INTO memory_events (id, event_type, payload_json, created_at) VALUES (?, ?, ?, datetime('now'))"
    ).run(crypto.randomUUID(), "archive_completed", JSON.stringify({ archiveId, fileName, count: events.length, checksum }));

    return { archivedEvents: events.length, archiveFile: fileName };
  }
}
