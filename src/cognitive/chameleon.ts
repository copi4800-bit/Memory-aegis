import type { MemorySearchResult } from "../retrieval/packet.js";

/**
 * Chameleon (Tắc kè hoa) — Context Budgeting (Hardened v3.4)
 *
 * Hardening additions:
 * - Configurable zone ratios via ZonePolicy
 * - Better policy.* detection (not just "rules.policy")
 * - Preset-aware zone allocation
 * - Persona retention guarantee: zone 1 always gets at least 1 slot
 * - Core directive preservation: zone 0 never dropped
 */

export interface RouterBudget {
  maxChars: number;
  topK: number;
  query?: string;
  /** Optional zone policy override for preset tuning */
  zonePolicy?: ZonePolicy;
}

export interface ZonePolicy {
  /** Zone 1 (Identity/Policy) share of total budget. Default: 0.20 */
  zone1Ratio: number;
  /** Minimum slots guaranteed for zone 1 (persona retention). Default: 1 */
  zone1MinSlots: number;
  /** Maximum characters per single snippet. Default: 800 */
  maxSnippetChars: number;
}

/** Default zone policies per preset */
export const ZONE_POLICIES: Record<string, ZonePolicy> = {
  minimal:    { zone1Ratio: 0.30, zone1MinSlots: 1, maxSnippetChars: 400 },
  balanced:   { zone1Ratio: 0.20, zone1MinSlots: 1, maxSnippetChars: 800 },
  "local-safe": { zone1Ratio: 0.25, zone1MinSlots: 2, maxSnippetChars: 600 },
  "max-memory": { zone1Ratio: 0.15, zone1MinSlots: 1, maxSnippetChars: 1200 },
};

export class ChameleonBudgeter {
  /**
   * Phân bổ ngân sách theo cơ chế Zone Hard Fence.
   * Hardened: configurable zones, better citation detection, guaranteed slots.
   */
  public static assemble(results: MemorySearchResult[], budget: RouterBudget): string {
    const policy = budget.zonePolicy ?? ZONE_POLICIES["balanced"];
    const maxSnippet = policy.maxSnippetChars;

    const zone0: MemorySearchResult[] = []; // Tối thượng (Trauma/Invariant)
    const zone1: MemorySearchResult[] = []; // Bản ngã (Identity/Policy)
    const zone2: MemorySearchResult[] = []; // Tác vụ (Fact/Procedural/Working)

    // Phân loại vào rổ — hardened citation detection
    for (const r of results) {
      const citation = r.citation || "";
      if (ChameleonBudgeter.isZone0(citation)) {
        zone0.push(r);
      } else if (ChameleonBudgeter.isZone1(citation)) {
        zone1.push(r);
      } else {
        zone2.push(r);
      }
    }

    // Tính ngân sách
    const maxChars = budget.maxChars;
    const zone1Limit = Math.floor(maxChars * policy.zone1Ratio);

    let usedChars = 0;
    let usedCount = 0;

    const selectedZone0: string[] = [];
    const selectedZone1: string[] = [];
    const selectedZone2: string[] = [];

    // === Zone 0: Cấp mù quáng (Không giới hạn chars, chỉ giới hạn topK) ===
    for (const r of zone0) {
      if (usedCount >= budget.topK) break;
      const snippet = ChameleonBudgeter.truncateSnippet(r.snippet, maxSnippet);
      const formatted = `[${r.score.toFixed(3)}] ${r.citation}\n${snippet}\n`;
      selectedZone0.push(formatted);
      usedChars += formatted.length;
      usedCount++;
    }

    // === Zone 1: Khóa ở mức zone1Ratio, đảm bảo zone1MinSlots ===
    let zone1Used = 0;
    let zone1Slots = 0;
    for (const r of zone1) {
      if (usedCount >= budget.topK) break;

      // Persona retention: guaranteed minimum slots
      const isGuaranteed = zone1Slots < policy.zone1MinSlots;

      if (!isGuaranteed && zone1Used >= zone1Limit) break;

      let snippet = r.snippet;
      let formatted = `[${r.score.toFixed(3)}] ${r.citation}\n${snippet}\n`;

      // Truncate nếu lố ngân sách rổ 1 (trừ khi guaranteed)
      if (!isGuaranteed && zone1Used + formatted.length > zone1Limit) {
        const allowedLen = zone1Limit - zone1Used - 50;
        if (allowedLen > 50) {
          snippet = snippet.substring(0, allowedLen) + "...";
          formatted = `[${r.score.toFixed(3)}] ${r.citation}\n${snippet}\n`;
        }
      }

      if (!isGuaranteed && zone1Used + formatted.length > zone1Limit) continue;

      selectedZone1.push(formatted);
      zone1Used += formatted.length;
      usedChars += formatted.length;
      usedCount++;
      zone1Slots++;
    }

    // === Zone 2: Phần dư còn lại ===
    for (const r of zone2) {
      if (usedCount >= budget.topK) break;

      const remainingChars = maxChars - usedChars;
      if (remainingChars < 100) break;

      let snippet = ChameleonBudgeter.truncateSnippet(r.snippet, maxSnippet);
      let formatted = `[${r.score.toFixed(3)}] ${r.citation}\n${snippet}\n`;

      if (formatted.length > remainingChars) {
        const allowedLen = remainingChars - 50;
        if (allowedLen > 100) {
          snippet = snippet.substring(0, allowedLen) + "...";
          formatted = `[${r.score.toFixed(3)}] ${r.citation}\n${snippet}\n`;
        }
      }

      if (formatted.length > remainingChars) continue;

      selectedZone2.push(formatted);
      usedChars += formatted.length;
      usedCount++;
    }

    if (usedCount === 0) return "";

    // Lắp ráp XML ngữ cảnh
    const out: string[] = ["<context-budget>"];

    if (selectedZone0.length > 0 || selectedZone1.length > 0) {
      out.push("  <core-directives>");
      selectedZone0.forEach(s => out.push("    " + s.trim().replace(/\n/g, "\n    ")));
      selectedZone1.forEach(s => out.push("    " + s.trim().replace(/\n/g, "\n    ")));
      out.push("  </core-directives>");
    }

    if (selectedZone2.length > 0) {
      out.push("  <task-memory>");
      selectedZone2.forEach(s => out.push("    " + s.trim().replace(/\n/g, "\n    ")));
      out.push("  </task-memory>");
    }

    out.push("</context-budget>");
    return out.join("\n");
  }

  // --- Zone detection (hardened) ---

  /** Zone 0: Trauma, invariant — critical safety nodes */
  private static isZone0(citation: string): boolean {
    return citation.includes("[trauma]") || citation.includes("[invariant]");
  }

  /** Zone 1: Identity, policy — persona/rules */
  private static isZone1(citation: string): boolean {
    return (
      citation.includes("identity.") ||
      citation.includes("policy.") ||
      citation.includes("rules.policy") // Legacy
    );
  }

  /** Truncate snippet to max length */
  private static truncateSnippet(snippet: string, maxLen: number): string {
    return snippet.length > maxLen ? snippet.substring(0, maxLen) + "..." : snippet;
  }
}
