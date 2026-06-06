"""Tests สำหรับ extract.py — ใช้ข้อความตรงจากเอกสาร A files เป็น fixture."""

import pytest
from datetime import date

from app.extract import (
    DeliveryDate,
    extract_delivery_dates,
    extract_has_hourly_penalty,
    extract_payment_percentages,
    extract_penalty_rate,
    extract_project_period,
)

# ---------------------------------------------------------------------------
# PENALTY-1 fixtures — จากเอกสารจริง
# ---------------------------------------------------------------------------

# จาก 02A section 11: มีวงเล็บอ่านออกเสียงกำกับ
_TEXT_02A_PENALTY = """
11. อัตราค่าปรับ
กรณีผู้รับจ้างไม่สามารถส่งมอบงานได้ตามกำหนดเวลา ผู้รับจ้างจะต้องชำระค่าปรับเป็น
รายวัน ในอัตราร้อยละ 0.10 (ศูนย์จุดหนึ่งศูนย์) ของราคาค่าจ้างนั้น แต่ต้องไม่ต่ำกว่าวันละ 100.00 บาท
"""

# จาก 03A: รูปสั้น ไม่มีวงเล็บ ใช้ "วงเงินสัญญา"
_TEXT_03A_PENALTY = """
อัตราค่าปรับ ร้อยละ 0.10 ของวงเงินสัญญา
"""

# มีงวดเงิน ร้อยละ 25 ก่อน section ค่าปรับ — ต้องไม่หยิบค่าผิด
_TEXT_PAYMENT_BEFORE_PENALTY = """
งวดที่ 1 ชำระเงินร้อยละ 25 ของค่าจ้าง
งวดที่ 2 ชำระเงินร้อยละ 25 ของค่าจ้าง
งวดที่ 3 ชำระเงินร้อยละ 25 ของค่าจ้าง
งวดที่ 4 ชำระเงินร้อยละ 25 ของค่าจ้าง

อัตราค่าปรับ
ร้อยละ 0.10 ของราคาค่าจ้าง ต้องไม่ต่ำกว่า 100 บาทต่อวัน
"""

# ไม่มี section ค่าปรับเลย
_TEXT_NO_PENALTY_SECTION = "งวดที่ 1 ชำระร้อยละ 50 ของค่าจ้าง"


# ---------------------------------------------------------------------------
# PENALTY-1 tests
# ---------------------------------------------------------------------------

def test_penalty_rate_with_parenthetical():
    assert extract_penalty_rate(_TEXT_02A_PENALTY) == 0.10


def test_penalty_rate_short_form_วงเงินสัญญา():
    assert extract_penalty_rate(_TEXT_03A_PENALTY) == 0.10


def test_penalty_rate_not_confused_with_payment_percentage():
    # ต้องได้ 0.10 ไม่ใช่ 25
    assert extract_penalty_rate(_TEXT_PAYMENT_BEFORE_PENALTY) == 0.10


def test_penalty_rate_returns_none_when_section_absent():
    assert extract_penalty_rate(_TEXT_NO_PENALTY_SECTION) is None


# ---------------------------------------------------------------------------
# DATE-1 fixtures — จากเอกสารจริง
# ---------------------------------------------------------------------------

# จาก 04A: ถึงวันที่ style, ช่วงสั้น 15 วัน
_TEXT_04A_PERIOD = "ระยะเวลาดำเนินการ\nตั้งแต่วันที่ 6 มกราคม 2569 ถึงวันที่ 20 มกราคม 2569"

# จาก 01A: en-dash style, วันปลายไม่มี "วันที่" นำ
_TEXT_01A_PERIOD = "ระยะเวลาดำเนินการ\nตั้งแต่วันที่ 1 เมษายน 2569 – 31 มีนาคม 2570"

# จาก 02A: ถึงวันที่ แบบเต็ม
_TEXT_02A_PERIOD = (
    "3.1 ระยะเวลาบำรุงรักษาตั้งแต่วันที่ 1 มีนาคม 2569 ถึงวันที่ 28 กุมภาพันธ์ 2570"
)

# จาก 04A ฉบับผิด: งวดที่ 1 กำหนดส่งก่อนวันเริ่มโครงการ (DATE-1 violation)
_TEXT_04A_DELIVERY = """\
งวดที่ 1 ผู้จ้างต้องจัดส่งเอกสาร ให้แล้วเสร็จ ตามข้อกำหนดข้อที่ 2.6 ภายในวันที่ 12 ธันวาคม 2568
โดยจะจ่ายชำระค่าจ้างร้อยละ 30 ของราคาจ้าง
งวดที่ 2 ผู้จ้างต้องจัดส่งเอกสารการขอใช้รถตู้ ช่วงวันที่ 6 – 12 มกราคม 2569
ภายในวันที่ 13 มกราคม 2569 โดยจะจ่ายร้อยละ 30
งวดที่ 3 ช่วงวันที่ 13 – 20 มกราคม 2569 ภายในวันที่ 20 มกราคม 2569
โดยจะจ่ายร้อยละ 40\
"""

