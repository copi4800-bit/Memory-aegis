from aegis_py.app import AegisApp
import os
import json
from datetime import datetime
import shutil

# Dọn dẹp DB cũ để bắt đầu sạch
db_path = "/tmp/aegis_stress_test_extreme.db"
if os.path.exists(db_path):
    os.remove(db_path)

# Khởi tạo Aegis 8 (v7) với ngôn ngữ tiếng Việt
app = AegisApp(db_path=db_path, locale="vi")

def print_result(title, result):
    print(f"\n{'='*20} {title} {'='*20}")
    if isinstance(result, str):
        print(result)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

try:
    # --- TRẬN 1: XUNG ĐỘT DỒN DẬP (CONFLICT BOMBING) ---
    print("\n--- BẮT ĐẦU TRẬN 1: XUNG ĐỘT DỒN DẬP ---")
    
    # Nạp thông tin ban đầu (Preference)
    app.put_memory("Sếp thích uống cà phê đen vào buổi sáng", subject="uống", scope_type="agent", scope_id="default")
    
    # Nạp 4 thông tin mâu thuẫn liên tiếp cùng một chủ đề "uống"
    app.put_memory("Sếp cực kỳ ghét cà phê đen, chỉ thích trà gừng", subject="uống", scope_type="agent", scope_id="default")
    app.put_memory("Sếp chỉ thích uống nước cam, không thích trà hay cà phê", subject="uống", scope_type="agent", scope_id="default")
    app.put_memory("Sếp muốn thử trà đào vào buổi sáng", subject="uống", scope_type="agent", scope_id="default")
    app.put_memory("Quên hết đi, sếp chỉ thích cà phê sữa", subject="uống", scope_type="agent", scope_id="default")

    # Kiểm tra truy vấn khi có nhiều xung đột
    # Xem kết quả chọn cái nào và giải thích (Why This Result)
    recall_conflict = app.memory_recall("sếp thích uống gì", retrieval_mode="explain")
    print_result("KẾT QUẢ RECALL KHI CÓ XUNG ĐỘT", recall_conflict)

    # Kiểm tra Conflict Prompt (UX xử lý xung đột)
    prompts = app.memory_conflict_prompts()
    print_result("CÁC XUNG ĐỘT CẦN XỬ LÝ (ACTIONABLE PROMPTS)", prompts)


    # --- TRẬN 2: SỬA ĐỔI TẦNG SÂU (DEEP CORRECTION) ---
    print("\n--- BẮT ĐẦU TRẬN 2: SỬA ĐỔI TẦNG SÂU ---")
    
    # Nạp một thông tin "cứng" (Stable Preference)
    app.put_memory("Sếp luôn dùng tên 'Hali' để ký tên", subject="tên", scope_type="agent", scope_id="default")
    
    # Ép thay đổi bằng lệnh Correct (Stickiness test)
    app.put_memory("Từ nay sếp đổi tên thành 'Claw Master', đừng dùng tên cũ nữa", subject="tên", scope_type="agent", scope_id="default")
    
    # Truy vấn lại ngay để xem bản mới có "dính" không
    recall_correction = app.memory_recall("tên sếp là gì", retrieval_mode="explain")
    print_result("KIỂM TRA ĐỘ 'DÍNH' CỦA BẢN SỬA ĐỔI", recall_correction)


    # --- TRẬN 3: TRUY VẤN MẬP MỜ (AMBIGUITY TORTURE) ---
    print("\n--- BẮT ĐẦU TRẬN 3: TRUY VẤN MẬP MỜ ---")
    
    # Nạp thông tin mập mờ, không rõ ràng
    app.put_memory("Có vẻ như sếp sắp đi du lịch", subject="du lịch", scope_type="agent", scope_id="default")
    app.put_memory("Sếp có nhắc đến chuyện đi Đà Lạt hay Nha Trang gì đó", subject="du lịch", scope_type="agent", scope_id="default")
    
    # Truy vấn mập mờ để xem 'Why This Result' giải thích độ tin cậy thấp ra sao
    recall_ambiguous = app.memory_recall("sếp đi đâu", retrieval_mode="explain")
    print_result("GIẢI THÍCH KHI DỮ LIỆU MẬP MỜ", recall_ambiguous)


    # --- TRẬN 4: KIỂM TRA SỨC KHỎE (HEALTH CHECK UNDER PRESSURE) ---
    print("\n--- BẮT ĐẦU TRẬN 4: KIỂM TRA SỨC KHỎE ---")
    
    # Xem chẩn đoán tổng quát (Memory Doctor)
    health_summary = app.memory_health_summary()
    print_result("CHẨN ĐOÁN SỨC KHỎE BỘ NHỚ (MEMORY DOCTOR)", health_summary)

finally:
    app.close()
    if os.path.exists(db_path):
        os.remove(db_path)

print("\n--- HOÀN THÀNH STRESS TEST ---")
