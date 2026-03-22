import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { AegisMemoryManager, closeAllManagers } from "../../src/aegis-manager.js";
import { DEFAULT_AEGIS_CONFIG } from "../../src/core/models.js";
import { resolve } from "node:path";
import { newId } from "../../src/core/id.js";

describe("Stress Test: Taxonomy Drift & Metadata Flood", () => {
  let manager: AegisMemoryManager;
  const workspaceDir = resolve(process.cwd(), ".tmp_stress_drift");

  beforeEach(async () => {
    manager = await AegisMemoryManager.create({
      agentId: "test_stress",
      workspaceDir,
      config: {
        ...DEFAULT_AEGIS_CONFIG,
        enabledLayers: ["bowerbird", "eagle"]
      }
    });

    const db = manager.getDb();
    // Clear out
    db.prepare("DELETE FROM drift_events").run();
    db.prepare("DELETE FROM memory_events").run();
    db.prepare("DELETE FROM memory_edges").run();
    db.prepare("DELETE FROM memory_nodes").run();
  });

  afterEach(async () => {
    await closeAllManagers();
  });

  it("should survive an injection of 1000 completely unstructured noisy nodes", async () => {
    const db = manager.getDb();
    const insertNode = db.prepare(`
      INSERT INTO memory_nodes (id, memory_type, content, canonical_subject, scope, status, importance, created_at, updated_at)
      VALUES (?, 'semantic_fact', ?, null, 'workspace', 'active', 0.5, datetime('now'), datetime('now'))
    `);

    // 1. Pháo kích (Flood injection): 500 node với content hoàn toàn vô nghĩa và NULL subject
    const insertMany = db.transaction(() => {
      for (let i = 0; i < 500; i++) {
        insertNode.run(newId(), `Junk node #${i}`);
      }
    });
    insertMany();

    // 2. Pháo kích (Targeted injection): 500 node có chứa keyword để Bowerbird bắt được
    const insertRecognizable = db.transaction(() => {
      for (let i = 0; i < 500; i++) {
        insertNode.run(newId(), `Lỗi error TS2304 tại file index.ts ở dòng ${i}.`);
      }
    });
    insertRecognizable();

    // 3. Giai đoạn phân luồng (Taxonomy Hardening)
    const cleanupResult = await manager.runTaxonomyCleanup();
    
    // Bowerbird chỉ nên bắt được 500 node có pattern error log, còn 500 node rác phải bỏ rớt (NULL)
    expect(cleanupResult.classified).toBeGreaterThanOrEqual(100);
    expect(cleanupResult.classified).toBeLessThanOrEqual(500);

    // 4. Đo lường sức chịu đựng qua Eagle
    const { EagleEye } = await import("../../src/cognitive/eagle.js");
    const eagle = new EagleEye(db);
    const report = eagle.analyze();

    // Hệ thống không sụp, báo cáo Eagle vẫn gen ra được
    expect(report).toContain("BÁO CÁO GIÁM SÁT TỪ ĐẠI BÀNG");
    
    // Tổng node_count phải là 1000
    const count = db.prepare("SELECT count(*) as c FROM memory_nodes").get() as any;
    expect(count.c).toBe(1000);
  });
});
