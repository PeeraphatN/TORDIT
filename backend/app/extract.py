"""Regex extractors — pre-processing ก่อนส่งให้ LLM.

ดึงค่าตัวเลขและวันที่ออกมาเป็น structured data เพื่อ inject เข้า prompt
ลดโอกาสที่โมเดลอ่านตัวเลขผิด (spec §5 ความเสี่ยงที่หนึ่ง)

แต่ละ extractor ค้นใน section ที่เกี่ยวข้องโดยอิงชื่อหัวข้อ ไม่ใช่เลขข้อ
เพราะเลขข้อสลับกันได้แต่ชื่อหัวข้อคงที่ (spec §4.2 R1)

กฎที่รองรับ:
  PENALTY-1  อัตราค่าปรับ (%) จาก section อัตราค่าปรับ
  PENALTY-2  ตรวจหาค่าปรับหน่วยชั่วโมง (ผิดรูปแบบ) ใน section อัตราค่าปรับ
  PAY-1      % งวดเงินแต่ละงวดจาก section งวดงาน/ชำระเงิน
  DATE-1     ระยะเวลาโครงการ + วันครบกำหนดแต่ละงวด
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

# ---------------------------------------------------------------------------
# Thai calendar helpers
# ---------------------------------------------------------------------------

_MONTH_MAP: dict[str, int] = {
    "มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3,
    "เมษายน": 4, "พฤษภาคม": 5, "มิถุนายน": 6,
    "กรกฎาคม": 7, "สิงหาคม": 8, "กันยายน": 9,
    "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12,
}

_MONTH_PAT = "|".join(_MONTH_MAP)
# group(n), group(n+1), group(n+2) → day, month_th, year_be
_D = rf"(\d{{1,2}})\s+({_MONTH_PAT})\s+(\d{{4}})"


def _to_date(day: str, month_th: str, year_be: str) -> date:
    """แปลง (วัน, เดือนไทย, ปี พ.ศ.) → datetime.date (ค.ศ.)"""
    return date(int(year_be) - 543, _MONTH_MAP[month_th], int(day))


# ---------------------------------------------------------------------------
# Section text extractor — shared helper
# ---------------------------------------------------------------------------

# หัวข้อระดับบน: ขึ้นต้นบรรทัดด้วยตัวเลข 1-2 หลัก ตามด้วยจุด (ไม่ใช่ตัวเลข) และ whitespace
# เช่น "8. งวดงาน" หรือ "11. อัตราค่าปรับ" แต่ไม่ใช่ "3.1 รายละเอียด"
_TOP_SECTION_BOUNDARY = re.compile(
    r"^\s*\d{1,2}\.(?!\d)\s+",
    re.UNICODE | re.MULTILINE,
)


def _section_text(text: str, keyword_re: re.Pattern) -> str | None:
    """ดึงข้อความจากต้นบรรทัดที่พบ keyword จนถึงต้น section ถัดไป.

    อิงชื่อหัวข้อแทนเลขข้อ เพราะเลขข้อสลับกันได้ (spec §4.2 R1)
    """
    m = keyword_re.search(text)
    if not m:
        return None
    line_start = text.rfind("\n", 0, m.start())
    start = (line_start + 1) if line_start >= 0 else 0
    boundary = _TOP_SECTION_BOUNDARY.search(text, m.end())
    end = boundary.start() if boundary else len(text)
    return text[start:end]


# ---------------------------------------------------------------------------
# PENALTY-1 — อัตราค่าปรับ
# ---------------------------------------------------------------------------

_PENALTY_SECTION_KW = re.compile(r"อัตราค่าปรับ", re.UNICODE)

# "ร้อยละ 0.10 (ศูนย์จุดหนึ่งศูนย์) ของราคาค่าจ้าง..."
# "ร้อยละ 0.10 ของวงเงินสัญญา"
_PENALTY_RATE_RE = re.compile(
    r"ร้อยละ\s*([\d.]+)\s*(?:\([^)]*\)\s*)?ของ(?:ราคาค่าจ้าง|(?:วงเงิน|มูลค่า)(?:สัญญา)?)",
    re.UNICODE,
)


def extract_penalty_rate(text: str) -> float | None:
    """อัตราค่าปรับหลัก (%) — None ถ้าไม่พบ section หรือไม่พบค่า."""
    section = _section_text(text, _PENALTY_SECTION_KW)
    if not section:
        return None
    m = _PENALTY_RATE_RE.search(section)
    return float(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# PENALTY-2 — ค่าปรับหน่วยรายชั่วโมง
# ---------------------------------------------------------------------------

# "ชั่วโมงละ 1,000 บาท" / "ชั่วโมงส่วนที่เกิน..."
_HOURLY_PENALTY_RE = re.compile(r"ชั่วโมง(?:ละ|ส่วนที่เกิน)", re.UNICODE)


def extract_has_hourly_penalty(text: str) -> bool:
    """True ถ้าพบค่าปรับรายชั่วโมงใน section อัตราค่าปรับ (PENALTY-2 violation).

    ค้นเฉพาะใน section อัตราค่าปรับ ไม่ใช่ทั้งเอกสาร
    เพราะ "ชั่วโมง" ปรากฏในขอบเขตงาน (เช่น uptime 24 ชั่วโมง) ได้โดยไม่ผิดระเบียบ
    """
    section = _section_text(text, _PENALTY_SECTION_KW)
    if not section:
        return False
    return bool(_HOURLY_PENALTY_RE.search(section))


# ---------------------------------------------------------------------------
# PAY-1 — งวดเงินรวม
# ---------------------------------------------------------------------------

# ครอบ: "งวดงานและการจ่ายเงิน" (02A), "เงื่อนไขการชำระเงิน" (01A/03A),
#        "ส่งมอบงานและการชำระเงิน" (04A)
_PAYMENT_SECTION_KW = re.compile(r"(?:งวดงาน|การ(?:ชำระ|จ่าย)เงิน)", re.UNICODE)

# ร้อยละ X ภายใน block งวด — เอาค่าแรกที่พบ
_PCT_IN_BLOCK_RE = re.compile(r"ร้อยละ\s*([\d.]+)", re.UNICODE)


def extract_payment_percentages(text: str) -> list[float]:
    """% งวดเงินแต่ละงวด (ลำดับตามเอกสาร) จาก section งวดงาน/ชำระเงิน.

    คืน list ว่างถ้าไม่พบ section หรือไม่พบ งวดที่ N ในนั้น
    """
    section = _section_text(text, _PAYMENT_SECTION_KW)
    if not section:
        return []
    results = []
    for block in _INSTALLMENT_RE.finditer(section):
        m = _PCT_IN_BLOCK_RE.search(block.group(2))
        if m:
            results.append(float(m.group(1)))
    return results


# ---------------------------------------------------------------------------
# DATE-1 — ระยะเวลาโครงการ + วันครบกำหนดงวด
# ---------------------------------------------------------------------------

# "ตั้งแต่วันที่ D M Y (–|-|ถึง[วันที่]) [วันที่] D M Y"
# รองรับทั้ง en-dash (U+2013) และ hyphen และ "ถึงวันที่"
_PROJECT_PERIOD_RE = re.compile(
    rf"ตั้งแต่วันที่\s+{_D}\s*(?:[–\-]|ถึง(?:วันที่)?)\s*(?:วันที่\s*)?{_D}",
    re.UNICODE,
)

# ค้น section ระยะเวลาดำเนินการก่อน เพื่อหลีกเลี่ยง period ที่อาจอยู่ใน scope งานหรืองวด
_DURATION_SECTION_RE = re.compile(r"ระยะเวลาดำเนินการ", re.UNICODE)

# แต่ละ "งวดที่ N" จนถึง "งวดที่ N+1" หรือจบข้อความ
# งวดท(?:ี่)? รองรับ OCR ที่ตกหล่น ี่ ออกไป
_INSTALLMENT_RE = re.compile(
    r"(งวดท(?:ี่)?\s*\d+)(.+?)(?=งวดท(?:ี่)?\s*\d+|\Z)",
    re.DOTALL | re.UNICODE,
)

# "ภายในวันที่ D M Y" หรือ "ถึงวันที่ D M Y" ในบริบทงวด
# (?:ี่)? รองรับ OCR ที่ตกหล่น ี่ ออกไป
_DEADLINE_RE = re.compile(
    rf"(?:ภายในวัน(?:ที่)?|ถึงวัน(?:ที่)?)\s+{_D}",
    re.UNICODE,
)

# fallback สำหรับ OCR ที่ตกหล่น "ตั้งแต่วันที่" — หา D M Y ... separator ... D M Y
# scoped ใน section ระยะเวลาดำเนินการเท่านั้นเพื่อหลีกเลี่ยง false positive
_PROJECT_PERIOD_FALLBACK_RE = re.compile(
    rf"(\d{{1,2}})\s+({_MONTH_PAT})\s+(\d{{4}})\s+(?:\S+\s+){{0,3}}(\d{{1,2}})\s+({_MONTH_PAT})\s+(\d{{4}})",
    re.UNICODE,
)


@dataclass
class DeliveryDate:
    label: str    # เช่น "งวดที่ 1"
    deadline: date


@dataclass
class CheckContext:
    raw_text: str
    procurement_type: str
    form: str
    penalty_rate: float | None
    has_hourly_penalty: bool
    payment_percentages: list[float]
    project_period: tuple[date, date] | None
    delivery_dates: list[DeliveryDate]


def extract_project_period(text: str) -> tuple[date, date] | None:
    """(start, end) ของระยะเวลาดำเนินการ — None ถ้าไม่พบ.

    ค้นใน section ระยะเวลาดำเนินการก่อน ถ้าไม่มี section นั้นจึง fallback ทั้งเอกสาร
    ถ้า OCR ตกหล่น "ตั้งแต่วันที่" ใช้ fallback regex หา D M Y separator D M Y
    """
    sec = _DURATION_SECTION_RE.search(text)
    m = _PROJECT_PERIOD_RE.search(text, sec.start() if sec else 0)
    if not m:
        m = _PROJECT_PERIOD_RE.search(text)
    if not m and sec:
        nxt = _TOP_SECTION_BOUNDARY.search(text, sec.end())
        sec_text = text[sec.start(): nxt.start() if nxt else len(text)]
        m = _PROJECT_PERIOD_FALLBACK_RE.search(sec_text)
    if not m:
        return None
    start = _to_date(m.group(1), m.group(2), m.group(3))
    end = _to_date(m.group(4), m.group(5), m.group(6))
    return start, end


def extract_delivery_dates(text: str) -> list[DeliveryDate]:
    """วันครบกำหนดของแต่ละงวด (ภายในวันที่ / ถึงวันที่ ที่อยู่ใน block งวด).

    ค้นเฉพาะใน payment section ก่อน เพื่อกันกรณีที่ "งวดที่ N" ปรากฏในส่วนอื่น
    เช่น ภาคผนวกหรือหน้าสรุป — fallback ทั้งเอกสารเมื่อไม่พบ section header
    """
    section = _section_text(text, _PAYMENT_SECTION_KW) or text
    results = []
    for block in _INSTALLMENT_RE.finditer(section):
        label = block.group(1).strip()
        m = _DEADLINE_RE.search(block.group(2))
        if m:
            results.append(DeliveryDate(
                label=label,
                deadline=_to_date(m.group(1), m.group(2), m.group(3)),
            ))
    return results


def build_context(text: str, procurement_type: str, form: str) -> CheckContext:
    """รวม raw text + structured fields ทั้งหมดเป็น CheckContext ก่อนส่ง LLM."""
    return CheckContext(
        raw_text=text,
        procurement_type=procurement_type,
        form=form,
        penalty_rate=extract_penalty_rate(text),
        has_hourly_penalty=extract_has_hourly_penalty(text),
        payment_percentages=extract_payment_percentages(text),
        project_period=extract_project_period(text),
        delivery_dates=extract_delivery_dates(text),
    )
