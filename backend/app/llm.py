"""LLM integration — ตรวจ TOR ด้วยโมเดลภาษารอบเดียว (spec §5).

provider/model สลับได้ด้วย env เปลี่ยนเองภายหลังได้ง่าย (ตามที่ทีมตกลง):

  LLM_MODE      mock | live   default = mock
                mock = คืน findings ตัวอย่างตาม Contract (ไม่ต้องมี API key)
                       ปลดล็อก frontend ให้ต่อ flow ได้ทันที (team_brief §3)
                live = ยิงโมเดลจริง
  LLM_PROVIDER  anthropic | openai | ...   default = anthropic
  LLM_MODEL     model id      default = claude-sonnet-4-6
  <PROVIDER>_API_KEY ตาม provider เช่น ANTHROPIC_API_KEY

สลับ provider = แก้ LLM_PROVIDER + LLM_MODEL + ตั้ง API key ของ provider นั้น
(provider อื่นนอกจาก anthropic ต้องลง integration package เพิ่ม เช่น langchain-openai)

โมเดลคืน list[Finding] ผ่าน structured output แล้ว checker เรียก filter_findings ต่อ
(hard filter rule_id ที่ไม่มีจริง + ตัดซ้ำ, spec §9).
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field

from app.extract import CheckContext
from app.prompt import build_system_prompt, format_user_message
from app.schemas import Finding, Severity

DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 8192


class _FindingList(BaseModel):
    """container สำหรับ structured output (top-level array ไม่เหมาะเป็น tool schema)."""

    findings: list[Finding] = Field(default_factory=list)


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

    model = _build_model().with_structured_output(_FindingList)
    result: _FindingList = await model.ainvoke(
        [
            ("system", build_system_prompt()),
            ("human", format_user_message(context)),
        ]
    )
    return list(result.findings)


def _build_model():
    """สร้าง chat model จาก env — import langchain แบบ lazy เพื่อให้ mock mode ไม่ต้องลง deps."""
    from langchain.chat_models import init_chat_model

    return init_chat_model(
        os.getenv("LLM_MODEL", DEFAULT_MODEL),
        model_provider=os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER),
        max_tokens=_MAX_TOKENS,
    )