# จาก 01A: 4 งวด ชำระ 25% ต่องวด
_TEXT_01A_DELIVERY = """\
งวดที่ 1 ชำระเงินร้อยละ 25 ของค่าจ้าง เมื่อผู้รับจ้างได้ปฏิบัติงานบำรุงรักษา
ตั้งแต่วันที่ 1 เมษายน 2569 – 30 มิถุนายน 2569 และคณะกรรมการตรวจรับแล้ว
งวดที่ 2 ชำระเงินร้อยละ 25 ของค่าจ้าง ตั้งแต่วันที่ 1 กรกฎาคม 2569 –
30 กันยายน 2569 และคณะกรรมการตรวจรับแล้ว
งวดที่ 3 ชำระเงินร้อยละ 25 ของค่าจ้าง ตั้งแต่วันที่ 1 ตุลาคม 2569 –
31 ธันวาคม 2569 และคณะกรรมการตรวจรับแล้ว
งวดที่ 4 (งวดสุดท้าย) ชำระเงินร้อยละ 25 ของค่าจ้าง ตั้งแต่วันที่ 1 มกราคม 2570 –
31 มีนาคม 2570 และคณะกรรมการตรวจรับแล้ว\
"""


# ---------------------------------------------------------------------------
# DATE-1 tests — project period
# ---------------------------------------------------------------------------

def test_project_period_ถึงวันที่_style():
    assert extract_project_period(_TEXT_04A_PERIOD) == (date(2026, 1, 6), date(2026, 1, 20))


def test_project_period_en_dash_style():
    # 2569 = 2026 CE, 2570 = 2027 CE
    assert extract_project_period(_TEXT_01A_PERIOD) == (date(2026, 4, 1), date(2027, 3, 31))


def test_project_period_without_section_header():
    # 02A ไม่มีหัวข้อ "ระยะเวลาดำเนินการ" ต้อง fallback หาทั้งเอกสาร
    assert extract_project_period(_TEXT_02A_PERIOD) == (date(2026, 3, 1), date(2027, 2, 28))


def test_project_period_returns_none_when_absent():
    assert extract_project_period("ไม่มีวันที่ใด ๆ เลย") is None


# ---------------------------------------------------------------------------
# DATE-1 tests — delivery dates
# ---------------------------------------------------------------------------

def test_delivery_dates_finds_all_three_installments():
    results = extract_delivery_dates(_TEXT_04A_DELIVERY)
    assert len(results) == 3


def test_delivery_date_labels_correct():
    results = extract_delivery_dates(_TEXT_04A_DELIVERY)
    assert [r.label for r in results] == ["งวดที่ 1", "งวดที่ 2", "งวดที่ 3"]


def test_delivery_date_installment1_is_before_project_start():
    # งวดที่ 1: 12 ธ.ค. 2568 (2025 CE) — ก่อนเริ่มโครงการ 6 ม.ค. 2569 (2026 CE)
    # นี่คือข้อผิดที่ DATE-1 ต้องตรวจจับ
    results = extract_delivery_dates(_TEXT_04A_DELIVERY)
    period = extract_project_period(_TEXT_04A_PERIOD)
    assert period is not None
    assert results[0].deadline < period[0]  # before start


def test_delivery_date_installments_2_3_within_period():
    results = extract_delivery_dates(_TEXT_04A_DELIVERY)
    period = extract_project_period(_TEXT_04A_PERIOD)
    assert period is not None
    start, end = period
    for r in results[1:]:
        assert start <= r.deadline <= end


def test_delivery_dates_returns_empty_when_no_installments():
    assert extract_delivery_dates("ไม่มีงวดใด ๆ") == []


def test_delivery_dates_01a_no_ภายินวันที่():
    # 01A ใช้ "ตั้งแต่...ถึง" ไม่ใช่ "ภายในวันที่" — งวดเหล่านี้จะไม่ถูก capture
    # (เป็น known limitation ที่ยอมรับได้ใน MVP)
    results = extract_delivery_dates(_TEXT_01A_DELIVERY)
    assert results == []


