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
    import pytesseract
    from pdf2image import convert_from_bytes
    from PIL import ImageFilter

    images = convert_from_bytes(pdf_bytes, dpi=400)
    pages = []
    for img in images:
        img = img.convert("L").filter(ImageFilter.SHARPEN)
        pages.append(
            pytesseract.image_to_string(img, lang="tha+eng", config="--oem 1 --psm 3")
        )

    text = _normalize_thai("\n\n".join(pages).strip())
    if not text:
        raise ValueError("PDF contains no extractable text — may be a blank or corrupt document")
    return text
