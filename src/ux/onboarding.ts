/**
 * Guided Onboarding — First-time setup flow.
 *
 * Phase 5.3: Lần đầu cài:
 * 1. Chọn preset
 * 2. Health check
 * 3. Test lưu nhớ thử
 * 4. Test gọi lại thử
 * 5. Summary
 */

import type Database from "better-sqlite3";
import { AegisDoctor, type DoctorReport } from "../maintenance/doctor.js";
import { ingestChunk } from "../core/ingest.js";
import { fts5Search } from "../retrieval/fts-search.js";
import type { AegisPreset } from "../core/presets.js";

export interface OnboardingResult {
  preset: AegisPreset;
  healthCheck: { passed: boolean; report: DoctorReport };
  storeTest: { passed: boolean; nodeId?: string };
  recallTest: { passed: boolean; found: boolean };
  summary: string;
  allPassed: boolean;
}

/**
 * Run the full onboarding flow.
 */
export function runOnboarding(
  db: Database.Database,
  workspaceDir: string,
  dbPath: string,
  preset: AegisPreset = "balanced",
): OnboardingResult {
  const result: OnboardingResult = {
    preset,
    healthCheck: { passed: false, report: {} as DoctorReport },
    storeTest: { passed: false },
    recallTest: { passed: false, found: false },
    summary: "",
    allPassed: false,
  };

  // Step 1: Health check
  const doctor = new AegisDoctor(db, workspaceDir, dbPath);
  const report = doctor.diagnose();
  result.healthCheck = {
    passed: report.summary.status !== "broken",
    report,
  };

  // Step 2: Store test
  try {
    const testContent = "Aegis onboarding test — this is a temporary memory to verify the store pipeline works correctly.";
    const nodeId = ingestChunk(db, {
      sourcePath: "onboarding-test",
      content: testContent,
      source: "memory",
      scope: "global",
    });
    result.storeTest = { passed: true, nodeId };
  } catch {
    result.storeTest = { passed: false };
  }

  // Step 3: Recall test
  try {
    const results = fts5Search(db, "aegis onboarding test verify store pipeline");
    result.recallTest = {
      passed: true,
      found: results.length > 0,
    };
  } catch {
    result.recallTest = { passed: false, found: false };
  }

  // Step 4: Cleanup test node
  if (result.storeTest.nodeId) {
    try {
      db.prepare("DELETE FROM memory_nodes WHERE id = ?").run(result.storeTest.nodeId);
      db.prepare("DELETE FROM fingerprints WHERE node_id = ?").run(result.storeTest.nodeId);
      db.prepare("DELETE FROM memory_events WHERE node_id = ?").run(result.storeTest.nodeId);
    } catch {
      // Non-critical cleanup failure
    }
  }

  // Summary
  result.allPassed = result.healthCheck.passed && result.storeTest.passed && result.recallTest.passed;
  result.summary = renderOnboardingResult(result);

  return result;
}

function renderOnboardingResult(r: OnboardingResult): string {
  const lines: string[] = [];

  lines.push("## Aegis Setup Complete");
  lines.push("");
  lines.push(`Preset: **${r.preset}**`);
  lines.push("");

  const check = (ok: boolean) => ok ? "[OK]" : "[FAIL]";

  lines.push("### Checks");
  lines.push(`${check(r.healthCheck.passed)} Database & workspace`);
  lines.push(`${check(r.storeTest.passed)} Store pipeline`);
  lines.push(`${check(r.recallTest.passed)} Recall pipeline`);
  lines.push(`${check(r.recallTest.found)} FTS index working`);
  lines.push("");

  if (r.allPassed) {
    lines.push("All checks passed. Aegis is ready.");
    lines.push("");
    lines.push("**Quick start:**");
    lines.push("- Aegis auto-captures context from your conversations");
    lines.push("- Use `/recall <query>` to search your memory");
    lines.push("- Use `/remember <info>` to store important information");
    lines.push("- Use `/memory-status` to check memory health");
  } else {
    lines.push("Some checks failed. Review the issues below:");
    lines.push("");
    if (!r.healthCheck.passed) {
      lines.push("- Database or workspace issue:");
      for (const iss of r.healthCheck.report.summary.issues) {
        lines.push(`  - ${iss}`);
      }
    }
    if (!r.storeTest.passed) {
      lines.push("- Store pipeline failed — check database permissions");
    }
    if (!r.recallTest.passed) {
      lines.push("- Recall pipeline failed — FTS index may need rebuilding");
    }
  }

  return lines.join("\n");
}