# "งวดที่ N" ปรากฏนอก payment section — ต้องไม่ถูกดึงมา
_TEXT_INSTALLMENT_OUTSIDE_PAYMENT = """\
3. คุณสมบัติ
ผู้เสนอราคาต้องมีประสบการณ์งวดที่ 1 และงวดที่ 2 ก่อนหน้า

4. ส่งมอบงานและการชำระเงิน
งวดที่ 1 ภายในวันที่ 20 มกราคม 2569 โดยจ่ายร้อยละ 100

5. อัตราค่าปรับ\
"""


def test_delivery_dates_scoped_to_payment_section():
    # "งวดที่ 1" และ "งวดที่ 2" ใน section คุณสมบัติต้องไม่ถูกนับ
    results = extract_delivery_dates(_TEXT_INSTALLMENT_OUTSIDE_PAYMENT)
    assert len(results) == 1
    assert results[0].label == "งวดที่ 1"
    assert results[0].deadline == date(2026, 1, 20)


# ---------------------------------------------------------------------------
# PENALTY-2 fixtures — จากเอกสารจริง
# ---------------------------------------------------------------------------

# จาก 02A section 11: มีทั้งค่าปรับรายวัน (ถูก) และรายชั่วโมง (ผิด)
_TEXT_02A_PENALTY_FULL = """\
11. อัตราค่าปรับ
11.1 กรณีผู้รับจ้างไม่สามารถส่งมอบงานได้ตามกำหนดเวลา ผู้รับจ้างจะต้องชำระค่าปรับเป็น
รายวัน ในอัตราร้อยละ 0.10 (ศูนย์จุดหนึ่งศูนย์) ของราคาค่าจ้างนั้น แต่ต้องไม่ต่ำกว่าวันละ 100.00 บาท
11.2 ค่าปรับตามเงื่อนไขข้อ 3.3 รายชั่วโมงที่มีระยะเวลาขัดข้องเกิน 7 ชั่วโมง
ผู้รับจ้างต้องชำระค่าปรับชั่วโมงส่วนที่เกินในอัตราชั่วโมงละ 1,000 บาท

12. การรักษาความลับ\
"""

# ค่าปรับที่ถูกต้อง — มีเฉพาะรายวัน ไม่มีชั่วโมง
_TEXT_CORRECT_PENALTY = """\
9. อัตราค่าปรับ
กรณีผู้รับจ้างไม่สามารถส่งมอบงานได้ตามกำหนด ผู้รับจ้างจะต้องชำระค่าปรับเป็นรายวัน
ในอัตราร้อยละ 0.10 ของราคาค่าจ้าง แต่ต้องไม่ต่ำกว่าวันละ 100 บาท

10. วงเงินงบประมาณ\
"""

# "ชั่วโมง" ปรากฎในขอบเขตงาน (uptime) แต่ไม่ใช่ในค่าปรับ
_TEXT_HOURLY_IN_SCOPE_NOT_PENALTY = """\
3. ขอบเขตการดำเนินงาน
3.3 ผู้รับจ้างต้องบำรุงรักษาให้ระบบทำงานได้ 24 ชั่วโมงต่อวัน
    เมื่อมีระยะเวลาขัดข้องเกิน 7 ชั่วโมง ถือว่าผิดสัญญา

9. อัตราค่าปรับ
ร้อยละ 0.10 ของราคาค่าจ้าง นับบัดจากวันที่ครบกำหนด

10. วงเงินงบประมาณ\
"""


# ---------------------------------------------------------------------------
# PENALTY-2 tests
# ---------------------------------------------------------------------------

def test_hourly_penalty_detected_02a():
    # 02A: "ชั่วโมงส่วนที่เกิน" และ "ชั่วโมงละ" ใน section อัตราค่าปรับ
    assert extract_has_hourly_penalty(_TEXT_02A_PENALTY_FULL) is True


def test_hourly_penalty_absent_correct_form():
    assert extract_has_hourly_penalty(_TEXT_CORRECT_PENALTY) is False


def test_hourly_penalty_not_triggered_by_scope_section():
    # "ชั่วโมง" ใน section ขอบเขตงานต้องไม่ถูกนับ
    assert extract_has_hourly_penalty(_TEXT_HOURLY_IN_SCOPE_NOT_PENALTY) is False


def test_hourly_penalty_absent_no_penalty_section():
    assert extract_has_hourly_penalty("ไม่มีหัวข้ออัตราค่าปรับเลย") is False


# ---------------------------------------------------------------------------
# PAY-1 fixtures — จากเอกสารจริง
# ---------------------------------------------------------------------------

