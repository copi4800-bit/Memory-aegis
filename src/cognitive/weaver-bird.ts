import type Database from "better-sqlite3";
import { nowISO, newId } from "../core/id.js";

/**
 * WeaverBird (Chim Dòng Dọc) — v4.0
 *
 * Nhiệm vụ: Xâu chuỗi các dòng sự kiện, tin nhắn sử dụng Tool của Agent
 * để dệt thành một Procedural Blueprint (Sách Hướng Dẫn).
 *
 * Hardening additions:
 * - Blueprint versioning: mỗi goal có version tăng dần
 * - Confidence via success/fail tracking
 * - Fact vs Procedure distinction: không lưu blueprint nếu < 2 tool calls
 * - Prevent stale blueprints: supersede version cũ thay vì giữ song song
 */

export interface BlueprintMeta {
  version: number;
  successRate: number; // 0.0 - 1.0
  toolCount: number;
}

export class WeaverBird {

  /**
   * Phân tích thô (Passive Shadow Log) mảng messages từ OpenClaw
   * để tạo ra một đoạn Blueprint mô tả cách giải quyết tác vụ.
   *
   * Hardened: trả về null nếu < 2 unique tool calls (fact, không phải procedure).
   */
  public static extractProceduralBlueprint(messages: any[], userGoal: string): string | null {
    if (!messages || messages.length === 0) return null;

    const toolCalls: Array<{ name: string; args: any }> = [];

    for (const msg of messages) {
      if (!msg || typeof msg !== "object") continue;

      // OpenAI Format
      if (Array.isArray(msg.tool_calls)) {
        for (const tc of msg.tool_calls) {
          if (tc?.function?.name) {
            let args = "";
            try { args = JSON.parse(tc.function.arguments); } catch { args = tc.function.arguments; }
            toolCalls.push({ name: tc.function.name, args });
          }
        }
      }

      // Anthropic/OpenClaw JSON Format
      if (Array.isArray(msg.content)) {
        for (const block of msg.content) {
          if (block.type === "tool_use" && block.name) {
            toolCalls.push({ name: block.name, args: block.input });
          } else if (block.type === "call" && block.function) {
            toolCalls.push({ name: block.function, args: block.input || block.arguments });
          }
        }
      }
    }

    if (toolCalls.length === 0) return null;

    // Tóm lược thành Blueprint
    // Lọc trùng tool call gần nhau để blueprint đỡ rác
    const uniqueSequence: string[] = [];
    let lastTool = "";
    for (const call of toolCalls) {
      if (call.name !== lastTool || call.name === "run_command") {
        uniqueSequence.push(call.name);
        lastTool = call.name;
      }
    }

    // Hardened: Fact vs Procedure distinction
    // < 2 unique tools → đây là fact/observation, không phải procedure
    if (uniqueSequence.length < 2) return null;

    const shortGoal = userGoal.split('\n').map(s => s.trim()).filter(Boolean)[0] || "Unknown Goal";

    const lines = [
      `# Mẫu Định Tuyến Quy Trình (Procedural Blueprint)`,
      `**Mục tiêu (Bối cảnh):** ${shortGoal.substring(0, 150)}${shortGoal.length > 150 ? "..." : ""}`,
      ``,
      `**Trình tự Tool thực thi thành công:**`
    ];

    uniqueSequence.forEach((t, i) => lines.push(`${i + 1}. Sử dụng tool \`${t}\``));

    lines.push(``);
    lines.push(`*Blueprint này được tự động quan sát và dệt bởi Weaver Bird. Agent có thể tham khảo trình tự tool này khi xử lý tác vụ tương tự để tránh đi vào ngõ cụt.*`);

    return lines.join("\n");
  }

  /**
   * Lưu Blueprint vào DB.
   * Hardened: version tracking + supersede version cũ cùng goal.
   */
  public static saveBlueprint(db: Database.Database, blueprintContent: string, goalFingerprint?: string): BlueprintMeta {
    const now = nowISO();
    let version = 1;

    // Tìm version cũ cùng goal → supersede
    if (goalFingerprint) {
      const existing = db.prepare(`
        SELECT id, blueprint_version, blueprint_success_count, blueprint_fail_count
        FROM memory_nodes
        WHERE memory_type = 'procedural'
          AND canonical_subject = 'workflow.procedure'
          AND status = 'active'
          AND content LIKE ?
        ORDER BY blueprint_version DESC
        LIMIT 1
      `).get(`%${goalFingerprint.substring(0, 80)}%`) as {
        id: string; blueprint_version: number;
        blueprint_success_count: number; blueprint_fail_count: number;
      } | undefined;

      if (existing) {
        version = (existing.blueprint_version || 0) + 1;
        // Supersede version cũ thay vì giữ song song
        db.prepare(`
          UPDATE memory_nodes SET status = 'superseded', updated_at = ? WHERE id = ?
        `).run(now, existing.id);
      }
    }

    const id = newId();
    db.prepare(`
      INSERT INTO memory_nodes (
        id, memory_type, content, canonical_subject, scope, status,
        importance, salience, memory_state, created_at, updated_at,
        blueprint_version, blueprint_success_count, blueprint_fail_count
      ) VALUES (?, 'procedural', ?, 'workflow.procedure', 'session', 'active',
        0.8, 0.8, 'stable', ?, ?,
        ?, 0, 0)
    `).run(id, blueprintContent, now, now, version);

    return { version, successRate: 0, toolCount: 0 };
  }

  /**
   * Report outcome of a blueprint execution.
   * Hardened: Track success/fail để tính confidence.
   */
  public static reportOutcome(db: Database.Database, blueprintId: string, success: boolean): void {
    const col = success ? "blueprint_success_count" : "blueprint_fail_count";
    db.prepare(`
      UPDATE memory_nodes
      SET ${col} = ${col} + 1, updated_at = ?
      WHERE id = ? AND memory_type = 'procedural'
    `).run(nowISO(), blueprintId);
  }

  /**
   * Tính confidence (success rate) cho một blueprint.
   */
  public static getConfidence(db: Database.Database, blueprintId: string): number {
    const row = db.prepare(`
      SELECT blueprint_success_count, blueprint_fail_count
      FROM memory_nodes WHERE id = ?
    `).get(blueprintId) as { blueprint_success_count: number; blueprint_fail_count: number } | undefined;

    if (!row) return 0;
    const total = (row.blueprint_success_count || 0) + (row.blueprint_fail_count || 0);
    if (total === 0) return 0.5; // Default neutral confidence for new blueprints
    return (row.blueprint_success_count || 0) / total;
  }
}
