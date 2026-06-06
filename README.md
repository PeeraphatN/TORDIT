# TORDIT

ระบบตรวจสอบ TOR (ขอบเขตงาน) ของการจัดซื้อจัดจ้างภาครัฐไทยให้สอดคล้องกับกฎระเบียบ ว 159, ว 214 และระเบียบกระทรวงการคลัง พ.ศ. 2560

ผู้ใช้อัปโหลด TOR เป็น PDF เลือกประเภทการจัดซื้อจัดจ้างและรูปแบบ ระบบจะส่งคืนรายงานที่ระบุข้อความที่ไม่สอดคล้อง กฎข้อใดที่ละเมิด และคำแนะนำในการแก้ไข พร้อม rule ID และการอ้างอิงกฎหมายครบถ้วน

## Stack

| Layer    | Tech                                        |
| -------- | ------------------------------------------- |
| Backend  | Python 3.12 · FastAPI · Typhoon API (LLM)   |
| Frontend | Next.js 15 · TypeScript · Tailwind CSS      |
| Infra    | Docker Compose                              |

## Quick Start

```bash
# 1. Copy environment file
cp backend/.env.example backend/.env
# แก้ไข TYPHOON_API_KEY ใน backend/.env

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
pip install -e ".[dev]"
cp .env.example .env   # set TYPHOON_API_KEY

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

See `backend/.env.example` for the full list. Required:

| Variable          | Description                     |
| ----------------- | ------------------------------- |
| `TYPHOON_API_KEY` | API key for Typhoon (OCR + LLM) |

## Project Structure

```
backend/
  app/
    main.py       # FastAPI app, endpoints
    checker.py    # Orchestrates the full check pipeline
    extract.py    # Builds structured context from raw text
    rules.py      # Compliance rule definitions
    llm.py        # Typhoon API client
    pdf.py        # PDF → text extraction
    schemas.py    # Pydantic models
  tests/          # Unit + integration tests

frontend/
  src/
    app/          # Next.js pages (upload + result)
    components/   # FindingCard, FindingsPanel
    types/        # API response types

docker-compose.yml
```

## License

MIT