# จาก 02A section 8: 4 งวด × 25%
_TEXT_02A_PAYMENT = """\
8. งวดงานและการจ่ายเงิน
จุหาลงกรณ์มหาวิทยาลัยจะแบ่งจ่ายให้แก่ผู้รับจ้างเป็น 4 งวด ดังนี้
งวดที่ 1 จ่ายเป็นจำนวนเงินร้อยละ 25 ของค่าจ้าง ตั้งแต่วันที่ 1 มีนาคม 2569 – 31 พฤษภาคม 2569
งวดที่ 2 จ่ายเป็นจำนวนเงินร้อยละ 25 ของค่าจ้าง ตั้งแต่วันที่ 1 มิถุนายน 2569 – 31 สิงหาคม 2569
งวดที่ 3 จ่ายเป็นจำนวนเงินร้อยละ 25 ของค่าจ้าง ตั้งแต่วันที่ 1 กันยายน 2569 – 30 พฤศจิกายน 2569
งวดที่ 4 จ่ายเป็นจำนวนเงินร้อยละ 25 ของค่าจ้าง ตั้งแต่วันที่ 1 ธันวาคม 2569 – 28 กุมภาพันธ์ 2570

9. หลักเกณฑ์ในการพิจารณาคัดเลือกข้อเสนอ\
"""

# จาก 04A: 30 + 30 + 40 = 100%
_TEXT_04A_PAYMENT = """\
4. ส่งมอบงานและการชำระเงิน
ทั้งนี้ให้แบ่งงวดการเบิกจ่ายค่าจ้างออกเป็น 3 งวด ดังนี้
งวดที่ 1 ผู้จ้างต้องจัดส่งเอกสาร ให้แล้วเสร็จ ภายในวันที่ 12 ธันวาคม 2568
โดยจะจ่ายชำระค่าจ้างร้อยละ 30 ของราคาจ้าง
งวดที่ 2 ผู้จ้างต้องจัดส่งเอกสาร ช่วงวันที่ 6 – 12 มกราคม 2569
ภายในวันที่ 13 มกราคม 2569 โดยจะจ่ายร้อยละ 30
งวดที่ 3 ช่วงวันที่ 13 – 20 มกราคม 2569 ภายในวันที่ 20 มกราคม 2569
โดยจะจ่ายร้อยละ 40

5. การปรับและการบอกเลิกสัญญา\
"""

# มี ร้อยละ ใน section คุณสมบัติก่อน section ชำระเงิน — ต้องไม่ถูกหยิบ
_TEXT_PAYMENT_SECTION_ISOLATED = """\
3. คุณสมบัติของผู้เสนอราคา
3.1 ต้องมีผลงานไม่น้อยกว่าร้อยละ 30 ของวงเงินสัญญา

8. งวดงานและการจ่ายเงิน
งวดที่ 1 ร้อยละ 25 ของค่าจ้าง
งวดที่ 2 ร้อยละ 25 ของค่าจ้าง
งวดที่ 3 ร้อยละ 25 ของค่าจ้าง
งวดที่ 4 ร้อยละ 25 ของค่าจ้าง

9. หลักเกณฑ์การพิจารณา\
"""

# งวดเงินรวมไม่ครบ 100% (PAY-1 violation)
_TEXT_PAYMENT_WRONG_SUM = """\
6. เงื่อนไขการชำระเงิน
งวดที่ 1 ร้อยละ 30 ของค่าจ้าง
งวดที่ 2 ร้อยละ 30 ของค่าจ้าง
งวดที่ 3 ร้อยละ 30 ของค่าจ้าง\
"""


# ---------------------------------------------------------------------------
# PAY-1 tests
# ---------------------------------------------------------------------------

def test_payment_percentages_4x25_from_02a():
    result = extract_payment_percentages(_TEXT_02A_PAYMENT)
    assert result == [25.0, 25.0, 25.0, 25.0]


def test_payment_percentages_30_30_40_from_04a():
    result = extract_payment_percentages(_TEXT_04A_PAYMENT)
    assert result == [30.0, 30.0, 40.0]


def test_payment_percentages_sum_100_passes():
    assert sum(extract_payment_percentages(_TEXT_02A_PAYMENT)) == 100.0
    assert sum(extract_payment_percentages(_TEXT_04A_PAYMENT)) == 100.0


def test_payment_percentages_section_isolated():
    # ร้อยละ 30 ใน section คุณสมบัติต้องไม่ถูก capture เข้ามา
    result = extract_payment_percentages(_TEXT_PAYMENT_SECTION_ISOLATED)
    assert result == [25.0, 25.0, 25.0, 25.0]
    assert 30.0 not in result


def test_payment_percentages_wrong_sum_detectable():
    result = extract_payment_percentages(_TEXT_PAYMENT_WRONG_SUM)
    assert sum(result) != 100.0
    assert sum(result) == pytest.approx(90.0)


def test_payment_percentages_returns_empty_when_no_section():
    assert extract_payment_percentages("ไม่มีหัวข้องวดงานเลย") == []
