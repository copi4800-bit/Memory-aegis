#!/usr/bin/env node
/**
 * Aegis v4 Quick Setup — Beginner-friendly onboarding CLI.
 */

import { AegisMemoryManager } from "../aegis-manager.js";
import path from "node:path";
import os from "node:os";

async function main() {
  console.log("================================================");
  console.log("   Welcome to Memory Aegis v4 — Quick Setup   ");
  console.log("================================================");
  console.log("");

  const workspaceDir = process.cwd();
  console.log(`- Workspace detected: ${workspaceDir}`);

  try {
    console.log("- Initializing Aegis Manager...");
    const manager = await AegisMemoryManager.create({
      agentId: "aegis-cli-setup",
      workspaceDir,
      config: { preset: "balanced" }
    });

    console.log("- Running Guided Onboarding...");
    const result = await manager.runOnboarding("balanced");

    console.log("");
    console.log(result.summary);
    console.log("");

    if (result.allPassed) {
      console.log("Aegis v4 is now fully automated and active.");
      console.log("You can start chatting, and Aegis will manage your memories behind the scenes.");
    } else {
      console.log("Setup completed with some warnings. Please review the summary above.");
    }

    await manager.close();
  } catch (err) {
    console.error("Critical error during setup:", err);
    process.exit(1);
  }

  console.log("");
  console.log("================================================");
}

main();
