# PHASE 5: EXPLAINABILITY 2.0 (GSD)

## Objective
Xây dựng hệ thống giải thích trung thực (Faithful Explanation) dựa trên cấu trúc toán học 3 tầng của v9.

## Key Tasks
1. [ ] Cập nhật `ResidualScorer` để ghi lại chi tiết từng thành phần điểm (Trace factors).
2. [ ] Xây dựng `FaithfulRenderer` trong `translator.py` để dịch Trace sang tiếng Việt nhân bản.
3. [ ] Implement logic xác định "Decisive Factor" (Yếu tố quyết định): Yếu tố nào làm thay đổi thứ hạng nhiều nhất.
4. [ ] Viết bộ test "Explain Faithfulness".

## Explanation Levels
- **Base Level:** Khớp ngữ nghĩa, từ khóa, phạm vi.
- **Judge Level:** Tin cậy, sửa lỗi, xử lý mâu thuẫn.
- **Life Level:** Độ tươi mới, sự đào thải, củng cố.

## Acceptance Criteria
- [ ] Lời giải thích phải nêu rõ được tầng nào đã đưa ký ức vào và tầng nào đã đẩy nó lên đầu.
- [ ] Nếu một ký ức thắng nhờ sửa lỗi (Correction), Aegis phải nói rõ điều đó.
