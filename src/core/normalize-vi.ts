/**
 * Vietnamese diacritic normalization.
 * Maps tones and base vowel modifications to their ASCII equivalents.
 * Used for fuzzy term matching — "dùng" and "dụng" both normalize to "dung".
 */

const TONE_MAP: Record<string, string> = {
  // a variants
  "à": "a", "á": "a", "ả": "a", "ã": "a", "ạ": "a",
  "ă": "a", "ắ": "a", "ặ": "a", "ằ": "a", "ẳ": "a", "ẵ": "a",
  "â": "a", "ấ": "a", "ậ": "a", "ầ": "a", "ẩ": "a", "ẫ": "a",
  // e variants
  "è": "e", "é": "e", "ẻ": "e", "ẽ": "e", "ẹ": "e",
  "ê": "e", "ế": "e", "ệ": "e", "ề": "e", "ể": "e", "ễ": "e",
  // i variants
  "ì": "i", "í": "i", "ỉ": "i", "ĩ": "i", "ị": "i",
  // o variants
  "ò": "o", "ó": "o", "ỏ": "o", "õ": "o", "ọ": "o",
  "ô": "o", "ố": "o", "ộ": "o", "ồ": "o", "ổ": "o", "ỗ": "o",
  "ơ": "o", "ớ": "o", "ợ": "o", "ờ": "o", "ở": "o", "ỡ": "o",
  // u variants
  "ù": "u", "ú": "u", "ủ": "u", "ũ": "u", "ụ": "u",
  "ư": "u", "ứ": "u", "ự": "u", "ừ": "u", "ử": "u", "ữ": "u",
  // y variants
  "ỳ": "y", "ý": "y", "ỷ": "y", "ỹ": "y", "ỵ": "y",
  // d with stroke
  "đ": "d",
};

/**
 * Normalize a Vietnamese word by stripping tones and base vowel modifications.
 * Pure ASCII input is returned unchanged.
 * Example: "dùng" → "dung", "dụng" → "dung", "TypeScript" → "typescript"
 */
export function normalizeVietnamese(word: string): string {
  return word.split("").map(c => TONE_MAP[c] ?? c).join("");
}
