/**
 * Test: SQLITE_BUSY Under Concurrent Maintenance
 *
 * Mục tiêu: Kiểm tra hệ thống không bị SQLITE_BUSY khi insert + search chạy
 * đồng thời với maintenance cycle. Đây là điểm yếu chí mạng nhất của hệ thống.
 *
 * Kịch bản: Mở nhiều Worker async để insert dữ liệu và chạy retrieval,
 * trong khi một worker khác liên tục kích hoạt runMaintenanceCycle().
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { openDatabase, type AegisDatabase } from "../../src/db/connection.js";
import { ingestChunk, ingestBatch } from "../../src/core/ingest.js";
import { executeRetrievalPipeline } from "../../src/retrieval/pipeline.js";
import { runMaintenanceCycle } from "../../src/retention/maintenance.js";
import { DEFAULT_AEGIS_CONFIG } from "../../src/core/models.js";

let db: AegisDatabase;
let testDir: string;

const TEST_CONFIG = {
  ...DEFAULT_AEGIS_CONFIG,
  enabledLayers: ["orca", "salmon"] as any,
  retrievalMaxHops: 1,
  maxNodesPerSearch: 10,
};

beforeEach(() => {
  testDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-busy-"));
  db = openDatabase(path.join(testDir, "test.db"));
});

afterEach(() => {
  try { db.close(); } catch {}
  try { fs.rmSync(testDir, { recursive: true, force: true }); } catch {}
});

describe("SQLITE_BUSY Race Condition Tests", () => {
  it("no crash under concurrent insert + maintenance (WAL mode check)", async () => {
    // Kiểm tra WAL đã bật trước
    const mode = db.db.pragma("journal_mode") as Array<{ journal_mode: string }>;
    expect(mode[0].journal_mode).toBe("wal");

    // Seed data trước
    const seedChunks = Array.from({ length: 20 }, (_, i) => ({
      sourcePath: `seed/doc-${i}.md`,
      content: `Seed content block number ${i} with unique keywords omega-${i} delta memory.`,
      source: "memory" as const,
    }));
    ingestBatch(db.db, seedChunks);

    const errors: string[] = [];
    let sqliteBusyCount = 0;

    // Worker A: insert 50 records liên tục
    const insertWorker = async () => {
      for (let i = 0; i < 50; i++) {
        try {
          ingestChunk(db.db, {
            sourcePath: `concurrent/doc-${i}.md`,
            content: `Concurrent insert test content alpha-${i} bravo memory knowledge base.`,
            source: "memory",
          });
        } catch (err: any) {
          if (err?.message?.includes("SQLITE_BUSY") || err?.code === "SQLITE_BUSY") {
            sqliteBusyCount++;
          } else {
            errors.push(`insert-${i}: ${err?.message}`);
          }
        }
        // Nhường luồng
        await new Promise((r) => setImmediate(r));
      }
    };

    // Worker B: chạy retrieval 20 lần liên tục
    const retrievalWorker = async () => {
      for (let i = 0; i < 20; i++) {
        try {
          await executeRetrievalPipeline(db.db, "memory knowledge", TEST_CONFIG);
        } catch (err: any) {
          if (err?.message?.includes("SQLITE_BUSY") || err?.code === "SQLITE_BUSY") {
            sqliteBusyCount++;
          } else {
            errors.push(`retrieval-${i}: ${err?.message}`);
          }
        }
        await new Promise((r) => setImmediate(r));
      }
    };

    // Worker C: chạy maintenance 3 lần trong khi 2 worker kia chạy
    const maintenanceWorker = async () => {
      for (let i = 0; i < 3; i++) {
        try {
          await runMaintenanceCycle(db.db, testDir, TEST_CONFIG);
        } catch (err: any) {
          if (err?.message?.includes("SQLITE_BUSY") || err?.code === "SQLITE_BUSY") {
            sqliteBusyCount++;
          } else {
            errors.push(`maintenance-${i}: ${err?.message}`);
          }
        }
        await new Promise((r) => setImmediate(r));
      }
    };

    // Chạy song song
    await Promise.all([insertWorker(), retrievalWorker(), maintenanceWorker()]);

    // Report kết quả
    console.log(`[SQLITE_BUSY test] busy count: ${sqliteBusyCount}, other errors: ${errors.length}`);
    if (sqliteBusyCount > 0) {
      console.warn(`WARNING: ${sqliteBusyCount} SQLITE_BUSY error(s) detected — WAL config or transaction duration issue.`);
    }

    // Hệ thống không được crash (không có lỗi nghiêm trọng ngoài SQLITE_BUSY)
    expect(errors).toHaveLength(0);

    // SQLITE_BUSY có thể xảy ra, nhưng không được vượt quá 10% tổng số ops (70 ops)
    expect(sqliteBusyCount).toBeLessThan(7);
  });

  it("DB remains readable after concurrent writes", async () => {
    // Insert song song từ nhiều luồng async (Promise.all giả lập)
    const workers = Array.from({ length: 10 }, (_, workerIdx) =>
      (async () => {
        for (let i = 0; i < 5; i++) {
          ingestChunk(db.db, {
            sourcePath: `worker${workerIdx}/doc-${i}.md`,
            content: `Worker ${workerIdx} doc ${i}: unique content foxtrott-${workerIdx}-${i} kilo memory trace.`,
            source: "memory",
          });
          await new Promise((r) => setImmediate(r));
        }
      })()
    );

    await Promise.all(workers);

    // DB phải readable sau khi tất cả worker xong
    const nodeCount = (db.db.prepare("SELECT COUNT(*) as cnt FROM memory_nodes").get() as any).cnt;
    expect(nodeCount).toBeGreaterThanOrEqual(10); // ít nhất 10 nodes (dedup có thể gộp)

    // FTS phải hoạt động
    const ftsResult = db.db.prepare(
      "SELECT COUNT(*) as cnt FROM memory_nodes_fts WHERE memory_nodes_fts MATCH 'foxtrott*'"
    ).get() as any;
    expect(ftsResult.cnt).toBeGreaterThan(0);
  });

  it("maintenance cycle completes without throwing on non-empty DB", async () => {
    // Insert một lượng data vừa đủ
    const chunks = Array.from({ length: 30 }, (_, i) => ({
      sourcePath: `maintenance-test/doc-${i}.md`,
      content: `Maintenance test entry ${i}: data for hygiene cycle review echo-${i}.`,
      source: "memory" as const,
    }));
    ingestBatch(db.db, chunks);

    // Chạy maintenance — không được throw
    const report = await runMaintenanceCycle(db.db, testDir, TEST_CONFIG);

    expect(report).toBeDefined();
    expect(typeof report.stateTransitions).toBe("number");
    expect(typeof report.staleEdgesPruned).toBe("number");
    expect(report.ftsOptimized).toBe(true);
    console.log("[Maintenance report]", report);
  });

  it("WAL mode survives concurrent read + write without checkpoint failure", async () => {
    // Insert 100 nodes
    for (let i = 0; i < 100; i++) {
      ingestChunk(db.db, {
        sourcePath: `wal-test/doc-${i}.md`,
        content: `WAL stress test content zulu-${i} victor memory persistence layer.`,
        source: "memory",
      });
    }

    // Đọc trong khi WAL có thể đang dirty
    const results = await executeRetrievalPipeline(db.db, "memory persistence", TEST_CONFIG);
    expect(Array.isArray(results)).toBe(true);

    // WAL checkpoint thủ công — không được throw
    expect(() => {
      db.db.pragma("wal_checkpoint(PASSIVE)");
    }).not.toThrow();

    // DB vẫn readable sau checkpoint
    const countAfter = (db.db.prepare("SELECT COUNT(*) as cnt FROM memory_nodes").get() as any).cnt;
    expect(countAfter).toBe(100);
  });
});
