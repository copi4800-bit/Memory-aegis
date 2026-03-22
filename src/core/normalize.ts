/**
 * Text normalization utilities for Memory Aegis v3.
 * Used by Salmon fingerprinting and entity resolution.
 */

/**
 * Tokenize text into Unicode word tokens.
 * Compatible with OpenClaw's builtin tokenizer.
 */
export function tokenize(text: string): string[] {
  return text.match(/[\p{L}\p{N}_]+/gu)?.map((t) => t.trim()).filter(Boolean) ?? [];
}

/**
 * Tokenize to a Set for Jaccard similarity.
 */
export function tokenizeToSet(text: string): Set<string> {
  return new Set(tokenize(text.toLowerCase()));
}

/**
 * Jaccard similarity between two token sets. Returns [0, 1].
 */
export function jaccardSimilarity(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 && b.size === 0) return 1;
  if (a.size === 0 || b.size === 0) return 0;

  let intersection = 0;
  const smaller = a.size <= b.size ? a : b;
  const larger = a.size <= b.size ? b : a;

  for (const token of smaller) {
    if (larger.has(token)) intersection++;
  }

  const union = a.size + b.size - intersection;
  return union === 0 ? 0 : intersection / union;
}

/**
 * Normalize content for hash comparison.
 * Collapses whitespace, lowercases, strips punctuation.
 */
export function normalizeForHash(content: string): string {
  return content
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, "");
}

/**
 * Extract structural form from content.
 * Used for structure hash — compares logical shape not exact text.
 */
export function extractStructure(content: string): string {
  const lines = content.split("\n");
  const structural: string[] = [];

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (line === "") continue;

    if (/^#{1,6}\s/.test(line)) {
      structural.push("H:" + line.replace(/^#+\s*/, ""));
    } else if (/^[-*+]\s/.test(line)) {
      structural.push("L:" + line.replace(/^[-*+]\s*/, ""));
    } else if (/^\d+\.\s/.test(line)) {
      structural.push("L:" + line.replace(/^\d+\.\s*/, ""));
    } else if (/^[\w.]+\s*[:=]/.test(line)) {
      const key = line.match(/^([\w.]+)\s*[:=]/)?.[1] ?? line.slice(0, 30);
      structural.push("K:" + key);
    } else if (/^```/.test(line)) {
      structural.push("C:block");
    } else {
      structural.push("T:" + line.slice(0, 50));
    }
  }

  return structural.join("\n");
}

/**
 * Build FTS5 query string from raw query.
 * Uses AND for multi-token, with NEAR proximity for relevance.
 */
export function buildFtsQuery(raw: string): string | null {
  const tokens = tokenize(raw);
  if (tokens.length === 0) return null;

  const clean = tokens.map((t) => t.replaceAll('"', ""));
  const quoted = clean.map((t) => `"${t}"`);
  // Prefix variants for partial/stemmed matching
  const prefixed = clean.map((t) => (t.length >= 3 ? `${t}*` : `"${t}"`));

  if (tokens.length >= 2) {
    const nearQuery = `NEAR(${quoted.join(" ")}, 10)`;
    const andQuery = quoted.join(" AND ");
    const prefixOrQuery = prefixed.join(" OR ");
    return `${nearQuery} OR ${andQuery} OR ${prefixOrQuery}`;
  }

  // Single token: exact OR prefix
  return `${quoted[0]} OR ${prefixed[0]}`;
}

/**
 * Convert BM25 rank to [0, 1] score.
 * Same formula as OpenClaw builtin for compatibility.
 */
export function bm25RankToScore(rank: number): number {
  if (!Number.isFinite(rank)) return 1 / (1 + 999);
  if (rank < 0) {
    const relevance = -rank;
    return relevance / (1 + relevance);
  }
  return 1 / (1 + rank);
}

/**
 * Truncate text to maxLength, respecting word boundaries.
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  const truncated = text.slice(0, maxLength);
  const lastSpace = truncated.lastIndexOf(" ");
  return (lastSpace > maxLength * 0.5 ? truncated.slice(0, lastSpace) : truncated) + "...";
}
