import os
import shutil
import unittest
from pathlib import Path
from aegis_py.facade import Aegis

class TestFacadeV10(unittest.TestCase):
    def setUp(self):
        # Create a clean temporary DB for each test
        self.db_path = "/tmp/test_aegis_facade_v10.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.aegis = Aegis.auto(self.db_path)

    def tearDown(self):
        # Cleanup
        if hasattr(self, 'aegis'):
            self.aegis._app.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_patch_c_wording_logic(self):
        """Verify Patch C: Wording changes for first-write vs correction."""
        # 1. First write
        id1 = self.aegis.remember("Màu yêu thích của sếp là màu xanh.", subject="user.favorite_color")
        results = self.aegis.recall("màu yêu thích")
        self.assertTrue(len(results) > 0)
        reason = results[0].get("human_reason", "")
        # First write should NOT say "bản sửa lỗi"
        # It can say 'được ghi nhận là sự thật mới' or 'được sếp xác nhận là sự thật hiện tại'
        is_first_write_wording = any(w in reason for w in ["được ghi nhận là sự thật mới", "được sếp xác nhận là sự thật hiện tại"])
        self.assertTrue(is_first_write_wording, f"Reason did not contain first-write wording: {reason}")
        self.assertNotIn("bản sửa lỗi mới nhất", reason)

        # 2. Correction
        self.aegis.correct("Thật ra sếp thích màu đỏ.", subject="user.favorite_color")
        results2 = self.aegis.recall("màu yêu thích")
        reason2 = results2[0].get("human_reason", "")
        # Correction SHOULD say "bản sửa lỗi" or 'đã được cập nhật và xác nhận là sự thật mới nhất'
        is_correction_wording = any(w in reason2 for w in ["là bản sửa lỗi mới nhất", "đã được cập nhật và xác nhận là sự thật mới nhất"])
        self.assertTrue(is_correction_wording, f"Reason did not contain correction wording: {reason2}")

    def test_patch_a_slot_collision(self):
        """Verify Patch A: Remember detects slot collision without explicit correction."""
        # 1. First write
        self.aegis.remember("Mã cửa là 1234", subject="door.code")
        
        # 2. Second write same subject, different content, NOT marked as correction
        # We use a new subject to be sure
        self.aegis.remember("Địa chỉ nhà là Quận 1", subject="user.address")
        id2 = self.aegis.remember("Địa chỉ nhà là Quận 7", subject="user.address")
        
        # Verify metadata has conflict markers
        mem = self.aegis._app.storage.get_memory(id2)
        meta = mem.metadata or {}
        self.assertTrue(meta.get("conflict_candidate"), f"Expected conflict_candidate=True, got {meta}")
        self.assertTrue(meta.get("requires_review"))

    def test_patch_b_recall_conflict_guard(self):
        """Verify Patch B: Recall flags conflicts if multiple truths exist for same subject."""
        # Force a conflict state by having two active memories for same subject
        # Note: Aegis.remember might prevent this if it sees a duplicate, 
        # but Patch A allows it as a 'conflict_candidate' (which is still 'active' status usually)
        
        self.aegis.remember("Sếp tên là Tùng", subject="user.name")
        # In v10, remember might not retire the old one automatically if not marked as correction
        self.aegis.remember("Sếp tên là Nam", subject="user.name")
        
        results = self.aegis.recall("Sếp tên là gì")
        
        # Check if guard triggered
        has_conflict = any(r.get("facade_conflict_detected") for r in results)
        if not has_conflict:
            print("\nDEBUG Patch B failure:")
            print(f"Result count: {len(results)}")
            for i, r in enumerate(results):
                content = r.get("content", "N/A")
                status = r.get("memory", {}).get("status", "N/A")
                gov = r.get("governance_status", "N/A")
                suppressed = r.get("suppressed_candidates", [])
                print(f"Result {i}: content='{content}', status='{status}', gov='{gov}', suppressed_count={len(suppressed)}")
                for s in suppressed:
                    print(f"  Suppressed: content='{s.get('content')}', reason='{s.get('reason')}'")
        
        self.assertTrue(has_conflict, "Recall should have detected and flagged the slot conflict")
        self.assertIn("Có xung đột", results[0].get("facade_conflict_message", ""))

if __name__ == "__main__":
    unittest.main()
