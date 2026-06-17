"""Tests สำหรับ pdf.py — helper ที่ไม่ต้องเรียก API จริง.

ครอบ regression ของบั๊ก "scanned PDF ไม่ render":
  - Typhoon OCR คืน content เป็น {"natural_text": "..."} ต้องแกะก่อน
    ไม่งั้น \\n ถูก escape เป็นตัวอักษร ทำให้ regex extractor (MULTILINE ^) พัง
  - retry บน 429 ต้องเคารพ Retry-After และถอยแบบ exponential (กัน burst เกิน 2 RPS)
"""

import re

from app.pdf import _retry_delay, _unwrap_ocr_text


class _FakeResponse:
    """stub เลียนแบบ httpx.Response เฉพาะ .headers ที่ _retry_delay ใช้."""

    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


# ---------------------------------------------------------------------------
# _unwrap_ocr_text
# ---------------------------------------------------------------------------

def test_unwrap_natural_text_json():
    raw = '{"natural_text": "1. ความเป็นมา\\nบรรทัดสอง"}'
    assert _unwrap_ocr_text(raw) == "1. ความเป็นมา\nบรรทัดสอง"


def test_unwrap_plain_text_unchanged():
    assert _unwrap_ocr_text("1. ความเป็นมา\nบรรทัดสอง") == "1. ความเป็นมา\nบรรทัดสอง"


def test_unwrap_malformed_json_unchanged():
    # ขึ้นต้นด้วย { แต่ parse ไม่ได้ -> คืนค่าเดิม ไม่ throw
    assert _unwrap_ocr_text("{ไม่ใช่ json}") == "{ไม่ใช่ json}"


def test_unwrap_json_without_known_key_unchanged():
    raw = '{"foo": "bar"}'
    assert _unwrap_ocr_text(raw) == raw


def test_unwrap_restores_newlines_so_section_regex_works():
    # ผลกระทบปลายทาง: หลังแกะแล้วต้องมีขึ้นบรรทัดจริงให้ ^ (MULTILINE) จับหัวข้อได้
    text = _unwrap_ocr_text('{"natural_text": "8. งวดงาน\\n11. อัตราค่าปรับ"}')
    assert text.count("\n") == 1
    assert len(re.findall(r"^\s*\d{1,2}\.", text, re.MULTILINE)) == 2


# ---------------------------------------------------------------------------
# _retry_delay
# ---------------------------------------------------------------------------

def test_retry_delay_honors_retry_after():
    assert _retry_delay(_FakeResponse({"retry-after": "7"}), attempt=0) == 7.0


def test_retry_delay_caps_retry_after_at_60s():
    assert _retry_delay(_FakeResponse({"retry-after": "9999"}), attempt=0) == 60.0


def test_retry_delay_invalid_retry_after_falls_back_to_backoff():
    d = _retry_delay(_FakeResponse({"retry-after": "soon"}), attempt=0)
    assert 1.0 <= d < 2.0  # 2**0 + jitter[0,1)


def test_retry_delay_exponential_backoff_when_no_header():
    for attempt, base in [(0, 1), (1, 2), (2, 4), (3, 8)]:
        d = _retry_delay(None, attempt)
        assert base <= d < base + 1


def test_retry_delay_backoff_capped_at_30s():
    assert 30.0 <= _retry_delay(None, attempt=20) < 31.0
