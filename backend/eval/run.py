"""TORDIT LLM-as-Judge eval CLI.

Usage (run from backend/):
    # evaluate a whole folder recursively
    python -m eval.run --data-dir "../DUMMY DATA/01"

    # evaluate specific PDFs
    python -m eval.run path/a.pdf path/b.pdf

    # override procurement type / form
    python -m eval.run --data-dir "../DUMMY DATA" --type จ้างทั่วไป --form เต็ม

    # write JSON report to file (prints summary to stdout either way)
    python -m eval.run --data-dir "../DUMMY DATA/02" --out results.json

    # override judge model
    JUDGE_MODEL=gemini-2.5-pro python -m eval.run --data-dir "../DUMMY DATA/01"

Requires:
    LLM_MODE=live  GOOGLE_API_KEY=<key>  (set in backend/.env or shell)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from eval.judge import FindingScore, judge_document
from eval.pipeline import check_pdf


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _aggregate_scores(scores: list[FindingScore]) -> dict:
    n = len(scores)
    if n == 0:
        return {}
    return {
        "mean":         round(sum(s.normalized for s in scores) / n, 3),
        "grounding":    round(sum(s.grounding for s in scores) / n, 3),        # 0–1
        "rule_accuracy": round(sum(s.rule_accuracy for s in scores) / (n * 2), 3),  # normalized
        "fix_quality":  round(sum(s.fix_quality for s in scores) / (n * 2), 3),
        "relevance":    round(sum(s.relevance for s in scores) / (n * 2), 3),
    }


# ---------------------------------------------------------------------------
# Per-file eval
# ---------------------------------------------------------------------------

async def eval_file(
    pdf_path: Path,
    procurement_type: str,
    form: str,
) -> dict:
    print(f"  {pdf_path.name}", end=" ... ", flush=True)
    try:
        findings, tor_text = await check_pdf(pdf_path, procurement_type, form)
        print(f"{len(findings)} findings", end=" → judging", flush=True)
        scores = await judge_document(findings, tor_text)
        print(" ✓")
    except Exception as exc:
        print(f" ERROR: {exc}")
        return {"file": pdf_path.name, "error": str(exc)}

    agg = _aggregate_scores(scores)
    return {
        "file": pdf_path.name,
        "finding_count": len(findings),
        "aggregate": agg,
        "findings": [
            {
                "rule_id": f.rule_id,
                "severity": f.severity.value,
                "description": f.description,
                "judge": {
                    "grounding":    sc.grounding,
                    "rule_accuracy": sc.rule_accuracy,
                    "fix_quality":  sc.fix_quality,
                    "relevance":    sc.relevance,
                    "normalized":   round(sc.normalized, 3),
                    "rationale":    sc.rationale,
                },
            }
            for f, sc in zip(findings, scores)
        ],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(args: argparse.Namespace) -> None:
    if os.getenv("LLM_MODE", "mock").lower() == "mock":
        print("WARNING: LLM_MODE is not 'live' — eval will score mock findings, not real ones.")
        print("         Set LLM_MODE=live in backend/.env or your shell.\n")

    pdfs: list[Path]
    if args.data_dir:
        pdfs = sorted(Path(args.data_dir).rglob("*.pdf"))
    else:
        pdfs = [Path(p) for p in args.pdfs]

    if not pdfs:
        print("No PDFs found.", file=sys.stderr)
        sys.exit(1)

    from eval.judge import JUDGE_MODEL
    print(f"Evaluating {len(pdfs)} PDF(s)")
    print(f"  type={args.type}  form={args.form}  judge={JUDGE_MODEL}\n")

    results = []
    for pdf in pdfs:
        result = await eval_file(pdf, args.type, args.form)
        results.append(result)

    # Overall summary across documents that have findings
    scored = [r for r in results if "aggregate" in r and r["aggregate"]]
    if scored:
        keys = ["mean", "grounding", "rule_accuracy", "fix_quality", "relevance"]
        overall = {
            k: round(sum(r["aggregate"][k] for r in scored) / len(scored), 3)
            for k in keys
        }
        summary = {
            "documents_total": len(results),
            "documents_with_findings": len(scored),
            "overall": overall,
        }
    else:
        summary = {
            "documents_total": len(results),
            "documents_with_findings": 0,
            "note": "No findings produced — check LLM_MODE=live and API keys.",
        }

    report = {"summary": summary, "documents": results}

    # Print summary table
    print("\n=== SUMMARY ===")
    print(f"Documents:       {summary['documents_total']}  ({summary.get('documents_with_findings', 0)} with findings)")
    if "overall" in summary:
        ov = summary["overall"]
        print(f"Overall score:   {ov['mean']:.3f}  (0–1)")
        print(f"  grounding:     {ov['grounding']:.3f}  (0–1)")
        print(f"  rule_accuracy: {ov['rule_accuracy']:.3f}  (0–1 normalized)")
        print(f"  fix_quality:   {ov['fix_quality']:.3f}  (0–1 normalized)")
        print(f"  relevance:     {ov['relevance']:.3f}  (0–1 normalized)")
    else:
        print(f"  {summary.get('note', '')}")

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"\nFull report → {out_path}")
    else:
        print("\n--- Full report (JSON) ---")
        print(json.dumps(report, ensure_ascii=False, indent=2))


def _parse() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="TORDIT LLM-as-Judge eval",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("pdfs", nargs="*", metavar="PDF", help="PDF file(s) to evaluate")
    p.add_argument("--data-dir", metavar="DIR", help="Scan directory recursively for PDFs")
    p.add_argument("--type", default="จ้างทั่วไป", metavar="TYPE", help="Procurement type (default: จ้างทั่วไป)")
    p.add_argument("--form", default="เต็ม", metavar="FORM", help="TOR form (default: เต็ม)")
    p.add_argument("--out", metavar="FILE", help="Write JSON report to this file")
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(main(_parse()))
