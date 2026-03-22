/**
 * Memory Profile — User-facing summary of "what Aegis remembers about you".
 *
 * Phase 5.2: Tạo profile tóm gọn:
 * - persona (identity)
 * - preferences (style, interaction state)
 * - active projects (context.project)
 * - recurring procedures (workflow)
 * - recent important facts (knowledge)
 */

import type Database from "better-sqlite3";
import type { TaxonomyCategory } from "../core/models.js";

export interface MemoryProfile {
  persona: string[];
  preferences: string[];
  projects: string[];
  procedures: string[];
  recentFacts: string[];
  rules: string[];
  stats: {
    totalActive: number;
    crystallized: number;
    oldestMemory: string | null;
    newestMemory: string | null;
  };
}

/**
 * Build a user-facing memory profile from the knowledge graph.
 */
export function buildMemoryProfile(db: Database.Database): MemoryProfile {
  const profile: MemoryProfile = {
    persona: [],
    preferences: [],
    projects: [],
    procedures: [],
    recentFacts: [],
    rules: [],
    stats: { totalActive: 0, crystallized: 0, oldestMemory: null, newestMemory: null },
  };

  // --- Stats ---
  const statsRow = db.prepare(`
    SELECT
      COUNT(*) as total,
      SUM(CASE WHEN memory_state = 'crystallized' THEN 1 ELSE 0 END) as crystallized,
      MIN(created_at) as oldest,
      MAX(created_at) as newest
    FROM memory_nodes WHERE status = 'active'
  `).get() as any;

  profile.stats = {
    totalActive: statsRow?.total || 0,
    crystallized: statsRow?.crystallized || 0,
    oldestMemory: statsRow?.oldest || null,
    newestMemory: statsRow?.newest || null,
  };

  // --- Persona (identity.*) ---
  profile.persona = querySnippets(db, ["identity.persona", "identity.style"], 5);

  // --- Preferences (interaction state + identity.style) ---
  const interactionRows = db.prepare(`
    SELECT brevity_preference, formality_preference, exploration_preference
    FROM interaction_states
    ORDER BY last_updated_at DESC LIMIT 1
  `).all() as any[];

  if (interactionRows.length > 0) {
    const s = interactionRows[0];
    if (s.brevity_preference > 0.6) profile.preferences.push("Prefers concise responses");
    if (s.brevity_preference < 0.3) profile.preferences.push("Prefers detailed responses");
    if (s.formality_preference > 0.6) profile.preferences.push("Prefers formal tone");
    if (s.formality_preference < 0.3) profile.preferences.push("Prefers casual tone");
    if (s.exploration_preference > 0.6) profile.preferences.push("Likes exploring tangents");
  }

  // --- Active projects (context.project) ---
  profile.projects = querySnippets(db, ["context.project"], 5);

  // --- Procedures (workflow.*) ---
  profile.procedures = querySnippets(db, ["workflow.procedure", "workflow.decision"], 5);

  // --- Recent facts (knowledge.*) ---
  profile.recentFacts = querySnippets(db, ["knowledge.fact", "knowledge.lesson", "knowledge.reference"], 8);

  // --- Rules (policy.*) ---
  profile.rules = querySnippets(db, ["policy.safety", "policy.directive"], 5);

  return profile;
}

/**
 * Query short snippets from memory nodes by taxonomy subjects.
 */
function querySnippets(db: Database.Database, subjects: string[], limit: number): string[] {
  if (subjects.length === 0) return [];

  const placeholders = subjects.map(() => "?").join(", ");
  const rows = db.prepare(`
    SELECT content FROM memory_nodes
    WHERE status = 'active' AND canonical_subject IN (${placeholders})
    ORDER BY importance DESC, updated_at DESC
    LIMIT ?
  `).all(...subjects, limit) as Array<{ content: string }>;

  return rows.map((r) => {
    const text = r.content.trim();
    return text.length > 120 ? text.substring(0, 120) + "..." : text;
  });
}

/**
 * Render profile as human-readable text.
 */
export function renderProfile(profile: MemoryProfile): string {
  const lines: string[] = [];

  lines.push("## Memory Profile");
  lines.push("");

  // Stats header
  const oldest = profile.stats.oldestMemory
    ? new Date(profile.stats.oldestMemory).toLocaleDateString()
    : "N/A";
  lines.push(`Tracking ${profile.stats.totalActive} active memories (${profile.stats.crystallized} crystallized) since ${oldest}`);
  lines.push("");

  // Persona
  if (profile.persona.length > 0) {
    lines.push("### Who you are");
    for (const p of profile.persona) lines.push(`- ${p}`);
    lines.push("");
  }

  // Preferences
  if (profile.preferences.length > 0) {
    lines.push("### Communication preferences");
    for (const p of profile.preferences) lines.push(`- ${p}`);
    lines.push("");
  }

  // Rules
  if (profile.rules.length > 0) {
    lines.push("### Rules & directives");
    for (const r of profile.rules) lines.push(`- ${r}`);
    lines.push("");
  }

  // Projects
  if (profile.projects.length > 0) {
    lines.push("### Active projects");
    for (const p of profile.projects) lines.push(`- ${p}`);
    lines.push("");
  }

  // Procedures
  if (profile.procedures.length > 0) {
    lines.push("### Known workflows");
    for (const p of profile.procedures) lines.push(`- ${p}`);
    lines.push("");
  }

  // Recent facts
  if (profile.recentFacts.length > 0) {
    lines.push("### Recent knowledge");
    for (const f of profile.recentFacts) lines.push(`- ${f}`);
    lines.push("");
  }

  // Empty state
  if (
    profile.persona.length === 0 &&
    profile.preferences.length === 0 &&
    profile.rules.length === 0 &&
    profile.projects.length === 0 &&
    profile.procedures.length === 0 &&
    profile.recentFacts.length === 0
  ) {
    lines.push("No memories stored yet. Start a conversation and Aegis will learn over time.");
    lines.push("");
  }

  return lines.join("\n");
}
