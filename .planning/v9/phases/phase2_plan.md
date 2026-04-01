# PHASE 2: CORRECTION & CONFLICT HARDENING (GSD)

## Objective
Chốt hạ logic xử lý sửa lỗi (Correction) và mâu thuẫn (Conflict) ở tầng toán học và ràng buộc cứng (Hard Constraints).

## Key Tasks
1. [ ] Implement `intent-sensitive` logic trong Scorer (Normal Recall vs. Conflict Probe).
2. [ ] Xây dựng `HardConstraintEngine` để đảm bảo "Sự thật mới luôn thắng".
3. [ ] Viết bộ test "Gauntlet" cho các tình huống xung đột phức tạp.

## Acceptance Criteria
- [ ] Correction Winner phải thắng tuyệt đối trong `normal_recall`.
- [ ] Conflict phải được phơi bày rõ ràng trong `conflict_probe`.
- [ ] Không có tình trạng "ông nói gà bà nói vịt" trong kết quả top-1.

## Calibration Targets
- `lambda_c` (Normal Recall) = 0.4 (Suppress mạnh)
- `lambda_c` (Conflict Probe) = 0.0 (Surfacing)
- `tau_slot_winner` = 0.15 (Margin tối thiểu)
