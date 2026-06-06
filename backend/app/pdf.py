import io

from pypdf import PdfReader

# OCR ผลิต ํา (MAITAIKHU U+0E4D + SARA A U+0E32) แทน ำ (SARA AM U+0E33)
# normalize ก่อนส่ง regex เพื่อให้ pattern ทำงานได้ถูกต้อง
_MAITAIKHU_SARA_A = "ํา"
_SARA_AM = "ำ"


def _normalize_thai(text: str) -> str:
    return text.replace(_MAITAIKHU_SARA_A, _SARA_AM)


def extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(pages).strip()
    if text:
        return text
    return _ocr_extract(pdf_bytes)


def _ocr_extract(pdf_bytes: bytes) -> str:
    import base64
    import io as _io
    import os
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor

    import httpx
    from pdf2image import convert_from_bytes

    api_key = os.environ.get("TYPHOON_OCR_API_KEY")
    if not api_key:
        raise ValueError("TYPHOON_OCR_API_KEY is not set — required for image-based PDF OCR")

    prompt = (
        "อ่านและถอดข้อความทั้งหมดในภาพให้ครบถ้วน "
        "รักษาการขึ้นบรรทัดใหม่และโครงสร้างข้อความ "
        "ตอบเฉพาะข้อความเท่านั้น ไม่ต้องอธิบายเพิ่มเติม"
    )

    images = convert_from_bytes(pdf_bytes, dpi=200)
    if not images:
        raise ValueError("PDF contains no extractable text — may be a blank or corrupt document")

    # Sliding-window rate limiter: 20 requests per 60 s
    _lock = threading.Lock()
    _sent_at: list[float] = []

    def _acquire() -> None:
        while True:
            with _lock:
                now = time.monotonic()
                _sent_at[:] = [t for t in _sent_at if now - t < 60.0]
                if len(_sent_at) < 20:
                    _sent_at.append(now)
                    return
                wait = 60.0 - (now - _sent_at[0])
            time.sleep(max(wait, 0.05))

    def _ocr_one(idx_img: tuple) -> str:
        idx, img = idx_img
        _acquire()
        buf = _io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()

        payload = {
            "model": "typhoon-ocr-preview",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ]}],
            "max_tokens": 8192,
        }

        for attempt in range(3):
            try:
                response = client.post(
                    "https://api.opentyphoon.ai/v1/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                break
            except httpx.TimeoutException:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise

        body = response.json()
        choices = body.get("choices") or []
        if not choices:
            raise ValueError(f"Typhoon API returned no choices on page {idx + 1}: {body}")
        choice = choices[0]
        content = (choice.get("message") or {}).get("content")
        if content is None:
            raise ValueError(f"Typhoon API returned no content on page {idx + 1}: {choice}")
        if choice.get("finish_reason") == "length":
            raise ValueError(f"OCR truncated on page {idx + 1} — content exceeds max_tokens")
        return content

    with httpx.Client(timeout=60.0) as client:
        with ThreadPoolExecutor(max_workers=min(len(images), 10)) as executor:
            pages = list(executor.map(_ocr_one, enumerate(images)))

    text = _normalize_thai("\n\n".join(pages).strip())
    if not text:
        raise ValueError("PDF contains no extractable text — may be a blank or corrupt document")
    return text
