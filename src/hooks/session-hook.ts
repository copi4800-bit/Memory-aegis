/**
 * Session lifecycle hooks for OpenClaw integration.
 */

import type { AegisMemoryManager } from "../aegis-manager.js";
import { prewarm, consolidateSession, flushPending } from "../cognitive/dolphin.js";

export function createSessionHooks(getManager: () => AegisMemoryManager | null) {
  return {
    async onSessionStart(sessionKey: string): Promise<void> {
      const manager = getManager();
      if (!manager) return;

      if (manager.layerEnabled("dolphin")) {
        prewarm(manager.getDb(), sessionKey);
      }
    },

    async onSessionEnd(sessionKey: string): Promise<void> {
      const manager = getManager();
      if (!manager) return;

      if (manager.layerEnabled("dolphin")) {
        consolidateSession(manager.getDb(), sessionKey);
        flushPending(manager.getDb());
      }

      // Run maintenance on session end
      void manager.runMaintenance();
    },
  };
}
