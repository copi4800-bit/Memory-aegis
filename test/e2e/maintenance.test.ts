import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { AegisMemoryManager, closeAllManagers } from "../../src/aegis-manager.js";
import { DEFAULT_AEGIS_CONFIG } from "../../src/core/models.js";
import { resolve } from "node:path";

describe("E2E Pipeline: Maintenance-Focused", () => {
  let manager: AegisMemoryManager;
  const workspaceDir = resolve(process.cwd(), ".tmp_e2e_maintenance");

  beforeEach(async () => {
    manager = await AegisMemoryManager.create({
      agentId: "test_e2e",
      workspaceDir,
      config: {
        ...DEFAULT_AEGIS_CONFIG,
        enabledLayers: ["meerkat", "zebra-finch", "scrub-jay", "eagle", "bowerbird"]
      }
    });

    const db = manager.getDb();
    db.prepare("DELETE FROM drift_events").run();
    db.prepare("DELETE FROM fingerprints").run();
    db.prepare("DELETE FROM memory_events").run();
    db.prepare("DELETE FROM memory_edges").run();
    db.prepare("DELETE FROM memory_nodes").run();
    db.prepare("DELETE FROM episodes").run();
  });

  afterEach(async () => {
    await closeAllManagers();
  });

  it("should successfully run Conflict Scan -> Supersede -> Scrub Jay Cleanup -> Telemetry", async () => {
    // 1. Nạp mâu thuẫn (Conflict Injection)
    const db = manager.getDb();
    const insertNode = db.prepare(`
      INSERT INTO memory_nodes (id, memory_type, content, canonical_subject, scope, status, importance, created_at, updated_at, source_path)
      VALUES (?, ?, ?, ?, ?, 'active', 0.8, ?, ?, null)
    `);

    insertNode.run(
      "old_port_node", "semantic_fact",
      "Port mặc định của project bắt buộc là 3000.",
      "config.port", "workspace", "2024-01-01T10:00:00.000Z", "2024-01-01T10:00:00.000Z"
    );

    insertNode.run(
      "new_port_node", "semantic_fact",
      "Tuyệt đối không dùng port 3000, port mới được thống nhất là 8080.",
      "config.port", "workspace", "2024-01-03T10:00:00.000Z", "2024-01-03T10:00:00.000Z"
    );

    // Bơm dấu vân tay giả (Fingerprints) để thỏa mãn Foreign Key constraint của Meerkat
    db.prepare(`
      INSERT OR IGNORE INTO fingerprints (id, node_id, fingerprint_version, created_at)
      VALUES 
        ('legacy_baseline', 'old_port_node', 'v1', datetime('now')),
        ('legacy_current', 'new_port_node', 'v1', datetime('now'))
    `).run();

    // 2. Kích hoạt Maintenance Pipeline (Meerkat & Zebra Finch & Bowerbird)
    await manager.runMaintenance();

    // 3. Kiểm tra kết quả Supersede (Zebra Finch)
    const oldNode = db.prepare("SELECT id, status FROM memory_nodes WHERE id = ?").get("old_port_node") as any;
    const newNode = db.prepare("SELECT id, status FROM memory_nodes WHERE id = ?").get("new_port_node") as any;

    // Meerkat scans the conflict, Zebra Finch flags the older one as superseded
    expect(oldNode.status).toBe("superseded");
    expect(newNode.status).toBe("active");

    // 4. Báo cáo Telemetry (Eagle)
    const { EagleEye } = await import("../../src/cognitive/eagle.js");
    const eagle = new EagleEye(db);
    const report = eagle.analyze();
    
    // Báo cáo phải cập nhật trạng thái
    expect(report).toContain("BÁO CÁO GIÁM SÁT TỪ ĐẠI BÀNG");
    // Eagle could identify superseded counts, but we at least expect no massive unresolved conflicts
    expect(report).not.toContain("bốc cháy");
  });
});
