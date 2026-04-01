import os
import sys
import time
import json
import uuid
import random
from datetime import datetime, timezone

# Setup PYTHONPATH to include the current extension directory
sys.path.append(os.getcwd())

from aegis_py.app import AegisApp
from aegis_py.storage.models import Memory, Conflict
from aegis_py.v10.models import GovernanceStatus, TruthRole, RetrievableMode

class SuperStressV10:
    def __init__(self, db_path="super_stress_v10.db"):
        print(f"🏗️ Khởi tạo Super Stress Test V10 tại: {db_path}")
        if os.path.exists(db_path):
            os.remove(db_path)
        self.app = AegisApp(db_path)
        self.db_path = db_path
        self.oracle_truth = {} # Map slot_id -> expected winner memory_id
        self.stats = {
            "total_put": 0,
            "start_time": time.time()
        }

    def quiet_put(self, content, subject=None, scope_type="agent", scope_id="default", status="active", metadata=None, m_type="episodic"):
        m = Memory(
            id=str(uuid.uuid4()),
            type=m_type,
            scope_type=scope_type,
            scope_id=scope_id,
            content=content,
            subject=subject,
            source_kind="manual",
            status=status,
            confidence=1.0,
            activation_score=1.0,
            metadata=metadata or {}
        )
        if "admission_state" not in m.metadata:
            m.metadata["admission_state"] = "validated"
        
        self.app.storage.memory.put_memory(m)
        
        # Tạo evidence events để tăng evidence_strength (cần 5+ để đạt 1.0)
        for _ in range(5):
            self.app.storage.create_evidence_event(
                scope_type=scope_type,
                scope_id=scope_id,
                raw_content=content,
                source_kind="manual",
                memory_id=m.id
            )
            
        # Index FTS/Vector
        try:
            self.app.storage.memory.index_memory_vector(m.id)
        except:
            pass
            
        self.stats["total_put"] += 1
        return m.id

    def bulk_put(self, memories_data):
        """Batch insert memories and evidence for performance."""
        conn = self.app.storage._get_connection()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        
        # Batch insert memories
        memory_rows = []
        evidence_rows = []
        
        for data in memories_data:
            m_id = str(uuid.uuid4())
            metadata = data.get("metadata", {})
            if "admission_state" not in metadata:
                metadata["admission_state"] = "validated"
                
            memory_rows.append((
                m_id, data.get("type", "episodic"), data.get("scope_type", "agent"),
                data.get("scope_id", "default"), data.get("content"), data.get("subject"),
                "manual", "active", 1.0, 1.0, 0, now, now, json.dumps(metadata)
            ))
            
            # 5 evidence events per memory
            for _ in range(5):
                evidence_rows.append((
                    str(uuid.uuid4()), data.get("scope_type", "agent"), data.get("scope_id", "default"),
                    data.get("content"), "manual", m_id, now
                ))
                
        cursor.executemany("""
            INSERT INTO memories (id, type, scope_type, scope_id, content, subject, source_kind, status, confidence, activation_score, access_count, created_at, updated_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, memory_rows)
        
        cursor.executemany("""
            INSERT INTO evidence_events (id, scope_type, scope_id, raw_content, source_kind, memory_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, evidence_rows)
        
        conn.commit()
        self.stats["total_put"] += len(memory_rows)
        return [row[0] for row in memory_rows]

    def phase1_corpus_generator(self):
        print("\n--- Tầng 1: Corpus Generator (Biển dữ kiện - MAX SCALE) ---")
        
        # 1. Sinh 100,000 noise memories
        print("🌊 Đang sinh 100,000 noise memories (Bulk)...")
        batch_size = 5000
        for i in range(0, 100000, batch_size):
            noise_batch = [
                {
                    "content": f"Dữ liệu nhiễu thứ {j} về {uuid.uuid4().hex[:8]}",
                    "type": "semantic"
                } for j in range(i, min(i + batch_size, 100000))
            ]
            self.bulk_put(noise_batch)
            print(f"  > Đã nạp {min(i + batch_size, 100000)}/100,000...", end="\r")
        print()
        
        # 2. Sinh 1,000 Fact Slots
        print("📌 Đang sinh 1,000 Fact Slots...")
        for i in range(1000):
            slot_id = f"fact.slot.{i}"
            content = f"Giá trị chuẩn của slot {i} là {uuid.uuid4().hex[:4]}."
            m_id = self.quiet_put(content, subject=slot_id, metadata={"is_winner": True})
            self.oracle_truth[slot_id] = m_id
            
        # 3. Sinh Duplicate Clusters
        print("👯 Đang sinh duplicate clusters cho 200 slots...")
        for i in range(200):
            slot_id = f"fact.slot.{i}"
            for j in range(5):
                self.quiet_put(f"Biến thể duplicate {j} của slot {i}: {self.oracle_truth[slot_id][:8]}...", subject=slot_id)

        # 4. Sinh User Preference Overrides
        print("👤 Đang sinh 500 User Preferences...")
        for i in range(500):
            slot_id = f"user.pref.{i}"
            content = f"Người dùng {i} thích cài đặt {uuid.uuid4().hex[:4]}."
            m_id = self.quiet_put(content, subject=slot_id, scope_type="consumer", scope_id="user_123", metadata={"is_correction": True})
            self.oracle_truth[f"{slot_id}@user_123"] = m_id

    def phase2_event_injector(self):
        print("\n--- Tầng 2: Event Injector (Biến động hệ thống) ---")
        
        # 1. Supersede old facts
        print("🔄 Superseding 100 facts...")
        for i in range(800, 900):
            slot_id = f"fact.slot.{i}"
            old_id = self.oracle_truth[slot_id]
            # Mark old as superseded
            self.app.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_id,))
            # Create new winner
            new_content = f"Giá trị MỚI ĐÃ CẬP NHẬT của slot {i} là NEW_{uuid.uuid4().hex[:4]}."
            new_id = self.quiet_put(new_content, subject=slot_id, metadata={"is_correction": True, "is_winner": True})
            self.oracle_truth[slot_id] = new_id

        # 2. Inject Direct Conflicts
        print("⚔️ Injecting 100 conflicts...")
        for i in range(600, 700):
            slot_id = f"fact.slot.{i}"
            c1_id = self.quiet_put(f"Thông tin A về {slot_id}: Trắng.", subject=slot_id)
            c2_id = self.quiet_put(f"Thông tin B về {slot_id}: Đen.", subject=slot_id)
            
            # Create conflict
            self.app.storage.execute(
                "INSERT INTO conflicts (id, memory_a_id, memory_b_id, subject_key, score, reason, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), c1_id, c2_id, slot_id, 0.99, "Direct contradiction", "open", datetime.now(timezone.utc).isoformat())
            )
            # Both are candidates, no winner for now in oracle
            self.oracle_truth[slot_id] = "CONFLICT"

    def phase3_query_assault(self):
        print("\n--- Tầng 3: Query Assault Engine (Tấn công truy vấn) ---")
        self.results = []
        
        # Test 1: Long-term Override Recall
        print("🔍 Testing Long-term Override Recall...")
        for i in range(20):
            slot_id = f"user.pref.{i}"
            expected_id = self.oracle_truth[f"{slot_id}@user_123"]
            payload = self.app.search_payload(f"cài đặt {i}", scope_id="user_123", scope_type="consumer", retrieval_mode="explain")
            
            winner_id = payload[0]["memory"]["id"] if payload else None
            status = "PASS" if winner_id == expected_id else "FAIL"
            self.results.append(("Override Recall", status, f"Slot {i}"))

        # Test 2: Superseded Suppression
        print("🔍 Testing Superseded Suppression...")
        for i in range(800, 820):
            slot_id = f"fact.slot.{i}"
            payload = self.app.search_payload(f"Giá trị của slot {i}", scope_id="default", scope_type="agent", retrieval_mode="explain")
            
            has_superseded = any(r.get("governance_status") == "superseded" for r in payload)
            has_active_winner = any(r.get("governance_status") == "active" and r["memory"]["id"] == self.oracle_truth[slot_id] for r in payload)
            
            status = "PASS" if has_active_winner and not has_superseded else "FAIL"
            self.results.append(("Superseded Suppression", status, f"Slot {i}"))

        # Test 3: Conflict Quarantine
        print("🔍 Testing Conflict Quarantine...")
        for i in range(600, 620):
            slot_id = f"fact.slot.{i}"
            payload = self.app.search_payload(f"Thông tin về {slot_id}", scope_id="default", scope_type="agent", retrieval_mode="explain")
            
            is_quarantined = any(r.get("governance_status") in ["quarantined", "pending_review", "disputed"] for r in payload)
            if not is_quarantined and len(payload) > 0:
                if payload[0].get("governance_status") == "active":
                    is_quarantined = False
                else:
                    is_quarantined = True
            elif len(payload) == 0:
                is_quarantined = True
                
            status = "PASS" if is_quarantined else "FAIL"
            self.results.append(("Conflict Quarantine", status, f"Slot {i}"))

        # Test 4: Anti-Score Regression (Scoring Trap)
        print("🔍 Testing Anti-Score Regression (Scoring Trap)...")
        trap_slot = "trap.slot.score"
        old_id = self.quiet_put("Trái đất hình vuông (Dữ liệu cũ, phổ biến).", subject=trap_slot, metadata={"usage_count": 1000})
        self.app.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_id,))
        new_id = self.quiet_put("Trái đất hình cầu (Sự thật mới).", subject=trap_slot, metadata={"is_winner": True, "usage_count": 1})
        
        payload = self.app.search_payload("Trái đất hình gì vuông hay tròn", scope_id="default", scope_type="agent", retrieval_mode="explain")
        winner_id = payload[0]["memory"]["id"] if payload else None
        status = "PASS" if winner_id == new_id else "FAIL"
        self.results.append(("Anti-Score Regression", status, "Earth shape trap"))

    def phase4_failure_analyzer(self):
        print("\n--- Tầng 4 & 5: Oracle & Failure Analyzer ---")
        print("="*60)
        print(f"{'TEST CATEGORY':<25} | {'STATUS':<10} | {'REMARK'}")
        print("-"*60)
        
        passes = 0
        for cat, stat, rem in self.results:
            icon = "✅" if stat == "PASS" else "❌"
            print(f"{cat:<25} | {icon} {stat:<6} | {rem}")
            if stat == "PASS": passes += 1
            
        print("="*60)
        hit_rate = (passes / len(self.results)) * 100 if self.results else 0
        print(f"TOTAL PASS RATE: {hit_rate:.2f}%")
        print(f"Total memories put: {self.stats['total_put']}")
        print(f"Execution time: {time.time() - self.stats['start_time']:.2f}s")
        
        if hit_rate > 90:
            print("\n🏆 KẾT LUẬN: Aegis V10 là Truth & Policy Engine thực thụ (MAX SCALE)!")
        else:
            print("\n⚠️ KẾT LUẬN: Aegis V10 vẫn còn bị Score-centric, cần cải thiện Governance.")

if __name__ == "__main__":
    stress = SuperStressV10()
    stress.phase1_corpus_generator()
    stress.phase2_event_injector()
    stress.phase3_query_assault()
    stress.phase4_failure_analyzer()
