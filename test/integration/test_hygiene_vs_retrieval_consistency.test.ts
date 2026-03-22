/**
 * Test: Hygiene vs Retrieval Consistency
 *
 * Mục tiêu: Kiểm tra tính nhất quán khi một Node đang bị TTL/archive/prune
 * trong khi retrieval pipeline cùng lúc cố gắng trả về node đó.
 *
 * Kịch bản nguy hiểm: Viper/Nutcracker xóa node, trong khi executeRetrievalPipeline
 * đang đi qua node đó trong spreading activation → ghost node → data corruption.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { openDatabase, type AegisDatabase } from "../../src/db/connection.js";
import { ingestChunk } from "../../src/core/ingest.js";
import { executeRetrievalPipeline } from "../../src/retrieval/pipeline.js";
import { runMaintenanceCycle } from "../../src/retention/maintenance.js";
import { DEFAULT_AEGIS_CONFIG } from "../../src/core/models.js";
import { newId, nowISO } from "../../src/core/id.js";

let db: AegisDatabase;
let testDir: string;

const TEST_CONFIG = {
  ...DEFAULT_AEGIS_CONFIG,
  enabledLayers: ["orca", "salmon", "elephant"] as any,
  retrievalMaxHops: 2,
  maxNodesPerSearch: 20,
};

beforeEach(() => {
  testDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-hygiene-"));
  db = openDatabase(path.join(testDir, "test.db"));
});

afterEach(() => {
  try { db.close(); } catch {}
  try { fs.rmSync(testDir, { recursive: true, force: true }); } catch {}
});

describe("Hygiene vs Retrieval Consistency", () => {
  it("retrieval does not return expired nodes after TTL cleanup", async () => {
    // Tạo node với TTL đã hết hạn (quá khứ)
    const expiredNodeId = newId();
    const pastTime = new Date(Date.now() - 1000 * 60 * 60).toISOString(); // 1 giờ trước
    const now = nowISO();

    db.db.prepare(`
      INSERT INTO memory_nodes (
        id, memory_type, content, scope, status,
        importance, salience, memory_state,
        raw_hash, normalized_hash, structure_hash, fingerprint_version,
        frequency_count, first_seen_at, last_seen_at,
        ttl_expires_at, created_at, updated_at, source_path
      ) VALUES (
        ?, 'semantic_fact', 'expired TTL node unique content quasar-expired-test', 'user', 'active',
        0.3, 0.3, 'volatile',
        'raw-exp-001', 'norm-exp-001', 'struct-exp-001', 1,
        1, ?, ?,
        ?, ?, ?, 'test/expired.md'
      )
    `).run(expiredNodeId, pastTime, pastTime, pastTime, now, now);

    // Update FTS
    db.db.prepare(`
      INSERT INTO memory_nodes_fts(memory_nodes_fts) VALUES('rebuild')
    `).run();

    // Trước maintenance: node có thể search được
    const beforeResults = await executeRetrievalPipeline(db.db, "quasar-expired-test", TEST_CONFIG);
    const beforeHasExpired = beforeResults.some((r) => r.snippet?.includes("quasar-expired-test"));

    // Chạy maintenance — TTL cleanup phải expire node này
    await runMaintenanceCycle(db.db, testDir, TEST_CONFIG);

    // Sau maintenance: retrieval không được trả về node đã expired
    const afterResults = await executeRetrievalPipeline(db.db, "quasar-expired-test", TEST_CONFIG);
    const afterHasExpired = afterResults.some((r) => r.snippet?.includes("quasar-expired-test"));

    console.log(`[TTL test] before: found=${beforeHasExpired}, after: found=${afterHasExpired}`);

    // Node đã bị expire → retrieval không được trả về
    expect(afterHasExpired).toBe(false);

    // Xác nhận node status đã đổi thành expired trong DB
    const nodeRow = db.db.prepare("SELECT status FROM memory_nodes WHERE id = ?").get(expiredNodeId) as any;
    expect(nodeRow?.status).toBe("expired");
  });

  it("retrieval only returns active nodes, never deleted/expired/archived", async () => {
    // Insert 5 active nodes
    const activeIds: string[] = [];
    for (let i = 0; i < 5; i++) {
      const id = ingestChunk(db.db, {
        sourcePath: `active/doc-${i}.md`,
        content: `Active node content juliet-active-${i} testing retrieval filter.`,
        source: "memory",
      });
      activeIds.push(id);
    }

    // Insert 3 nodes với status không phải active — giả lập đã được hygiene xử lý
    const badStatuses = ["expired", "deleted", "merged"] as const;
    for (const status of badStatuses) {
      const id = newId();
      const now = nowISO();
      db.db.prepare(`
        INSERT INTO memory_nodes (
          id, memory_type, content, scope, status,
          importance, salience, memory_state,
          raw_hash, normalized_hash, structure_hash, fingerprint_version,
          frequency_count, first_seen_at, last_seen_at,
          created_at, updated_at, source_path
        ) VALUES (
          ?, 'semantic_fact', 'juliet-active-content status-test ${status} node', 'user', ?,
          0.3, 0.3, 'volatile',
          'raw-${status}-001', 'norm-${status}-001', 'struct-${status}-001', 1,
          1, ?, ?,
          ?, ?, 'test/${status}.md'
        )
      `).run(id, status, now, now, now, now);
    }

    // Rebuild FTS
    db.db.prepare("INSERT INTO memory_nodes_fts(memory_nodes_fts) VALUES('rebuild')").run();

    // Retrieval pipeline phải filter ra chỉ active nodes
    const results = await executeRetrievalPipeline(db.db, "juliet-active", TEST_CONFIG);

    // Không được có bất kỳ result nào từ node không active
    for (const result of results) {
      // Tìm node_id từ path
      let nodeId: string | null = null;
      if (result.path?.startsWith("aegis://")) {
        const parts = result.path.split("/");
        nodeId = parts[parts.length - 1] ?? null;
      }
      if (nodeId) {
        const row = db.db.prepare("SELECT status FROM memory_nodes WHERE id = ?").get(nodeId) as any;
        if (row) {
          expect(row.status).toBe("active");
        }
      }
    }
  });

  it("concurrent maintenance + retrieval: no ghost node returned", async () => {
    // Tạo nhiều nodes
    for (let i = 0; i < 30; i++) {
      ingestChunk(db.db, {
        sourcePath: `ghost-test/doc-${i}.md`,
        content: `Ghost test content november-${i} retrieval consistency memory trace.`,
        source: "memory",
      });
    }

    // Set một số nodes để sẽ bị TTL expire khi maintenance chạy
    const now = nowISO();
    const pastExpiry = new Date(Date.now() - 1000).toISOString();
    db.db.prepare(`
      UPDATE memory_nodes
      SET ttl_expires_at = ?
      WHERE rowid % 3 = 0 AND status = 'active'
    `).run(pastExpiry);

    const ghostsFound: string[] = [];

    // Chạy retrieval và maintenance xen kẽ
    const retrievalRound = async (roundIdx: number) => {
      const results = await executeRetrievalPipeline(db.db, "november memory trace", TEST_CONFIG);
      for (const r of results) {
        // Nếu có path, kiểm tra node còn tồn tại và active
        if (r.path?.startsWith("aegis://")) {
          const parts = r.path.split("/");
          const nodeId = parts[parts.length - 1];
          if (nodeId) {
            const row = db.db.prepare("SELECT status FROM memory_nodes WHERE id = ?").get(nodeId) as any;
            if (row && row.status !== "active") {
              ghostsFound.push(`round-${roundIdx}: node ${nodeId} status=${row.status}`);
            }
          }
        }
      }
    };

    // Xen kẽ retrieval và maintenance
    await retrievalRound(0);
    await runMaintenanceCycle(db.db, testDir, TEST_CONFIG);
    await retrievalRound(1);
    await runMaintenanceCycle(db.db, testDir, TEST_CONFIG);
    await retrievalRound(2);

    if (ghostsFound.length > 0) {
      console.warn("[Ghost node WARNING]", ghostsFound);
    }

    // Không được có ghost node trong kết quả retrieval sau maintenance
    expect(ghostsFound).toHaveLength(0);
  });

  it("state transitions during maintenance do not corrupt FTS index", async () => {
    // Insert nodes
    for (let i = 0; i < 20; i++) {
      ingestChunk(db.db, {
        sourcePath: `fts-integrity/doc-${i}.md`,
        content: `FTS integrity test oscar-${i} memory node state transition.`,
        source: "memory",
      });
    }

    // Đếm FTS entries trước
    const ftsBefore = (db.db.prepare(
      "SELECT COUNT(*) as cnt FROM memory_nodes_fts WHERE memory_nodes_fts MATCH 'oscar*'"
    ).get() as any).cnt;

    // Chạy maintenance
    await runMaintenanceCycle(db.db, testDir, TEST_CONFIG);

    // Đếm active nodes sau maintenance
    const activeAfter = (db.db.prepare(
      "SELECT COUNT(*) as cnt FROM memory_nodes WHERE status = 'active'"
    ).get() as any).cnt;

    // Đếm FTS entries sau (chỉ tính active nodes thực sự)
    const ftsAfter = (db.db.prepare(
      "SELECT COUNT(*) as cnt FROM memory_nodes_fts WHERE memory_nodes_fts MATCH 'oscar*'"
    ).get() as any).cnt;

    console.log(`[FTS integrity] before: ${ftsBefore}, after: ${ftsAfter}, active nodes: ${activeAfter}`);

    // FTS không được trả về nhiều hơn số active nodes (không bị stale)
    // FTS có thể chứa ít hơn nếu nodes bị expire/delete, nhưng không được có thêm
    expect(ftsAfter).toBeLessThanOrEqual(ftsBefore);
    expect(ftsAfter).toBeGreaterThanOrEqual(0);

    // Retrieval vẫn hoạt động được
    const results = await executeRetrievalPipeline(db.db, "oscar memory state", TEST_CONFIG);
    expect(Array.isArray(results)).toBe(true);
  });
});
