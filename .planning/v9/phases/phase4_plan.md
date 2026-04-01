# PHASE 4: LIFECYCLE STABILIZATION (GSD)

## Objective
Thiết lập cơ chế điều tiết ký ức theo thời gian và sự đào thải, đảm bảo bộ não luôn tươi mới và không bị "loãng" bởi thông tin cũ.

## Key Tasks
1. [ ] Hoàn thiện toán tử `compute_life_delta` với logic Decay (giảm dần theo thời gian) và Staleness (lỗi thời theo ngữ cảnh).
2. [ ] Implement `ReuseReinforcement`: Thưởng cho ký ức đã được verify qua thực tế sử dụng.
3. [ ] Áp dụng `Lifecycle Non-Domination Constraint`: Đảm bảo vòng đời không bao giờ đè chết sự thật (Truth > Lifecycle).
4. [ ] Viết bộ test "Stability vs Decay".

## Mathematical Operators
- **Decay (-lambda_d):** Giảm mềm theo công thức $1 - e^{-\mu \Delta t}$.
- **Staleness (-lambda_st):** Phạt ký ức "đúng ngày xưa nhưng nay đã khác".
- **Reuse (+lambda_u):** Thưởng logarit cho số lần sử dụng thành công.

## Acceptance Criteria
- [ ] Ký ức cũ, không dùng, không là winner phải bị loại bỏ khỏi top kết quả.
- [ ] Ký ức "Gạo cội" (ổn định, reuse cao) phải đứng vững trước sự tấn công của thông tin mới "vô căn cứ".
