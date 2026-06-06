"""สร้าง sample_tor.pdf — PDF ข้อความ (text-based) สำหรับเทสต์ flow อัปโหลด.

ใช้ฟอนต์ base-14 (Helvetica) เนื้อหาเป็น ASCII เพราะ mock mode ไม่สนเนื้อหา
(findings มาจาก _MOCK_FINDINGS) — แค่ต้องเป็น PDF ที่ pypdf ดึง text ได้ตรงๆ
ไม่ต้องตก OCR. รันใหม่ได้ด้วย:  python tests/fixtures/make_sample_pdf.py
"""

from pathlib import Path

LINES = [
    "Terms of Reference (TOR) - Sample Document",
    "Procurement: General Hiring (full form)",
    "",
    "1. Project scope and objectives",
    "2. Qualifications of bidders",
    "3. Submission requirements",
    "4. Evaluation criteria (price)",
    "5. Penalty rate: 1,000 baht per hour",
    "6. Payment milestones and schedule",
    "",
    "This is a placeholder TOR used to exercise the upload pipeline.",
]


def _content_stream() -> bytes:
    parts = ["BT", "/F1 14 Tf", "72 720 Td", "16 TL"]
    for line in LINES:
        safe = line.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        parts.append(f"({safe}) Tj")
        parts.append("T*")
    parts.append("ET")
    return ("\n".join(parts)).encode("latin-1")


def build_pdf() -> bytes:
    content = _content_stream()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content),
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += b"%d 0 obj\n%s\nendobj\n" % (i, body)

    xref_pos = len(pdf)
    n = len(objects) + 1
    pdf += b"xref\n0 %d\n" % n
    pdf += b"0000000000 65535 f \n"
    for off in offsets:
        pdf += b"%010d 00000 n \n" % off
    pdf += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (n, xref_pos)
    return bytes(pdf)


if __name__ == "__main__":
    out = Path(__file__).with_name("sample_tor.pdf")
    out.write_bytes(build_pdf())
    print(f"wrote {out} ({out.stat().st_size} bytes)")
