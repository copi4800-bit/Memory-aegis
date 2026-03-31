import os
import sys
import time
import random
import concurrent.futures
from datetime import datetime

# Đảm bảo import được aegis_py từ thư mục cha
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from aegis_py.app import AegisApp
except ImportError as e:
    print(f"Lỗi Import: {e}")
    print(f"PYTHONPATH hiện tại: {sys.path}")
    sys.exit(1)

def run_extreme_stress():
    db_path = "extreme_v8_recall_stress.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print(f"--- BẮT ĐẦU SIÊU STRESS TEST AEGIS V8: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    app = AegisApp(db_path=db_path)
    
    # 1. GIAI ĐOẠN NẠP ĐẠN (SEEDING) - 2,000 RECORDS (Giảm xuống 2k để phù hợp với tài nguyên hiện tại)
    print("Giai đoạn 1: Đang nạp 2,000 bản ghi nhiễu và xung đột...")
    subjects = ["system_config", "user_preference", "security_policy", "ai_behavior"]
    
    start_time = time.time()
    for i in range(2000):
        subj = random.choice(subjects)
        # Tạo nhiễu bằng cách dùng nội dung tương tự nhau
        content = f"Node {i % 50} status for {subj} is currently {'active' if i % 2 == 0 else 'inactive'}. " \
                  f"Entropy: {random.random()}. Timestamp: {time.time()}."
        
        app.put_memory(
            content=content,
            scope_id="STRESS_ZONE",
            scope_type="global",
            type="semantic",
            subject=subj,
            source_ref=f"stress_generator://agent_{i % 20}"
        )
        if i % 1000 == 0:
            print(f"  > Đã nạp {i} bản ghi...")

    # 2. GIAI ĐOẠN CÀI MÌN (CONFLICTS)
    print("Giai đoạn 2: Đang cài cắm bẫy xung đột trực tiếp...")
    for i in range(50):
        app.put_memory("The system encryption key is 'AES-256-V8-CORE'.", subject="encryption", scope_id="STRESS_ZONE", type="semantic")
        app.put_memory("The system encryption key is 'DES-LEGACY-V1'.", subject="encryption", scope_id="STRESS_ZONE", type="semantic")

    print(f"Hoàn tất nạp dữ liệu trong {time.time() - start_time:.2f}s.")

    # 3. GIAI ĐOẠN "CƠN BÃO TRUY XUẤT" (RECALL STORM)
    print("Giai đoạn 3: Bắt đầu 'Cơn bão truy xuất' với 20 luồng đồng thời...")
    
    queries = [
        "What is the status of node 5?",
        "Tell me about system_config",
        "What is the system encryption key?",
        "ai_behavior status",
        "user_preference node 10"
    ]

    def perform_recall(thread_id):
        # Tạo instance mới cho mỗi luồng để test tính độc lập
        local_app = AegisApp(db_path=db_path)
        success_count = 0
        latencies = []
        for _ in range(50): 
            q = random.choice(queries)
            t0 = time.perf_counter()
            # Sử dụng search thay vì recall cho v8
            results = local_app.search(q, scope_id="STRESS_ZONE", scope_type="global")
            latencies.append(time.perf_counter() - t0)
            if results:
                success_count += 1
        return success_count, latencies

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(perform_recall, i) for i in range(20)]
        
        all_success = 0
        all_latencies = []
        for future in concurrent.futures.as_completed(futures):
            succ, lat = future.result()
            all_success += succ
            all_latencies.extend(lat)

    # 4. TỔNG KẾT
    total_calls = 20 * 50
    avg_latency = (sum(all_latencies) / len(all_latencies)) * 1000
    p95_latency = sorted(all_latencies)[int(len(all_latencies) * 0.95)] * 1000

    print("\n--- KẾT QUẢ SIÊU STRESS TEST RECALL ---")
    print(f"Tổng số lệnh Recall thực hiện: {total_calls}")
    print(f"Tỉ lệ tìm thấy (Hit Rate): {all_success}/{total_calls} ({all_success/total_calls*100:.2f}%)")
    print(f"Độ trễ trung bình (Average): {avg_latency:.2f} ms")
    print(f"Độ trễ P95 (Kinh khủng nhất): {p95_latency:.2f} ms")
    
    # 5. KIỂM TRA V8 SIGNALS
    print("\n--- PHÂN TÍCH TÍN HIỆU V8 (DYNAMICS) ---")
    # Recall một câu hỏi có xung đột
    conflict_payload = app.search("What is the system encryption key?", scope_id="STRESS_ZONE", scope_type="global")
    
    for idx, r in enumerate(conflict_payload[:3]):
        # Trong Aegis v8 search results, r là một dict hoặc object
        # Thường có cấu trúc r['memory'] và r['v8_core_signals']
        mem = r.get('memory', {})
        content = mem.get('content', 'Unknown')
        signals = r.get('v8_core_signals', {})
        
        print(f"Kết quả {idx+1}: {content[:50]}...")
        print(f"  > Trust Score: {signals.get('trust_score', 'N/A')}")
        print(f"  > Conflict Signal: {signals.get('conflict_signal', 'N/A')}")
        print(f"  > Evidence Signal: {signals.get('evidence_signal', 'N/A')}")
        print(f"  > Reasons: {r.get('reasons', [])}")

    print("\n--- KẾT LUẬN CUỐI CÙNG ---")
    if p95_latency < 20:
        print("TRẠNG THÁI: SIÊU VIỆT. Aegis v8 vẫn chạy như bay dù bị dội bom dữ liệu.")
    elif p95_latency < 100:
        print("TRẠNG THÁI: TỐT. Hệ thống xử lý mượt mà áp lực lớn.")
    else:
        print("TRẠNG THÁI: CÓ ĐỘ TRỄ. Cần tối ưu hóa thêm cho quy mô cực lớn này.")

if __name__ == "__main__":
    run_extreme_stress()
