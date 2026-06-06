"""Pydantic schemas — Contract ระหว่าง backend / frontend / สถิติ (team_brief.md §4).

Finding คือรูปแบบผลลัพธ์ต่อ 1 ข้อค้นพบ (spec.md §8). โมเดลคืน list[Finding] ออกมาตรงๆ
ผ่าน structured output แล้ว backend คัดกรองด้วย filter_findings (rules.py) ก่อนส่งต่อ.
"""

from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    VIOLATION = "ผิดระเบียบ"      # ต้องแก้
    IMPROVEMENT = "ควรปรับปรุง"   # คำแนะนำ


class Finding(BaseModel):
    error_class: int = Field(ge=1, le=4)  # ประเภทข้อผิด 1-4 (spec §3)
    severity: Severity
    topic_location: str
    description: str
    rule_id: str
    citation: str
    suggested_fix: str
    # เพิ่มเพื่อความน่าเชื่อถือ (เติมโดย apply_references ไม่ใช่โมเดล):
    evidence: str | None = None    # ข้อความตรงคำจาก TOR ที่เป็นหลักฐาน (verify แล้วว่ามีจริง)
    provision: str | None = None   # ตัวบทกฎหมายจริงของ rule_id ให้เจ้าหน้าที่กดดู


class CheckStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CheckResult(BaseModel):
    check_id: str
    status: CheckStatus
    procurement_type: str | None = None
    form: str | None = None
    findings: list[Finding] = Field(default_factory=list)
    error: str | None = None
