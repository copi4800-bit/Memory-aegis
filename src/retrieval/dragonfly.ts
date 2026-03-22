import type Database from "better-sqlite3";
import { bm25RankToScore } from "../core/normalize.js";
import { type FtsResult } from "./fts-search.js";

/**
 * Meganeura Mode (Dragonfly V2) — 100% Local Semantic-lite Rescue (Hardened v3.2)
 *
 * Chiến thuật:
 * 1. Multi-hop Synonym Expansion (Nội suy đa tầng)
 * 2. Trigram/N-gram Fuzzy Matching (Khớp mảnh từ)
 * 3. Fallback LIKE
 *
 * Hardening additions:
 * - shouldRescue(): Kiểm tra xem FTS hit đã đủ mạnh chưa, nếu mạnh thì skip rescue
 * - Confidence score cho mỗi rescue result
 * - Noise filter: loại kết quả quá ngắn hoặc chỉ match trigram rác
 * - Latency guard: giới hạn số token scan
 */

export interface RescueResult extends FtsResult {
  rescueConfidence: number;       // 0.0 - 1.0
  rescueStrategy: "synonym" | "trigram" | "direct"; // Chiến thuật nào bắt được
}

export class DragonflySentry {
  /** Ngưỡng FTS score tối thiểu để coi là "đủ mạnh" — skip rescue */
  static readonly FTS_STRONG_THRESHOLD = 0.4;
  /** Số token scan tối đa (latency guard) */
  static readonly MAX_SCAN_TOKENS = 30;
  /** Content tối thiểu để kết quả không bị coi là noise */
  static readonly MIN_CONTENT_LENGTH = 15;

  constructor(private db: Database.Database) {}

  /**
   * Kiểm tra xem có nên chạy rescue hay không.
   * Trả về false nếu FTS đã có kết quả đủ mạnh.
   */
  public static shouldRescue(ftsResults: FtsResult[]): boolean {
    if (ftsResults.length === 0) return true;
    // Nếu top result có score >= threshold → FTS đã hit tốt, không cần rescue
    const topScore = Math.max(...ftsResults.map(r => r.score));
    return topScore < DragonflySentry.FTS_STRONG_THRESHOLD;
  }

  /**
   * Rescue: Chạy tìm kiếm n-gram/fuzzy/synonym khi FTS5 trượt mục tiêu.
   * Hardened: thêm confidence, noise filter, latency guard.
   */
  public async rescue(query: string, limit = 5): Promise<RescueResult[]> {
    // 1. Mở rộng query bằng synonyms (Multi-hop)
    const expandedTokens = this.expandQuery(query, 2); // 2 hops

    // 2. Tạo Trigrams từ các token chính để bắt sai chính tả nặng
    const baseTokens: string[] = query.toLowerCase().match(/[\p{L}\p{N}_]+/gu) ?? [];
    const trigrams = this.generateTrigrams(baseTokens);

    const allSearchTokens = Array.from(new Set([...expandedTokens, ...trigrams]));
    if (allSearchTokens.length === 0) return [];

    const results: Map<string, RescueResult> = new Map();

    // Ưu tiên các token/trigram dài >= 3
    const keyTokens = allSearchTokens
      .filter(t => t.length >= 3)
      .slice(0, DragonflySentry.MAX_SCAN_TOKENS); // Latency guard
    if (keyTokens.length === 0) return [];

    // Track strategy source cho mỗi token
    const synonymSet = new Set(expandedTokens.filter(t => !baseTokens.includes(t)));
    const trigramSet = new Set(trigrams);

    const findSimilar = this.db.prepare(`
      SELECT
        mn.id as nodeId,
        mn.content,
        mn.memory_type as memoryType,
        mn.scope,
        mn.importance
      FROM memory_nodes mn
      WHERE mn.status = 'active'
        AND mn.memory_state != 'archived'
        AND (content LIKE ? OR canonical_subject LIKE ?)
      ORDER BY mn.importance DESC
      LIMIT ?
    `);

    for (const token of keyTokens) {
      const isDirectMatch = baseTokens.includes(token);
      const isSynonym = synonymSet.has(token);
      const matchWeight = isDirectMatch ? 0.6 : (isSynonym ? 0.4 : 0.25);
      const strategy: RescueResult["rescueStrategy"] = isDirectMatch ? "direct" : (isSynonym ? "synonym" : "trigram");

      const pattern = `%${token}%`;
      const rows = findSimilar.all(pattern, pattern, limit) as any[];

      for (const row of rows) {
        // Noise filter: skip content quá ngắn
        if (row.content.length < DragonflySentry.MIN_CONTENT_LENGTH) continue;

        const currentScore = matchWeight * row.importance;

        if (!results.has(row.nodeId)) {
          results.set(row.nodeId, {
            nodeId: row.nodeId,
            score: currentScore,
            content: row.content,
            memoryType: row.memoryType,
            scope: row.scope,
            rescueConfidence: matchWeight,
            rescueStrategy: strategy,
          });
        } else {
          // Cộng dồn điểm khi khớp nhiều mảnh/từ (trần 0.85)
          const existing = results.get(row.nodeId)!;
          existing.score = Math.min(0.85, existing.score + (currentScore * 0.3));
          // Upgrade strategy: direct > synonym > trigram
          if (strategy === "direct") existing.rescueStrategy = "direct";
          else if (strategy === "synonym" && existing.rescueStrategy === "trigram") existing.rescueStrategy = "synonym";
          existing.rescueConfidence = Math.min(0.9, existing.rescueConfidence + matchWeight * 0.2);
        }
      }
    }

    return Array.from(results.values())
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);
  }

  /**
   * Expansion: Mở rộng query bằng từ đồng nghĩa mức độ nhẹ từ DB (hỗ trợ đa tầng).
   */
  public expandQuery(query: string, maxDepth = 1): string[] {
    const tokens = query.toLowerCase().match(/[\p{L}\p{N}_]+/gu) ?? [];
    const expanded = new Set<string>(tokens);

    const getSyns = this.db.prepare(`
      SELECT synonym FROM dragonfly_synonyms WHERE word = ?
    `);

    let currentFrontier = [...tokens];
    
    for (let depth = 0; depth < maxDepth; depth++) {
      const nextFrontier: string[] = [];
      for (const token of currentFrontier) {
        const syns = getSyns.all(token) as Array<{ synonym: string }>;
        for (const s of syns) {
          if (!expanded.has(s.synonym)) {
            expanded.add(s.synonym);
            nextFrontier.push(s.synonym);
          }
        }
      }
      currentFrontier = nextFrontier;
      if (currentFrontier.length === 0) break;
    }

    return Array.from(expanded);
  }

  /**
   * Trigram Generation: Cắt từ thành các mảnh 3 ký tự (ví dụ: "setup" -> "set", "etu", "tup").
   * Giúp bắt dính các từ sai chính tả cục bộ (ví dụ: "serup").
   */
  private generateTrigrams(tokens: string[]): string[] {
    const trigrams = new Set<string>();
    for (const token of tokens) {
      if (token.length >= 4) { // Chỉ cắt các từ dài từ 4 chữ trở lên để tránh noise
        for (let i = 0; i <= token.length - 3; i++) {
          trigrams.add(token.substring(i, i + 3));
        }
      }
    }
    return Array.from(trigrams);
  }
}
