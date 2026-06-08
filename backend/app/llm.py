"""LLM integration — ตรวจ TOR ด้วยโมเดลภาษารอบเดียว (spec §5).

provider/model สลับได้ด้วย env เปลี่ยนเองภายหลังได้ง่าย (ตามที่ทีมตกลง):

  LLM_MODE      mock | live   default = mock
                mock = คืน findings ตัวอย่างตาม Contract (ไม่ต้องมี API key)
                       ปลดล็อก frontend ให้ต่อ flow ได้ทันที (team_brief §3)
                live = ยิงโมเดลจริง
  LLM_PROVIDER  google_genai | anthropic | openai | ...   default = google_genai
  LLM_MODEL     model id      default = gemini-3.5-flash
  <PROVIDER>_API_KEY ตาม provider เช่น ANTHROPIC_API_KEY

สลับ provider = แก้ LLM_PROVIDER + LLM_MODEL + ตั้ง API key ของ provider นั้น
(provider อื่นนอกจาก anthropic ต้องลง integration package เพิ่ม เช่น langchain-openai)

โมเดลคืน list[Finding] ผ่าน structured output แล้ว checker เรียก filter_findings ต่อ
(hard filter rule_id ที่ไม่มีจริง + ตัดซ้ำ, spec §9).
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field, field_validator

from app.extract import CheckContext
from app.prompt import build_system_prompt, format_user_message
from app.rules import RULE_ID_VALUES
from app.schemas import Finding, Severity

DEFAULT_PROVIDER = "google_genai"
DEFAULT_MODEL = "gemini-3.5-flash"
_MAX_TOKENS = 8192


class _LLMFinding(BaseModel):
    """Lenient schema สำหรับ parse LLM output — ทุก field มี default เพื่อรับ partial output.

    LLM บางครั้งไม่ส่ง rule_id/citation มา หรือส่ง error_class/severity ผิดรูปแบบ
    schema นี้รับ partial output แล้ว to_finding() กรองออกเองแทนที่จะให้ Pydantic crash ทั้ง list.
    """

    error_class: int = 4
    severity: Severity = Severity.IMPROVEMENT
    topic_location: str = ""
    description: str = ""
    # enum ใน schema ชี้นำ Gemini ให้เลือก rule_id ที่มีจริง (ลด omission + hallucination ตั้งแต่
    # ตอน generate) แต่ type ยังเป็น str + optional → ถ้าหลุดกรอบ parse ไม่ crash, filter_findings
    # เป็นตาข่ายสุดท้าย (defense-in-depth)
    rule_id: str = Field(default="", json_schema_extra={"enum": list(RULE_ID_VALUES)})
    citation: str = ""
    suggested_fix: str = ""
    evidence: str | None = None

    @field_validator("error_class", mode="before")
    @classmethod
    def clamp_error_class(cls, v: object) -> int:
        try:
            return max(1, min(4, int(v)))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 4

    @field_validator("severity", mode="before")
    @classmethod
    def coerce_severity(cls, v: object) -> Severity:
        try:
            return Severity(v)
        except (ValueError, TypeError):
            return Severity.IMPROVEMENT

    def to_finding(self) -> Finding | None:
        """แปลงเป็น Finding — คืน None ถ้า field สำคัญหายไป (จะถูกกรองออกก่อน filter_findings)."""
        if not self.topic_location or not self.description:
            return None
        return Finding(
            error_class=self.error_class,
            severity=self.severity,
            topic_location=self.topic_location,
            description=self.description,
            rule_id=self.rule_id,
            citation=self.citation,
            suggested_fix=self.suggested_fix,
            evidence=self.evidence,
        )


class _LLMFindingList(BaseModel):
    """container สำหรับ structured output (top-level array ไม่เหมาะเป็น tool schema)."""

    findings: list[_LLMFinding] = Field(default_factory=list)


# findings ตัวอย่างตาม Contract (team_brief §4) ครอบ error_class หลายแบบ + severity ทั้งสองค่า
# rule_id ทุกตัวมีจริงใน registry จึงผ่าน filter_findings — frontend เอาไปเรนเดอร์ได้เลย
_MOCK_FINDINGS: list[Finding] = [
    Finding(
        error_class=1,
        severity=Severity.VIOLATION,
        topic_location="คุณสมบัติของผู้ยื่นข้อเสนอ",
        description="ไม่พบหัวข้อคุณสมบัติผู้เสนอราคาตามชุดมาตรฐานที่ระเบียบกำหนด",
        rule_id="QUAL-1",
        citation="ว 159 ข้อ 3",
        suggested_fix="เพิ่มหัวข้อคุณสมบัติผู้ยื่นข้อเสนอให้ครบชุดมาตรฐาน",
    ),
    Finding(
        error_class=2,
        severity=Severity.VIOLATION,
        topic_location="อัตราค่าปรับ",
        description="ตั้งค่าปรับรายชั่วโมง 1,000 บาท ขัดรูปแบบรายวันที่ระเบียบกำหนด",
        rule_id="PENALTY-2",
        citation="ระเบียบ 2560 / ข้อ R2",  # mock — apply_references จะเขียนทับด้วย citation ทางการ
        suggested_fix="เปลี่ยนเป็นค่าปรับรายวัน ร้อยละ 0.10 ของราคาค่าจ้าง",
        evidence="Penalty rate: 1,000 baht per hour",  # ตรงกับ sample_tor.pdf (ground ผ่าน)
    ),
    Finding(
        error_class=4,
        severity=Severity.IMPROVEMENT,
        topic_location="หลักเกณฑ์ในการพิจารณาคัดเลือกข้อเสนอ",
        description="ใช้เกณฑ์ราคาอย่างเดียวกับงานที่ซับซ้อน ควรพิจารณาเกณฑ์ราคาประกอบเกณฑ์อื่น",
        rule_id="CRIT-2",
        citation="ข้อ R3 / มาตรา 65",  # mock — apply_references จะเขียนทับด้วย citation ทางการ
        suggested_fix="ปรับเป็นเกณฑ์ราคาประกอบคุณภาพให้เหมาะกับความซับซ้อนของงาน",
        evidence="Evaluation criteria (price)",  # ตรงกับ sample_tor.pdf (ground ผ่าน)
    ),
]


async def generate_findings(context: CheckContext) -> list[Finding]:
    """ตรวจ TOR แล้วคืนรายการข้อค้นพบ (ยังไม่ผ่าน filter_findings)."""
    if os.getenv("LLM_MODE", "mock").lower() == "mock":
        return [f.model_copy() for f in _MOCK_FINDINGS]

    model = _build_model().with_structured_output(_LLMFindingList)
    result: _LLMFindingList = await model.ainvoke(
        [
            ("system", build_system_prompt()),
            ("human", format_user_message(context)),
        ]
    )
    return [f for llm_f in result.findings if (f := llm_f.to_finding()) is not None]


def _build_model():
    """สร้าง chat model จาก env — import langchain แบบ lazy เพื่อให้ mock mode ไม่ต้องลง deps."""
    from langchain.chat_models import init_chat_model

    return init_chat_model(
        os.getenv("LLM_MODEL", DEFAULT_MODEL),
        model_provider=os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER),
        max_tokens=_MAX_TOKENS,
    )
