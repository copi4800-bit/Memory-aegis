import os
import sys
import json
from datetime import datetime

# Đảm bảo import được aegis_py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from aegis_py.app import AegisApp
except ImportError as e:
    print(f"Lỗi Import: {e}")
    sys.exit(1)

def run_ux_verification():
    db_path = "verify_ux_human.db"
    telemetry_path = "/tmp/aegis_telemetry.jsonl"
    if os.path.exists(db_path): os.remove(db_path)
    if os.path.exists(telemetry_path): os.remove(telemetry_path)
    
    app = AegisApp(db_path=db_path)
    
    print(f"--- BẮT ĐẦU KIỂM TRA TOÀN DIỆN AEGIS V8 (DONE 100%): {datetime.now().strftime('%H:%M:%S')} ---")
    
    # 1. Kịch bản Why-not: Sếp đổi ý
    print("\n[Bước 1] Sếp dặn: 'Sếp thích uống trà xanh.'")
    app.memory_remember("Sếp thích uống trà xanh.")
    
    print("[Bước 2] Sếp đổi ý: 'Thôi, sếp đổi sang trà lài rồi.'")
    app.memory_correct("Thôi, sếp đổi sang trà lài rồi.") # Cái trà xanh sẽ bị superseded

    # 3. Recall lại để xem Why-not
    print("\n[Bước 3] Em tìm kiếm 'trà' để xem giải thích Why-not...")
    results = app.search("trà", scope_id="default", scope_type="agent")
    
    if results:
        serialized = app._serialize_search_result(results[0], retrieval_mode="explain")
        print(f"\n[Aegis v8 chọn]: {serialized['memory']['content']}")
        print(f"[Lý do nhân hóa]: {serialized['human_reason']}")
        
        if serialized.get("suppressed_candidates"):
            print("\n[TẠI SAO KHÔNG CHỌN CÁI KIA? (WHY-NOT)]:")
            for candidate in serialized["suppressed_candidates"]:
                print(f"  - Ký ức: '{candidate['content']}...'")
                print(f"    Lý do loại: {candidate['reason']}")
        else:
            print("\n[!] Không tìm thấy Suppressed Candidates (Why-not).")

    # 4. Kiểm tra Telemetry Logs
    print("\n--- KIỂM TRA MẮT THẦN (TELEMETRY LOGS) ---")
    if os.path.exists(telemetry_path):
        with open(telemetry_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            print(f"Tổng số Event đã ghi: {len(lines)}")
            print("Event Exposure mới nhất:")
            last_event = json.loads(lines[-1])
            print(json.dumps(last_event, indent=2, ensure_ascii=False))
    else:
        print("[!] Không tìm thấy file Telemetry log.")

    app.close()

if __name__ == "__main__":
    run_ux_verification()
