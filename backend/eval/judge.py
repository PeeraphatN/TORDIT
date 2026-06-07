"""LLM-as-Judge: score each Finding across 4 dimensions using Gemini.

Dimensions (all normalized to 0–1 before averaging):
  grounding     0/1   — evidence text is present in the TOR
  rule_accuracy 0–2   — rule_id matches the described issue
  fix_quality   0–2   — suggested_fix is actionable and specific
  relevance     0–2   — finding is a real issue, not a false alarm

One Gemini call per document (all findings batched) to reduce latency and cost.
Override model via JUDGE_MODEL / JUDGE_PROVIDER env vars.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field

from app.schemas import Finding

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gemini-3.1-pro-preview")
JUDGE_PROVIDER = os.getenv("JUDGE_PROVIDER", "google_genai")
_MAX_TOR_CHARS = 6_000

_SYSTEM = """\
คุณเป็น expert ด้านการจัดซื้อจัดจ้างภาครัฐไทย (ว 159, ว 214, ระเบียบกระทรวงการคลัง 2560)
ทำหน้าที่ประเมินคุณภาพของผลการตรวจสอบ TOR ที่ระบบ AI ตรวจพบ

ให้คะแนนแต่ละ Finding 4 มิติ:

grounding (0–1)
  1 = ข้อความใน evidence มีอยู่จริงใน TOR (หรือ evidence เว้นว่างแต่ปัญหาอ่านชัดจากข้อความ TOR)
  0 = ไม่พบใน TOR เลย หรือ evidence คลาดเคลื่อนอย่างมีนัยสำคัญ

rule_accuracy (0–2)
  2 = rule_id ที่อ้างตรงกับปัญหาที่อธิบายอย่างสมบูรณ์
  1 = ถูกทิศทางแต่ไม่ใช่กฎที่เหมาะสมที่สุด
  0 = กฎผิด หรือไม่ตรงกันเลย

fix_quality (0–2)
  2 = แก้ไขได้จริง เฉพาะเจาะจง นำไปปฏิบัติได้ทันที
  1 = พอใช้ได้แต่ยังกำกวมหรือ generic เกินไป
  0 = ไม่เป็นประโยชน์ หรือไม่ตรงกับปัญหาที่ระบุ

relevance (0–2)
  2 = เป็นปัญหาจริงในบริบท TOR นี้ ควร flag
  1 = borderline — อาจเป็นปัญหาขึ้นกับบริบทเพิ่มเติม
  0 = false alarm — ไม่ใช่ปัญหา

ตอบเป็น JSON ตาม schema ที่กำหนด ส่ง scores ให้ครบทุกข้อตามลำดับ
เขียน rationale สั้นๆ 1 ประโยคภาษาไทย ต่อ Finding"""


class FindingScore(BaseModel):
    grounding: int = Field(ge=0, le=1)
    rule_accuracy: int = Field(ge=0, le=2)
    fix_quality: int = Field(ge=0, le=2)
    relevance: int = Field(ge=0, le=2)
    rationale: str

    @property
    def normalized(self) -> float:
        """Weighted average on 0–1 scale (max raw = 7)."""
        return (self.grounding + self.rule_accuracy + self.fix_quality + self.relevance) / 7.0


class _DocumentJudgment(BaseModel):
    scores: list[FindingScore]


def _build_judge():
    from langchain.chat_models import init_chat_model

    model = init_chat_model(
        JUDGE_MODEL,
        model_provider=JUDGE_PROVIDER,
        max_tokens=4096,
    )
    return model.with_structured_output(_DocumentJudgment)


def _format_findings(findings: list[Finding]) -> str:
    parts = []
    for i, f in enumerate(findings, 1):
        parts.append(
            f"[{i}] rule_id={f.rule_id}  severity={f.severity.value}\n"
            f"    description: {f.description}\n"
            f"    evidence:    {f.evidence or '(ไม่ระบุ)'}\n"
            f"    suggested_fix: {f.suggested_fix}"
        )
    return "\n\n".join(parts)


async def judge_document(
    findings: list[Finding],
    tor_text: str,
) -> list[FindingScore]:
    """Return one FindingScore per finding, same order as input.

    Returns empty list when findings is empty (no API call made).
    Pads with a zero score if the model returns fewer scores than findings.
    """
    if not findings:
        return []

    judge = _build_judge()

    tor_snippet = tor_text[:_MAX_TOR_CHARS]
    if len(tor_text) > _MAX_TOR_CHARS:
        tor_snippet += "\n... [ข้อความถูกตัดทิ้ง] ..."

    user_msg = (
        f"ข้อความ TOR:\n{tor_snippet}\n\n"
        f"ผลการตรวจสอบ ({len(findings)} ข้อ):\n{_format_findings(findings)}\n\n"
        f"ให้คะแนน {len(findings)} Findings ตามลำดับ"
    )

    result: _DocumentJudgment = await judge.ainvoke(
        [("system", _SYSTEM), ("human", user_msg)]
    )

    scores = result.scores
    # guard: pad if model returned fewer scores than findings
    while len(scores) < len(findings):
        scores.append(FindingScore(grounding=0, rule_accuracy=0, fix_quality=0, relevance=0, rationale="(ไม่ได้รับคะแนนจาก judge)"))

    return scores[: len(findings)]
