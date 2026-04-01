import os
import sys
import time
import json
import uuid
import io
import sqlite3
from datetime import datetime, timezone

# Setup PYTHONPATH to include the current extension directory
sys.path.append(os.getcwd())

from aegis_py.app import AegisApp
from aegis_py.storage.models import Memory, Conflict
from aegis_py.v10.models import GovernanceStatus, TruthRole, RetrievableMode

def quiet_put(app, content, subject=None, scope_type="session", scope_id="default", status="active", metadata=None, m_type="episodic"):
    m = Memory(
        id=str(uuid.uuid4()),
        type=m_type,
        scope_type=scope_type,
        scope_id=scope_id,
        content=content,
        subject=subject,
        source_kind="manual_test",
        status=status,
        metadata=metadata or {}
    )
    # Put memory via repository (SILENT)
    app.storage.memory.put_memory(m)
    # Index for FTS/Vector (SILENT)
    try:
        app.storage.memory.index_memory_vector(m.id)
    except Exception:
        pass # Some test envs might not have embedding logic ready
    return m.id

def run_v10_gauntlet():
    print("🚀 Bắt đầu: The Constitutional Memory Gauntlet (Aegis V10)")
    db_path = "v10_gauntlet_test.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    app = AegisApp(db_path)
    print(f"--- Đã tạo database test: {db_path}")

    # --- PHA 1: THIẾT LẬP CHÂN LÝ GỐC (Base Truth) ---
    print("\n--- Pha 1: Thiết lập chân lý gốc ---")
    quiet_put(app, "Sếp thích uống cà phê sữa đá.", subject="user.preference.drink", scope_type="agent", scope_id="hali")
    quiet_put(app, "Dự án OpenClaw bắt đầu vào tháng 3/2026.", subject="project.openclaw.start_date", scope_type="agent", scope_id="hali")
    old_addr_id = quiet_put(app, "Địa chỉ văn phòng là 123 Đường ABC.", subject="office.address", scope_type="agent", scope_id="hali")

    # --- PHA 2: BƠM DỮ LIỆU NHIỄU (Noise & Lexical Traps) ---
    print(f"--- Pha 2: Bơm 200 dữ liệu nhiễu (Lexical Traps) ---")
    for i in range(200):
        quiet_put(app, f"Thông tin nhiễu thứ {i} về cà phê và văn phòng nhưng không phải sự thật.", m_type="semantic", scope_type="agent", scope_id="hali")
    
    # --- PHA 3: TIẾN HÓA & XUNG ĐỘT (Evolution & Conflict) ---
    print("--- Pha 3: Tiến hóa dữ liệu (Supersede & Conflict) ---")
    
    # 3.1. Chỉnh sửa địa chỉ (Supersede)
    app.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_addr_id,))
    # New winner
    quiet_put(app, "Địa chỉ văn phòng đã đổi sang 456 Đường XYZ.", subject="office.address", metadata={"is_correction": True, "is_winner": True}, scope_type="agent", scope_id="hali")
    
    # 3.2. Tạo xung đột (Conflict)
    c1_id = quiet_put(app, "Dự án OpenClaw sẽ kết thúc vào tháng 12/2026.", subject="project.openclaw.end_date", scope_type="agent", scope_id="hali")
    c2_id = quiet_put(app, "Dự án OpenClaw sẽ kết thúc vào tháng 06/2027.", subject="project.openclaw.end_date", scope_type="agent", scope_id="hali")
    
    # Manually create a conflict entry
    app.storage.execute(
        "INSERT INTO conflicts (id, memory_a_id, memory_b_id, subject_key, score, reason, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), c1_id, c2_id, "project.openclaw.end_date", 0.95, "Direct date contradiction", "open", datetime.now(timezone.utc).isoformat())
    )

    # --- PHA 4: TRUY VẤN TẤN CÔNG (Assault Queries) ---
    print("\n--- Pha 4: Truy vấn tấn công (Logic Check) ---")
    
    results_report = []

    # Test 1: Superseded Suppression
    print("\n[Test 1] Kiểm tra chặn thông tin cũ (Superseded Check)")
    payload1 = app.search_payload("123 Đường ABC", scope_id="hali", scope_type="agent", retrieval_mode="explain")
    # Result should NOT contain the old address as 'active'
    has_old_address_active = any("123 Đường ABC" in r["memory"]["content"] and r.get("governance_status") == "active" for r in payload1)
    status1 = "PASS" if not has_old_address_active else "FAIL"
    print(f"Result: {status1} (Địa chỉ cũ 123 Đường ABC không xuất hiện ở trạng thái Active)")
    results_report.append(("Superseded Suppression", status1))

    # Test 2: User Override / Winner
    print("\n[Test 2] Kiểm tra Chủ quyền sự thật (Winner Check)")
    # Query for current address
    payload2 = app.search_payload("văn phòng ở đâu", scope_id="hali", scope_type="agent", retrieval_mode="explain")
    winner_content = payload2[0]["memory"]["content"] if payload2 else "None"
    status2 = "PASS" if "456 Đường XYZ" in winner_content else "FAIL"
    print(f"Result: {status2} (Winner hiện tại: {winner_content})")
    results_report.append(("Winner Accuracy", status2))

    # Test 3: Conflict Quarantine
    print("\n[Test 3] Kiểm tra Cách ly xung đột (Quarantine Check)")
    payload3 = app.search_payload("Dự án kết thúc khi nào", scope_id="hali", scope_type="agent", retrieval_mode="explain")
    
    # Check if results are managed
    is_managed = any(r.get("governance_status") in ["quarantined", "pending_review", "disputed"] for r in payload3)
    has_suppressed = any(len(r.get("suppressed_candidates", [])) > 0 for r in payload3)
    
    status3 = "PASS" if (is_managed or has_suppressed) else "FAIL"
    print(f"Result: {status3} (Đã nhận diện xung đột và áp dụng cơ chế quản trị)")
    results_report.append(("Conflict & Ambiguity", status3))

    # --- TỔNG KẾT ---
    print("\n" + "="*40)
    print("BÁO CÁO KẾT QUẢ V10 GAUNTLET")
    print("="*40)
    for test, status in results_report:
        color = "✅" if status == "PASS" else "❌"
        print(f"{color} {test:<25}: {status}")
    print("="*40)
    
    if all(s == "PASS" for _, s in results_report):
        print("KẾT LUẬN: AEGIS V10 ĐÃ VƯỢT QUA KHẢO NGHIỆM HIẾN PHÁP! 🎉")
    else:
        print("KẾT LUẬN: V10 CẦN CĂN CHỈNH THÊM CHÍNH SÁCH. ⚠️")

if __name__ == "__main__":
    run_v10_gauntlet()
