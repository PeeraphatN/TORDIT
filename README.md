# TORDIT

ระบบตรวจสอบ TOR (ขอบเขตงาน) ของการจัดซื้อจัดจ้างภาครัฐไทยให้สอดคล้องกับกฎระเบียบ ว 159, ว 214 และระเบียบกระทรวงการคลัง พ.ศ. 2560

ผู้ใช้อัปโหลด TOR เป็น PDF เลือกประเภทการจัดซื้อจัดจ้างและรูปแบบ ระบบจะส่งคืนรายงานที่ระบุข้อความที่ไม่สอดคล้อง กฎข้อใดที่ละเมิด และคำแนะนำในการแก้ไข พร้อม rule ID และการอ้างอิงกฎหมายครบถ้วน

## Stack

| Layer    | Tech                                        |
| -------- | ------------------------------------------- |
| Backend  | Python 3.12 · FastAPI · Gemini (LLM) · Typhoon OCR |
| Frontend | Next.js 15 · TypeScript · Tailwind CSS      |
| Infra    | Docker Compose                              |

## Quick Start

```bash
# 1. Copy environment file
cp backend/.env.example backend/.env
# แก้ไข GOOGLE_API_KEY ใน backend/.env (จำเป็นเมื่อ LLM_MODE=live)

# 2. Start all services
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

## API

### Submit a check

```
POST /api/v1/check
Content-Type: multipart/form-data
```

| Field              | Type   | Values                      |
| ------------------ | ------ | --------------------------- |
| `file`             | file   | PDF ≤ 5 MB                  |
| `procurement_type` | string | `จ้างทั่วไป` / `ซื้อทั่วไป` / ... |
| `form`             | string | `เต็ม` / `ย่อ`               |

Returns `202` with `{ check_id, status: "processing" }`.

### Poll result

```
GET /api/v1/check/{check_id}
```

Returns `CheckResult` with `status: "done"` or `"error"` and a list of findings.

## Local Development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[api,llm,dev]"
cp .env.example .env   # set GOOGLE_API_KEY

uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

Enable debug endpoint (returns raw extracted text):

```bash
ENABLE_DEBUG_ENDPOINTS=1 uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

See `backend/.env.example` for the full list. Key variables:

| Variable              | Default            | Description                                                  |
| --------------------- | ------------------ | ------------------------------------------------------------ |
| `LLM_MODE`            | `live`             | `mock` คืน findings ตัวอย่าง (ไม่ต้องมี key) / `live` ยิงโมเดลจริง |
| `LLM_PROVIDER`        | `google_genai`     | provider ของ LLM (สลับเป็น `anthropic` ได้)                    |
| `LLM_MODEL`           | `gemini-3.5-flash` | model id ของ provider นั้น                                      |
| `GOOGLE_API_KEY`      | —                  | จำเป็นเมื่อ `LLM_MODE=live` + provider `google_genai`            |
| `TYPHOON_OCR_API_KEY` | —                  | ไม่บังคับ — OCR สำหรับ PDF ที่เป็นรูป (image-based)              |

## Project Structure

```
backend/
  app/
    main.py       # FastAPI app, endpoints
    checker.py    # Orchestrates the full check pipeline
    pdf.py        # PDF → text extraction (+ Typhoon OCR fallback)
    extract.py    # Builds structured context from raw text
    rules.py      # Compliance rule definitions
    reference.py  # Official legal citations applied to findings
    fewshot.py    # Few-shot examples for the LLM prompt
    prompt.py     # System + user prompt builders
    llm.py        # LLM client (LangChain, provider-swappable)
    schemas.py    # Pydantic models
    jobs.py       # In-memory job/result store
  tests/          # Unit + integration tests

frontend/
  src/
    app/          # Next.js pages (upload + result)
    components/   # FindingCard, FindingsPanel
    lib/          # Shared utilities
    types/        # API response types

docker-compose.yml
```

## License

MIT
