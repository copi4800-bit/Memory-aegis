# PHASE 3: BIAS CALIBRATION (GSD)

## Objective
Chủ động đo lường và triệt tiêu các sai lệch hệ thống (Bias) trong quá trình phán đoán ký ức.

## Key Tasks
1. [ ] Implement `compute_bias_delta` trong Scorer để triệt 4 loại bias chính: Lexical, Recency, Activation, Staleness.
2. [ ] Thêm `BiasTruthBoost` để thưởng cho những ký ức có Lineage (Phả hệ) sạch sẽ.
3. [ ] Viết bộ test "Bias Fairness" để so sánh v9 với các hệ thống scoring gộp kiểu cũ.

## Bias Mitigation Targets
- **Lexical Bias (-lambda_lexb):** Phạt những ký ức có wording giống query bất thường nhưng tín hiệu Truth yếu.
- **Recency Bias (-lambda_recb):** Giảm ưu tiên cho ký ức "mới tinh" nhưng chưa qua kiểm chứng (Trust thấp).
- **Activation Bias (-lambda_actb):** Ngăn chặn ký ức "nổi tiếng" (usage cao) chiếm sóng mãi mãi.
- **Truth Alignment (+lambda_truthb):** Thưởng cho ký ức là Winner và có Evidence mạnh.

## Acceptance Criteria
- [ ] Trong bài test "Lexical vs Truth", sự thật phải thắng dù wording xấu hơn.
- [ ] Ký ức cũ nhưng ổn định phải thắng ký ức mới nhưng "vô căn cứ".
