from aegis_py.memory.correction import CorrectionDetector


def test_correction_detector_matches_english_triggers():
    detector = CorrectionDetector()

    assert detector.is_correction("My phone number is no longer 123-456.") is True
    assert detector.is_correction("Actually, my office moved to Room 202.") is True
    assert detector.is_correction("Update: the deployment window changed to Friday.") is True


def test_correction_detector_matches_vietnamese_triggers():
    detector = CorrectionDetector()

    assert detector.is_correction("Địa chỉ nhà tôi đã chuyển sang 456 Nguyễn Huệ.") is True
    assert detector.is_correction("Cập nhật: tôi đã đổi thành dùng email mới.") is True
    assert detector.is_correction("Thực ra số điện thoại đúng là 0909.") is True


def test_correction_detector_ignores_plain_statements():
    detector = CorrectionDetector()

    assert detector.is_correction("My office is in Room 101.") is False
    assert detector.is_correction("Tôi thích câu trả lời ngắn gọn.") is False
    assert detector.is_correction("") is False
