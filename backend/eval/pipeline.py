"""Direct TOR check pipeline for eval — bypasses HTTP and JobStore."""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.extract import build_context
from app.llm import generate_findings
from app.pdf import extract_text
from app.rules import apply_references, filter_findings
from app.schemas import Finding


async def check_pdf(
    pdf_path: Path,
    procurement_type: str = "จ้างทั่วไป",
    form: str = "เต็ม",
) -> tuple[list[Finding], str]:
    """Run a PDF through the full check pipeline.

    Returns (findings, raw_tor_text). Requires LLM_MODE=live.
    """
    pdf_bytes = pdf_path.read_bytes()
    text = await asyncio.to_thread(extract_text, pdf_bytes)
    context = build_context(text, procurement_type, form)
    raw = await generate_findings(context)
    findings = filter_findings(raw)
    findings = apply_references(findings, context.raw_text)
    return findings, context.raw_text
