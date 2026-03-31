from __future__ import annotations
from typing import Any

TRANSLATIONS: dict[str, dict[str, str]] = {
    "vi": {
        # Trust labels
        "trust_level_v_high": "Cực kỳ tin tưởng",
        "trust_level_high": "Tin tưởng",
        "trust_level_medium": "Trung bình",
        "trust_level_low": "Yếu",
        "trust_level_none": "Chưa xác minh",

        # Readiness labels
        "readiness_level_ready": "Sẵn sàng",
        "readiness_level_good": "Tốt",
        "readiness_level_normal": "Bình thường",
        "readiness_level_faded": "Lờ mờ",
        "readiness_level_latent": "Tiềm tàng",

        # Conflict labels
        "conflict_level_v_high": "Cực kỳ xung đột",
        "conflict_level_high": "Áp lực cao",
        "conflict_level_medium": "Có xung đột",
        "conflict_level_low": "Ổn định",
        "conflict_level_none": "Nhất quán",

        # Signal labels (Generic)
        "signal_v_high": "Rất cao",
        "signal_high": "Cao",
        "signal_medium": "Trung bình",
        "signal_low": "Thấp",
        "signal_critical": "Nghiêm trọng",

        # Narratives (Translator)
        "reason_trust_v_high_evidence": "Em rất tin tưởng vì sếp đã xác nhận rõ ràng.",
        "reason_trust_v_high_stable": "Đây là thông tin ổn định, em đã ghi nhớ sâu.",
        "reason_trust_high": "Thông tin này khớp với ngữ cảnh sếp vừa hỏi.",
        "reason_usage_high": "Dạo này sếp hay nhắc tới việc này.",
        "reason_conflict_high": "⚠️ Có mâu thuẫn nhỏ, sếp xem lại giúp em nhé.",
        "reason_decay_high": "Ký ức này đã hơi cũ rồi.",
        "reason_regret_high": "Em từng nhớ sai chỗ này và đã sửa lại.",
        "reason_fallback": "Phù hợp nhất với bối cảnh hiện tại.",

        # Signal Names for Narratives
        "narrative_trust_v_high": "Gần như tuyệt đối",
        "narrative_trust_high": "Cao",
        "narrative_trust_medium": "Trung bình",
        "narrative_evidence_high": "Có nhiều bằng chứng trực tiếp",
        "narrative_evidence_low": "Dựa trên suy luận gián tiếp",
        "narrative_conflict_high": "Có mâu thuẫn cần giải quyết",
        "narrative_conflict_low": "Nhất quán",
        
        # UI Labels
        "action_remembered": "{honorific} em đã ghi nhớ thông tin này.",
        "action_not_remembered": "Em xin lỗi, em chưa lưu được thông tin này ngay lúc này ạ.",
        "action_updated": "{honorific} em đã cập nhật lại thông tin chính xác rồi ạ.",
        "action_not_updated": "{honorific} hiện tại em chưa cập nhật việc này được ạ.",
        "action_forgotten": "{honorific} em đã xóa thông tin này rồi ạ.",
        "action_not_forgotten": "{honorific} em không tìm thấy thông tin nào về '{query}' để xóa ạ.",
        "label_action": "Hành động",
        "intent_correction": "Sửa đổi",
        "intent_new": "Ghi mới",

        # Recall Responses
        "recall_empty": "{honorific} em không tìm thấy thông tin nào về '{query}' trong bộ nhớ gần đây ạ.",
        "recall_no_active": "{honorific} em không thấy thông tin nào về '{query}' còn hiệu lực trong bộ nhớ ạ.",
        "recall_header": "{honorific} đây là những gì em nhớ được:",
        "recall_conflict_warning": "⚠️ Sếp lưu ý: Em thấy có vài thông tin đang đá nhau, sếp có thể dùng lệnh /memory-clean để em dọn dẹp lại nhé.",
        "trust_prefix_strong": "✅ ",
        "trust_prefix_weak": "⚠️ [Tín hiệu yếu] ",
        "trust_prefix_uncertain": "❓ [Chưa chắc chắn] ",
        "trust_prefix_conflicting": "🔥 [Xung đột] ",
        "suppressed_header": "\n--- Thông tin cũ bị ẩn (để tránh nhiễu) ---",
        "suppressed_reason_superseded": "Thông tin này đã được sếp sửa lại bằng cái mới",
        "suppressed_reason_archived": "Thông tin này đã cũ và được đưa vào kho lưu trữ",

        # Conflict Resolution Prompts (Debt 2 Fix)
        "conflict_prompt_header": "{honorific} em thấy có chút mâu thuẫn trong ký ức về '{subject}':",
        "conflict_choice_newer": "Dùng thông tin mới nhất (ghi nhận lúc {time})",
        "conflict_choice_older": "Giữ lại thông tin cũ (ghi nhận lúc {time})",
        "conflict_choice_both": "Giữ cả hai (đây là hai trường hợp khác nhau)",
        "conflict_reason_contradiction": "Hai thông tin này đang phủ định lẫn nhau.",
        "conflict_reason_correction": "Đây có vẻ là một bản sửa lỗi nhưng em cần sếp xác nhận.",
        "conflict_footer": "Sếp muốn em xử lý thế nào cho chuẩn ạ?",

        # Health & Maintenance (Debt 3 Fix)
        "health_status_perfect": "✨ Sung sức",
        "health_status_good": "✅ Ổn định",
        "health_status_warning": "⚠️ Cần bảo trì",
        "health_status_critical": "🔥 Quá tải",
        "health_summary_perfect": "{honorific} em đang cảm thấy rất 'minh mẫn'! Bộ nhớ của em cực kỳ gọn gàng với {total} ký ức.",
        "health_summary_good": "{honorific} bộ nhớ của em đang hoạt động tốt với {total} ký ức, dù có vài chỗ cần lưu ý nhỏ.",
        "health_summary_warning": "{honorific} em đang thấy hơi 'nặng đầu' một chút vì có {conflicts} xung đột và {stale} thông tin đã cũ.",
        "health_summary_critical": "{honorific} bộ nhớ của em đang bị 'loãng' nghiêm trọng! Em cần sếp giúp dọn dẹp {conflicts} xung đột ngay ạ.",
        "health_issue_conflict": "Phát hiện {count} chủ đề đang mâu thuẫn lẫn nhau.",
        "health_issue_stale": "Có {count} thông tin đã lâu sếp không dùng tới (hơn 30 ngày).",
        "health_action_clean": "Sếp thử dùng lệnh /memory-clean xem sao nhé!",
        "health_action_archive": "Sếp nên cho em lưu trữ (archive) các thông tin cũ này ạ.",
    },
    "en": {
        # Trust labels
        "trust_level_v_high": "Strongly Trusted",
        "trust_level_high": "Trusted",
        "trust_level_medium": "Moderate",
        "trust_level_low": "Weak",
        "trust_level_none": "Unverified",

        # Readiness labels
        "readiness_level_ready": "Ready",
        "readiness_level_good": "Good",
        "readiness_level_normal": "Normal",
        "readiness_level_faded": "Faded",
        "readiness_level_latent": "Latent",

        # Conflict labels
        "conflict_level_v_high": "Strong Conflict",
        "conflict_level_high": "High Pressure",
        "conflict_level_medium": "Conflicting",
        "conflict_level_low": "Stable",
        "conflict_level_none": "Consistent",

        # Signal labels (Generic)
        "signal_v_high": "Very High",
        "signal_high": "High",
        "signal_medium": "Medium",
        "signal_low": "Low",
        "signal_critical": "Critical",

        # Narratives (Translator)
        "reason_trust_v_high_evidence": "I strongly trust this information as it has been mentioned multiple times with clear evidence.",
        "reason_trust_v_high_stable": "This is something I remember deeply and has been confirmed as stable.",
        "reason_trust_high": "This information seems to align well with your intent, and I am monitoring it further.",
        "reason_usage_high": "You've been mentioning this frequently lately, so I've increased its priority.",
        "reason_conflict_high": "However, I noticed a slight conflict with other memories; could you please double-check this for me?",
        "reason_decay_high": "This memory is starting to fade as it hasn't been used in a while.",
        "reason_regret_high": "I previously misremembered this, but I've corrected it after your feedback.",
        "reason_fallback": "This result was selected because it best fits your current context.",

        # Signal Names for Narratives
        "narrative_trust_v_high": "Nearly Absolute",
        "narrative_trust_high": "High",
        "narrative_trust_medium": "Moderate",
        "narrative_evidence_high": "Strong direct evidence",
        "narrative_evidence_low": "Based on indirect inference",
        "narrative_conflict_high": "Conflict detected, resolution needed",
        "narrative_conflict_low": "Consistent",
        
        # UI Labels
        "action_remembered": "I have remembered this information.",
        "action_not_remembered": "I apologize, I couldn't save this information right now.",
        "action_updated": "I have updated the information with the correct details.",
        "action_not_updated": "I am unable to update this information right now.",
        "action_forgotten": "I have forgotten this information.",
        "action_not_forgotten": "I couldn't find any information about '{query}' to forget.",
        "label_action": "Action",
        "intent_correction": "Correction",
        "intent_new": "New Entry",

        # Recall Responses
        "recall_empty": "I couldn't find any information about '{query}' in your recent memory.",
        "recall_no_active": "I don't recall any active information about '{query}' in my memory.",
        "recall_header": "Here is what I remember:",
        "recall_conflict_warning": "⚠️ Note: I've detected some conflicting information. You can use /memory-clean to help me tidy things up.",
        "trust_prefix_strong": "✅ ",
        "trust_prefix_weak": "⚠️ [Weak Signal] ",
        "trust_prefix_uncertain": "❓ [Uncertain] ",
        "trust_prefix_conflicting": "🔥 [Conflict] ",
        "suppressed_header": "\n--- Suppressed Candidates (Why-not) ---",
        "suppressed_reason_superseded": "Old record was superseded",
        "suppressed_reason_archived": "Record was archived",
    }
}

def get_text(key: str, locale: str = "vi") -> str:
    """Retrieves a translated string for a given key and locale."""
    return TRANSLATIONS.get(locale, TRANSLATIONS["vi"]).get(key, key)
