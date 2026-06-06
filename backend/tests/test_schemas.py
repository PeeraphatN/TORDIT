import pytest
from pydantic import ValidationError

from app.schemas import Finding, Severity, CheckResult, CheckStatus

# ตัวอย่าง finding ตาม Contract ใน team_brief.md §4
VALID = {
    "error_class": 2,
    "severity": "ผิดระเบียบ",
    "topic_location": "อัตราค่าปรับ",
    "description": "ตั้งค่าปรับรายชั่วโมง ขัดรูปแบบรายวันที่ระเบียบกำหนด",
    "rule_id": "PENALTY-2",
    "citation": "ว 159 ข้อ 9 / ระเบียบ 2560",
    "suggested_fix": "เปลี่ยนเป็นค่าปรับรายวัน 0.10% ของค่าจ้าง",
}


def test_finding_parses_valid_contract_example():
    f = Finding.model_validate(VALID)
    assert f.severity is Severity.VIOLATION
    assert f.error_class == 2
    assert f.rule_id == "PENALTY-2"


def test_error_class_out_of_range_rejected():
    with pytest.raises(ValidationError):
        Finding.model_validate({**VALID, "error_class": 5})
    with pytest.raises(ValidationError):
        Finding.model_validate({**VALID, "error_class": 0})


def test_unknown_severity_rejected():
    with pytest.raises(ValidationError):
        Finding.model_validate({**VALID, "severity": "ไม่ผิด"})


def test_check_result_defaults_to_empty_findings():
    r = CheckResult(check_id="chk_1", status="processing")
    assert r.status is CheckStatus.PROCESSING
    assert r.findings == []
