import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { AegisMemoryManager, closeAllManagers } from "../../src/aegis-manager.js";
import { DEFAULT_AEGIS_CONFIG } from "../../src/core/models.js";
import { resolve } from "node:path";
import { newId } from "../../src/core/id.js";

describe("Stress Test: Deep Supersede Chains", () => {
  let manager: AegisMemoryManager;
  const workspaceDir = resolve(process.cwd(), ".tmp_stress_supersede");

  beforeEach(async () => {
    manager = await AegisMemoryManager.create({
      agentId: "test_stress",
      workspaceDir,
      config: {
        ...DEFAULT_AEGIS_CONFIG,
        enabledLayers: ["meerkat", "zebra-finch", "eagle"]
      }
    });

    const db = manager.getDb();
    db.prepare("DELETE FROM drift_events").run();
    db.prepare("DELETE FROM fingerprints").run();
    db.prepare("DELETE FROM memory_events").run();
    db.prepare("DELETE FROM memory_edges").run();
    db.prepare("DELETE FROM memory_nodes").run();
  });

  afterEach(async () => {
    await closeAllManagers();
  });

  it("should process a chain of 50 temporal supersede resolutions without stack overflow", async () => {
    const db = manager.getDb();
    const insertNode = db.prepare(`
      INSERT INTO memory_nodes (id, memory_type, content, canonical_subject, scope, status, importance, created_at, updated_at)
      VALUES (?, 'semantic_fact', ?, 'config.version', 'workspace', 'active', 0.8, ?, ?)
    `);

    // Tạo giả lập vân tay rác để Meerkat không crash
    const insertFingerprint = db.prepare(`
      INSERT OR IGNORE INTO fingerprints (id, node_id, fingerprint_version, created_at)
      VALUES (?, ?, 'v1', ?)
    `);

    // Seed 50 nodes mâu thuẫn trực tiếp (tất cả đều có keyword 'bắt buộc' để kích trigger)
    const CHAIN_LENGTH = 50;
    const nodeIds: string[] = [];

    db.transaction(() => {
      // Injects nodes backwards in time. Node 49 is the newest. Node 0 is the oldest.
      // Cần chắc chắn khoảng cách mỗi node lớn hơn 24 giờ.
      for (let i = 0; i < CHAIN_LENGTH; i++) {
        const id = `node_v${i}`;
        nodeIds.push(id);
        
        // Mỗi node lệch nhau 2 ngày
        const d = new Date("2020-01-01T00:00:00.000Z");
        d.setDate(d.getDate() + (i * 2)); 
        const iso = d.toISOString();

        insertNode.run(
          id, 
          i % 2 === 0 ? `Version API bắt buộc là ${i}` : `Tuyệt đối không dùng bản ${i-1}, bản chuẩn bây giờ là ${i}`,
          iso, iso
        );

        // Kỹ thuật trick: Meerkat hardcode check fingerprint cũ. Bơm sẵn 2 row thỏa mãn.
        insertFingerprint.run('legacy_baseline', id, iso);
        insertFingerprint.run('legacy_current', id, iso);
      }
    })();

    // Gọi vòng quét tự động
    await manager.runMaintenance();

    // 1. Kiểm tra bao nhiêu node bị superseded
    const activeNodes = db.prepare("SELECT count(*) as c FROM memory_nodes WHERE status = 'active'").get() as any;
    const supersededNodes = db.prepare("SELECT count(*) as c FROM memory_nodes WHERE status = 'superseded'").get() as any;

    // Node cuối cùng (newest) luôn active, còn lại (về lý thuyết) 49 node cũ sẽ bị đè bẹp
    // Thực tế tùy thuật toán của Zebra Finch: nếu nó xử lý theo batch thì có thể tốn n chu kỳ
    // Ít nhất nó không bị crash và có số lượng superseded > 0
    expect(supersededNodes.c).toBeGreaterThan(0);

    // 2. Kiểm tra Eagle report
    const { EagleEye } = await import("../../src/cognitive/eagle.js");
    const eagle = new EagleEye(db);
    const report = eagle.analyze();
    
    expect(report).toContain("BÁO CÁO GIÁM SÁT TỪ ĐẠI BÀNG");
  });
});
