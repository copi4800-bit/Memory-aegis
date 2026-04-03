from __future__ import annotations
from typing import Any

TRANSLATIONS: dict[str, dict[str, str]] = {
    "vi": {
        # --- Perfect UX: User Mode (Natural & Professional) ---
        "action_remembered": "{h_assistant} đã ghi nhận thông tin này ạ.",
        "action_updated": "{h_assistant} đã cập nhật lại theo thông tin mới nhất của {h_user} rồi ạ.",
        "action_forgotten": "{h_assistant} đã cho lùi thông tin này vào quá khứ rồi ạ.",
        "action_not_remembered": "{h_user_prefix}{h_user} {h_assistant} chưa lưu được việc này ngay lúc này, {h_user} đợi {h_assistant} xíu nhé.",
        
        "recall_header": "{h_user_prefix}{h_user} đây là những gì {h_assistant} nhớ được:",
        "recall_empty": "{h_user_prefix}{h_user} {h_assistant} chưa thấy dữ kiện nào về '{query}' trong bộ nhớ gần đây ạ.",
        "recall_no_active": "{h_user_prefix}{h_user} {h_assistant} không thấy thông tin nào về '{query}' còn hiệu lực ạ.",
        
        # --- Perfect UX: Categorized Wording (Sprint 1) ---
        "wording_first_write": "được ghi nhận là sự thật mới",
        "wording_first_write_confirmed": "được {h_user} xác nhận là sự thật hiện tại",
        "wording_correction": "là bản sửa lỗi mới nhất",
        "wording_correction_confirmed": "đã được cập nhật và xác nhận là sự thật mới nhất",
        "wording_conflict": "đang có thông tin chưa khớp nhau, {h_assistant} chưa muốn khẳng định bừa",
        "wording_uncertain": "có dữ kiện liên quan, nhưng chưa đủ sạch để chốt chắc",
        
        # --- Perfect UX: Conflict Awareness (Sprint 3) ---
        "recall_conflict_warning": "⚠️ Chỗ này đang có chút mâu thuẫn, {h_assistant} đang ưu tiên bản mới hơn nhưng {h_user} kiểm tra lại giúp {h_assistant} nhé.",
        "recall_conflict_prompt": "🔥 {h_assistant} đang thấy hai thông tin đá nhau ở phần này. {h_user} muốn {h_assistant} giữ bản nào cho chuẩn ạ?",
        
        "suppressed_header": "\n--- Dữ kiện cũ liên quan (đã bị thay thế) ---",
        "suppressed_reason_superseded": "Thông tin này không còn hiệu lực",
        "suppressed_reason_archived": "Thông tin này đã được đưa vào kho lưu trữ",

        # --- Perfect UX: Health (Sprint 4) ---
        "health_status_perfect": "✨ Minh mẫn",
        "health_status_good": "✅ Ổn định",
        "health_status_warning": "⚠️ Cần lưu ý",
        "health_status_critical": "🔥 Nặng đầu",
        
        "health_summary_perfect": "{h_user_prefix}{h_user} {h_assistant} đang cảm thấy rất minh mẫn! Mọi thứ đều gọn gàng với {total} ký ức.",
        "health_summary_good": "{h_user_prefix}{h_user} {h_assistant} đang hoạt động tốt, đang giữ {total} dữ kiện quan trọng.",
        "health_summary_warning": "{h_user_prefix}{h_user} {h_assistant} đang thấy hơi 'nặng đầu' vì có vài mâu thuẫn cần {h_user} xem qua ạ.",
        "health_summary_critical": "{h_user_prefix}{h_user} {h_assistant} bộ nhớ của {h_assistant} đang bị loãng nghiêm trọng! {h_user} giúp {h_assistant} dọn dẹp các xung đột ngay nhé.",

        # --- Audit & Explain Mode (Lớp 2 & 3) ---
        "reason_trust_v_high": "có độ tin cậy rất cao",
        "reason_usage_high": "được {h_user} nhắc tới thường xuyên",
        "reason_fallback": "phù hợp nhất với bối cảnh hiện tại",
        "trust_prefix_strong": "✅ ",
        "trust_prefix_weak": "❓ ",
        "trust_prefix_conflicting": "⚠️ ",
        "trust_prefix_uncertain": "",
        
        "label_action": "Hành động",
        "intent_correction": "Cập nhật",
        "intent_new": "Ghi mới",
    },
    "en": {
        "action_remembered": "I've noted this down.",
        "action_updated": "I've updated this with your latest information.",
        "action_forgotten": "I've moved this information to the archive.",
        "action_not_remembered": "I couldn't save this right now, {h_user}. One moment please.",
        "recall_empty": "I don't see any active facts for '{query}' recently.",
        "recall_no_active": "No active information found for '{query}'.",
        "wording_first_write_confirmed": "confirmed by {h_user} as current truth",
        "wording_correction": "the latest correction",
        "wording_correction_confirmed": "updated and confirmed as latest truth",
        "wording_conflict": "has conflicting data, I cannot confirm yet",
        "wording_uncertain": "has related data but not clean enough to be certain",
        "reason_trust_v_high": "highly reliable",
        "reason_usage_high": "frequently mentioned by {h_user}",
        "reason_fallback": "best fit for current context",
        "trust_prefix_strong": "✅ ",
        "trust_prefix_weak": "❓ ",
        "trust_prefix_conflicting": "⚠️ ",
        "trust_prefix_uncertain": "",
    }
}

def get_text(key: str, locale: str = "vi") -> str:
    """Retrieves a translated string for a given key and locale."""
    return TRANSLATIONS.get(locale, TRANSLATIONS["vi"]).get(key, key)
