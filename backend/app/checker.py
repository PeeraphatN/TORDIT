import asyncio

from app.extract import build_context
from app.jobs import JobStore
from app.llm import generate_findings
from app.pdf import extract_text
from app.rules import apply_references, filter_findings
from app.schemas import CheckStatus


async def run_check(
    check_id: str,
    pdf_bytes: bytes,
    procurement_type: str,
    form: str,
    jobs: JobStore,
) -> None:
    try:
        text = await asyncio.to_thread(extract_text, pdf_bytes)
        context = build_context(text, procurement_type, form)
        raw = await generate_findings(context)
        findings = filter_findings(raw)
        findings = apply_references(findings, context.raw_text)
        jobs.update(check_id, status=CheckStatus.COMPLETED, findings=findings)
    except Exception as exc:
        jobs.update(check_id, status=CheckStatus.FAILED, error=str(exc))
