import os
import sys
import json

# Setup PYTHONPATH to include the current extension directory
sys.path.append(os.getcwd())

from aegis_py.facade import Aegis

def run_demo():
    print("🚀 Bắt đầu Demo Aegis v10 Facade (Zero-Config)")
    
    # 1. Khởi tạo cực nhanh - Luôn dùng DB sạch cho demo
    db_file = "facade_demo_v10.db"
    for suffix in ["", "-wal", "-shm", "-journal"]:
        p = f"{db_file}{suffix}"
        if os.path.exists(p):
            try:
                os.remove(p)
            except:
                pass
        
    mem = Aegis.auto(db_file)
    print(f"✅ Trạng thái: {mem.status()['state']}")

    # 2. Ghi nhớ thông tin ban đầu
    print("\n📝 Ghi nhớ: 'Sở thích của tôi là nước ép dâu.'")
    mem.remember("Sở thích của tôi là nước ép dâu.", subject="user.preference.drink")

    # 3. Truy vấn thử
    print("\n🔍 Recall: 'Tôi thích uống gì?'")
    results = mem.recall("Tôi thích uống gì?")
    if results:
        print(f"   > Aegis trả lời: {results[0]['memory']['content']}")
        print(f"   > Giải thích: {results[0]['human_reason']}")

    # 4. Đính chính thông tin (Truth Correction)
    print("\n🔄 Đính chính: 'Bây giờ tôi thích sinh tố bơ hơn.'")
    mem.correct("Bây giờ tôi thích sinh tố bơ hơn.", subject="user.preference.drink")

    # 5. Truy vấn lại để xem Governance hoạt động
    print("\n🔍 Recall lại: 'Tôi thích uống gì?'")
    results = mem.recall("Tôi thích uống gì?")
    if results:
        print(f"   > Aegis trả lời: {results[0]['memory']['content']}")
        print(f"   > Governance Status: {results[0].get('governance_status')}")
        print(f"   > Giải thích: {results[0]['human_reason']}")

    # 6. Kiểm tra Conflict Quarantine
    print("\n⚔️ Tạo xung đột trực tiếp...")
    mem.remember("Mật mã cửa là 1234.", subject="door.code")
    mem.remember("Mật mã cửa là 5678.", subject="door.code")
    
    # Giả lập tạo conflict record (v10 Facade sẽ tự động hóa hơn trong tương lai)
    # Ở đây ta check xem v10 engine có tự động detect khi tìm kiếm không
    print("\n🔍 Recall mật mã cửa:")
    results = mem.recall("Mật mã cửa là bao nhiêu?")
    if results:
        # Nếu có conflict nặng, v10 sẽ quarantine hoặc đánh dấu disputed
        top = results[0]
        print(f"   > Trạng thái: {top.get('governance_status')}")
        print(f"   > Lý do: {top['human_reason']}")
    else:
        print("   > (Hệ thống không trả về kết quả vì đang có xung đột cần review)")

    print("\n📊 Tổng kết trạng thái hệ thống:")
    print(json.dumps(mem.status(), indent=2))

if __name__ == "__main__":
    run_demo()
