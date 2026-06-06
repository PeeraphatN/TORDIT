"""OCR engine benchmark.

Usage:
    python tests/bench_ocr.py <pdf> [engine]
    engine: tesseract | easyocr | paddleocr  (default: all, but use one at a time to avoid OOM)
"""

import re
import sys
import time
from pathlib import Path

pdf_path = Path(sys.argv[1])
only = sys.argv[2] if len(sys.argv) > 2 else None
max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 0  # 0 = all pages
pdf_bytes = pdf_path.read_bytes()

from pdf2image import convert_from_bytes
from PIL import ImageFilter

dpi = 200 if only in ("easyocr", "paddleocr") else 300
images_raw = convert_from_bytes(pdf_bytes, dpi=dpi)
if max_pages:
    images_raw = images_raw[:max_pages]
images_gray = [img.convert("L").filter(ImageFilter.SHARPEN) for img in images_raw]

_MAITAIKHU_SARA_A = "ํา"
_SARA_AM = "ำ"

def normalize(text):
    return text.replace(_MAITAIKHU_SARA_A, _SARA_AM)

_PENALTY_RE = re.compile(r"ร้อยละ\s*([\d.]+)")
_INSTALLMENT_RE = re.compile(r"งวดท(?:ี่)?\s*\d+", re.UNICODE)
_DATE_RE = re.compile(
    r"\d{1,2}\s+(?:มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน"
    r"|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s+\d{4}",
    re.UNICODE,
)

def score(text):
    thai_chars = sum(1 for c in text if '฀' <= c <= '๿')
    return {
        "chars": len(text),
        "thai": thai_chars,
        "penalty_hits": len(_PENALTY_RE.findall(text)),
        "installments": len(_INSTALLMENT_RE.findall(text)),
        "dates": len(_DATE_RE.findall(text)),
    }


def run_tesseract():
    import pytesseract
    pages = [
        pytesseract.image_to_string(img, lang="tha+eng", config="--oem 1 --psm 3")
        for img in images_gray
    ]
    return normalize("\n\n".join(pages).strip())


def run_easyocr():
    import easyocr
    import numpy as np
    reader = easyocr.Reader(["th", "en"], gpu=False)
    pages = []
    for img in images_gray:
        detections = reader.readtext(np.array(img), detail=0, paragraph=True)
        pages.append("\n".join(detections))
    return normalize("\n\n".join(pages).strip())


def run_paddleocr():
    from paddleocr import PaddleOCR
    import numpy as np
    ocr = PaddleOCR(lang="th")
    pages = []
    for img in images_raw:
        res = ocr.ocr(np.array(img))
        if res and isinstance(res[0], dict):
            lines = [r.get("rec_text", "") for r in res]
        else:
            lines = [line[1][0] for block in (res or []) for line in (block or [])]
        pages.append("\n".join(lines))
    return normalize("\n\n".join(pages).strip())


ENGINES = {
    "tesseract": run_tesseract,
    "easyocr":   run_easyocr,
    "paddleocr": run_paddleocr,
}

engines_to_run = {only: ENGINES[only]} if only else ENGINES

results = {}
for name, fn in engines_to_run.items():
    try:
        t0 = time.time()
        text = fn()
        results[name] = {"time": time.time() - t0, **score(text)}
    except Exception as e:
        results[name] = {"error": str(e)[:120]}

print(f"\nPDF: {pdf_path.name}  ({len(images_raw)} pages)\n")
header = f"{'engine':<12} {'time(s)':>8} {'chars':>7} {'thai':>7} {'penalty':>8} {'งวด':>5} {'dates':>6}"
print(header)
print("-" * len(header))
for engine, r in results.items():
    if "error" in r:
        print(f"{engine:<12}  ERROR: {r['error']}")
    else:
        print(f"{engine:<12} {r['time']:>8.1f} {r['chars']:>7} {r['thai']:>7} {r['penalty_hits']:>8} {r['installments']:>5} {r['dates']:>6}")
