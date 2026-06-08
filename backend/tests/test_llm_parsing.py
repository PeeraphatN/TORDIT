"""Regression tests สำหรับการ parse LLM output แบบทนทาน (app.llm._LLMFinding).

ที่มา: live Gemini เคยคืน findings ที่บาง item ขาด rule_id/citation ทำให้ schema เดิม
(list[Finding] ตรงๆ) validation crash ทั้ง list — finding ที่ดีหายหมด (OUTPUT_PARSING_FAILURE).
ชุดทดสอบนี้ตรึง payload ที่เคยพังจริงไว้ ไม่ให้ regression กลับมา.
"""

from app.llm import _LLMFinding, _LLMFindingList
from app.rules import RULE_ID_VALUES, filter_findings
from app.schemas import Severity

# payload ที่สร้างปัญหาจริง (จาก traceback): findings[0] ครบ, findings[1] ขาด rule_id+citation
PARTIAL_COMPLETION = {
    "findings": [
        {
            "error_class": 1,
            "severity": "ผิดระเบียบ",
            "topic_location": "โครงสร้างหัวข้อ TOR",
            "description": "ขาดหัวข้อย่อยซึ่งเป็นสาระสำคัญ",
            "rule_id": "STRUCT-1",
            "citation": "หนังสือเวียน ว 159",
            "suggested_fix": "เพิ่มหัวข้อย่อย",
            "evidence": None,
        },
        {
            "error_class": 1,
            "severity": "ผิดระเบียบ",
            "topic_location": "ลำดับหัวข้อหลักและเลขข้อย่อยใน TOR",
            "description": "หัวข้อหลักข้ามเลขข้อ 2 จาก 1. ความเป็นมา",
            # rule_id, citation หายไป — ตัวจุดชนวน crash เดิม
        },
    ]
}


def test_partial_completion_does_not_crash():
    """ขาด rule_id/citation ต้อง parse ได้ ไม่ crash ทั้ง list (regression ของ OUTPUT_PARSING_FAILURE)."""
    parsed = _LLMFindingList.model_validate(PARTIAL_COMPLETION)
    findings = [f for lf in parsed.findings if (f := lf.to_finding()) is not None]
    assert len(findings) == 2
    assert findings[0].rule_id == "STRUCT-1"
    assert findings[1].rule_id == ""  # ขาดมา → default ว่าง


def test_ruleless_finding_dropped_by_filter():
    """finding ที่ขาด rule_id ต้องถูก hard filter ตัดทิ้ง (ยึดหลัก drop-rather-than-miscite)."""
    parsed = _LLMFindingList.model_validate(PARTIAL_COMPLETION)
    findings = [f for lf in parsed.findings if (f := lf.to_finding()) is not None]
    kept = filter_findings(findings)
    assert [f.rule_id for f in kept] == ["STRUCT-1"]


def test_error_class_out_of_range_clamped():
    """error_class นอกช่วง 1-4 ต้องถูก clamp ไม่ใช่ทำให้ Finding (ge/le) crash."""
    assert _LLMFinding.model_validate({"error_class": 9}).error_class == 4
    assert _LLMFinding.model_validate({"error_class": 0}).error_class == 1
    assert _LLMFinding.model_validate({"error_class": "2"}).error_class == 2


def test_unknown_severity_falls_back_to_improvement():
    """severity แปลก ๆ ต้อง fallback เป็น 'ควรปรับปรุง' ไม่ใช่ crash."""
    assert _LLMFinding.model_validate({"severity": "ไม่ผิด"}).severity is Severity.IMPROVEMENT
    assert _LLMFinding.model_validate({}).severity is Severity.IMPROVEMENT


def test_missing_core_fields_yields_none():
    """ขาด topic_location หรือ description → to_finding() คืน None (ไม่มีเนื้อหาให้รายงาน)."""
    assert _LLMFinding.model_validate({"topic_location": "x"}).to_finding() is None
    assert _LLMFinding.model_validate({"description": "x"}).to_finding() is None
    assert _LLMFinding.model_validate({}).to_finding() is None


def test_complete_finding_survives_intact():
    """item ที่ครบต้องผ่านครบทุก field ไม่ถูกแปลงผิด."""
    f = _LLMFinding.model_validate(PARTIAL_COMPLETION["findings"][0]).to_finding()
    assert f is not None
    assert f.error_class == 1
    assert f.severity is Severity.VIOLATION
    assert f.rule_id == "STRUCT-1"


def test_rule_id_enum_in_schema_but_optional():
    """schema ที่ส่งให้ Gemini ต้องมี enum rule_id ครบ 16 ตัว แต่ไม่ required (ปล่อยให้ omit ได้)."""
    schema = _LLMFinding.model_json_schema()
    assert schema["properties"]["rule_id"]["enum"] == list(RULE_ID_VALUES)
    assert "rule_id" not in schema.get("required", [])


def test_out_of_enum_rule_id_does_not_crash():
    """enum เป็นแค่ตัวชี้นำตอน generate — ถ้า Gemini หลุดกรอบ parse ต้องไม่ crash (type ยังเป็น str)."""
    f = _LLMFinding.model_validate(
        {"rule_id": "FAKE-99", "topic_location": "x", "description": "y"}
    ).to_finding()
    assert f is not None and f.rule_id == "FAKE-99"
    assert filter_findings([f]) == []  # ตาข่ายสุดท้ายตัดทิ้ง
