"""Recall-based eval using labeled ground truth (no LLM judge required).

Metrics computed per document:
  grounding_rate  — fraction of findings whose evidence appears literally in TOR text
  recall          — fraction of expected rule IDs that appear in system findings
  precision       — fraction of system rule IDs that match expected (0.0 for clean docs)
  f1              — harmonic mean of recall and precision

For documents labeled as CLEAN (errors=[]), recall and precision are replaced with:
  clean_correct   — True if system produced 0 findings, False otherwise
  false_positive_count — number of spurious findings on a clean document

Usage (run from backend/):
    python -m eval.recall --data-dir "../DUMMY DATA" --out recall_results.json

    # single group
    python -m eval.recall --data-dir "../DUMMY DATA/01"

    # also include original (baseline) PDFs
    python -m eval.recall --data-dir "../DUMMY DATA" --include-originals
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from eval.pipeline import check_pdf

_GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"


# ---------------------------------------------------------------------------
# Ground truth helpers
# ---------------------------------------------------------------------------

def _load_ground_truth() -> dict:
    return json.loads(_GROUND_TRUTH_PATH.read_text(encoding="utf-8"))


def _lookup_entry(gt: dict, pdf_path: Path) -> dict | None:
    """Return the ground truth entry for a PDF, or None if not tracked."""
    # Try variants first (key = "01/01-1 TOR ..." style)
    for key, entry in gt["variants"].items():
        candidate = Path(key)
        if pdf_path.name == candidate.name and pdf_path.parent.name == candidate.parent.name:
            return entry
    # Try originals
    for key, entry in gt["originals"].items():
        if pdf_path.name == key:
            return entry
    return None


def _expected_rule_ids(entry: dict) -> set[str]:
    rules: set[str] = set()
    for err in entry.get("errors", []):
        rules.update(err.get("expected_rules", []))
    return rules


# ---------------------------------------------------------------------------
# Grounding check (free — no LLM)
# ---------------------------------------------------------------------------

def _grounding_rate(findings, tor_text: str) -> float:
    if not findings:
        return 1.0  # vacuously true
    hits = sum(
        1
        for f in findings
        if f.evidence and f.evidence.strip() and f.evidence.strip() in tor_text
    )
    return hits / len(findings)


# ---------------------------------------------------------------------------
# Per-file eval
# ---------------------------------------------------------------------------

async def eval_file(
    pdf_path: Path,
    entry: dict,
    procurement_type: str,
    form: str,
) -> dict:
    print(f"  {pdf_path.parent.name}/{pdf_path.name}", end=" ... ", flush=True)
    try:
        findings, tor_text = await check_pdf(pdf_path, procurement_type, form)
    except Exception as exc:
        print(f" ERROR: {exc}")
        return {"file": str(pdf_path), "error": str(exc)}

    grounding = _grounding_rate(findings, tor_text)
    expected = _expected_rule_ids(entry)
    found_rules = {f.rule_id for f in findings}
    is_clean = len(expected) == 0

    result: dict = {
        "file": f"{pdf_path.parent.name}/{pdf_path.name}",
        "group": entry.get("group", "?"),
        "finding_count": len(findings),
        "grounding_rate": round(grounding, 3),
        "expected_rules": sorted(expected),
        "found_rules": sorted(found_rules),
    }

    if is_clean:
        false_positives = len(findings)
        result["clean_correct"] = false_positives == 0
        result["false_positive_count"] = false_positives
        print(
            f" {len(findings)} findings | "
            f"clean={'✓' if false_positives == 0 else f'✗ ({false_positives} FP)'} | "
            f"ground={grounding:.2f}"
        )
    else:
        tp = expected & found_rules
        recall = len(tp) / len(expected) if expected else 0.0
        precision = len(tp) / len(found_rules) if found_rules else 0.0
        f1 = (2 * recall * precision / (recall + precision)) if (recall + precision) > 0 else 0.0
        result["recall"] = round(recall, 3)
        result["precision"] = round(precision, 3)
        result["f1"] = round(f1, 3)
        result["true_positives"] = sorted(tp)
        result["missed_rules"] = sorted(expected - found_rules)
        print(
            f" {len(findings)} findings | "
            f"recall={recall:.2f} P={precision:.2f} F1={f1:.2f} | "
            f"ground={grounding:.2f}"
        )

    return result


# ---------------------------------------------------------------------------
# Aggregate helpers
# ---------------------------------------------------------------------------

def _aggregate(results: list[dict]) -> dict:
    error_docs = [r for r in results if "recall" in r]
    clean_docs = [r for r in results if "clean_correct" in r]
    all_valid = [r for r in results if "error" not in r]

    agg: dict = {
        "total_documents": len(results),
        "error_documents": len(error_docs),
        "clean_documents": len(clean_docs),
        "mean_grounding_rate": (
            round(sum(r["grounding_rate"] for r in all_valid) / len(all_valid), 3)
            if all_valid else None
        ),
    }

    if error_docs:
        agg["mean_recall"] = round(sum(r["recall"] for r in error_docs) / len(error_docs), 3)
        agg["mean_precision"] = round(sum(r["precision"] for r in error_docs) / len(error_docs), 3)
        agg["mean_f1"] = round(sum(r["f1"] for r in error_docs) / len(error_docs), 3)

    if clean_docs:
        correct = sum(1 for r in clean_docs if r["clean_correct"])
        agg["clean_accuracy"] = round(correct / len(clean_docs), 3)
        agg["total_false_positives"] = sum(r["false_positive_count"] for r in clean_docs)

    return agg


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(args: argparse.Namespace) -> None:
    if os.getenv("LLM_MODE", "mock").lower() == "mock":
        print("WARNING: LLM_MODE is not 'live' — recall will be measured on mock findings.")
        print("         Set LLM_MODE=live in backend/.env or your shell.\n")

    gt = _load_ground_truth()

    # Collect PDFs
    if args.data_dir:
        pdfs = sorted(Path(args.data_dir).rglob("*.pdf"))
    else:
        pdfs = [Path(p) for p in args.pdfs]

    if not pdfs:
        print("No PDFs found.", file=sys.stderr)
        sys.exit(1)

    print(f"Evaluating {len(pdfs)} PDF(s) against ground truth\n")

    results = []
    skipped = []
    for pdf in pdfs:
        entry = _lookup_entry(gt, pdf)
        if entry is None:
            skipped.append(pdf.name)
            continue

        # originals are baselines — only include if --include-originals
        if entry.get("label") == "baseline" and not args.include_originals:
            continue

        grp = entry.get("group", "?")
        grp_cfg = gt["groups"].get(grp, {})
        procurement_type = grp_cfg.get("procurement_type", "จ้างทั่วไป")
        form = grp_cfg.get("form", "เต็ม")

        result = await eval_file(pdf, entry, procurement_type, form)
        results.append(result)

    if skipped:
        print(f"\nSkipped (not in ground truth): {', '.join(skipped)}")

    agg = _aggregate(results)

    print("\n=== RECALL SUMMARY ===")
    print(f"Documents:        {agg['total_documents']}  "
          f"({agg['error_documents']} with errors, {agg['clean_documents']} clean)")
    if "mean_grounding_rate" in agg and agg["mean_grounding_rate"] is not None:
        print(f"Grounding rate:   {agg['mean_grounding_rate']:.3f}  (evidence found in TOR)")
    if "mean_recall" in agg:
        print(f"Recall:           {agg['mean_recall']:.3f}  (expected rules caught / total expected)")
        print(f"Precision:        {agg['mean_precision']:.3f}  (caught rules that were expected)")
        print(f"F1:               {agg['mean_f1']:.3f}")
    if "clean_accuracy" in agg:
        print(f"Clean accuracy:   {agg['clean_accuracy']:.3f}  (clean docs with 0 findings)")
        print(f"Total FP on clean:{agg['total_false_positives']}")

    report = {"summary": agg, "documents": results}

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"\nFull report → {out_path}")
    else:
        print("\n--- Full report (JSON) ---")
        print(json.dumps(report, ensure_ascii=False, indent=2))


def _parse() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="TORDIT recall-based eval (no LLM judge required)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("pdfs", nargs="*", metavar="PDF", help="PDF file(s) to evaluate")
    p.add_argument("--data-dir", metavar="DIR", help="Scan directory recursively for PDFs")
    p.add_argument("--include-originals", action="store_true",
                   help="Also evaluate baseline/original PDFs (clean docs)")
    p.add_argument("--out", metavar="FILE", help="Write JSON report to this file")
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(main(_parse()))
