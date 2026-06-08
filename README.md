# TORDIT

ระบบตรวจสอบ TOR (ขอบเขตงาน) ของการจัดซื้อจัดจ้างภาครัฐไทยให้สอดคล้องกับกฎระเบียบ ว 159, ว 214 และระเบียบกระทรวงการคลัง พ.ศ. 2560

ผู้ใช้อัปโหลด TOR เป็น PDF เลือกประเภทการจัดซื้อจัดจ้างและรูปแบบ ระบบจะส่งคืนรายงานที่ระบุข้อความที่ไม่สอดคล้อง กฎข้อใดที่ละเมิด และคำแนะนำในการแก้ไข พร้อม rule ID และการอ้างอิงกฎหมายครบถ้วน

## Stack

| Layer    | Tech                                                  |
| -------- | ----------------------------------------------------- |
| Backend  | Python 3.11+ · FastAPI · Gemini 3.5 Flash (LLM) · Typhoon OCR (image-PDF fallback) |
| Frontend | Next.js 15 · TypeScript · Tailwind CSS                |
| Infra    | Docker Compose · Nginx (reverse proxy)                |

LLM provider is swappable via env (default `google_genai`); the backend also ships an `anthropic` path.

## How It Works

```
PDF upload + ประเภท/แบบ
   → extract text (pypdf; Typhoon OCR fallback if the PDF has no embedded text)
   → build prompt (16-rule checklist + few-shot examples)
   → Gemini (single pass, structured output)
   → hard filter: drop findings whose rule_id isn't real
   → stamp official citation + verify evidence quote
   → report grouped by TOR section
```

The model returns findings via a lenient schema (`rule_id` constrained to a 16-value enum, all
fields defaulted) so partial output never crashes the parse; the hard filter is the final guard
against invented citations.

## Quick Start

```bash
# 1. Copy environment file
cp backend/.env.example backend/.env
# แก้ไข GOOGLE_API_KEY ใน backend/.env (จำเป็นเมื่อ LLM_MODE=live)

# 2. Start all services
docker compose up --build
```

The app is served by Nginx on **http://localhost** (port 80). The backend is **not** published to
the host — the browser reaches it through the frontend's Next.js rewrites (`BACKEND_URL=http://backend:8000`).
For direct API access during development, run the backend locally (see below).

## API

### Submit a check

```
POST /api/v1/check
Content-Type: multipart/form-data
```

| Field              | Type   | Values                                       |
| ------------------ | ------ | -------------------------------------------- |
| `file`             | file   | PDF ≤ 5 MB                                   |
| `procurement_type` | string | `จ้างทั่วไป` (MVP รองรับเฉพาะค่านี้)              |
| `form`             | string | `เต็ม` (MVP รองรับเฉพาะค่านี้; `ย่อ` วางไว้เฟสถัดไป) |

Returns `202` with `{ check_id, status: "processing", ... }`.

### Poll result

```
GET /api/v1/check/{check_id}
```

Returns `CheckResult`. The `status` field is one of `processing`, `completed`, or `failed`.
When `completed`, `findings` holds the list; when `failed`, `error` holds the reason.

## Local Development

### Backend

The repo uses [uv](https://docs.astral.sh/uv/) (see `uv.lock`).

```bash
cd backend
uv sync --extra api --extra llm --extra dev
cp .env.example .env   # set GOOGLE_API_KEY

uv run uvicorn app.main:app --reload   # http://localhost:8000/docs
```

<details>
<summary>Without uv (plain pip)</summary>

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[api,llm,dev]"
cp .env.example .env
uvicorn app.main:app --reload
```
</details>

Run tests:

```bash
uv run pytest
```

Enable debug endpoint (returns raw extracted text):

```bash
ENABLE_DEBUG_ENDPOINTS=1 uv run uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

## Environment Variables

See `backend/.env.example` for the full list. Key variables:

| Variable              | Default            | Description                                                  |
| --------------------- | ------------------ | ------------------------------------------------------------ |
| `LLM_MODE`            | `live`             | `mock` คืน findings ตัวอย่าง (ไม่ต้องมี key) / `live` ยิงโมเดลจริง |
| `LLM_PROVIDER`        | `google_genai`     | provider ของ LLM (สลับเป็น `anthropic` ได้)                    |
| `LLM_MODEL`           | `gemini-3.5-flash` | model id ของ provider นั้น                                      |
| `GOOGLE_API_KEY`      | —                  | จำเป็นเมื่อ `LLM_MODE=live` + provider `google_genai`            |
| `TYPHOON_OCR_API_KEY` | —                  | จำเป็นเฉพาะเมื่อต้องตรวจ PDF ที่เป็นรูป (image-based) — ถ้าไม่ตั้งไว้ ระบบจะ error เมื่อเจอ PDF ที่ไม่มี text |

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
    llm.py        # LLM client (LangChain, provider-swappable) + lenient parse layer
    schemas.py    # Pydantic models (public Finding contract)
    jobs.py       # In-memory job/result store
  eval/           # Recall-based eval pipeline (LLM-as-judge)
  tests/          # Unit + integration tests

frontend/
  src/
    app/          # Next.js pages (upload + result/[id])
    components/   # FindingCard, FindingsPanel
    lib/          # Shared utilities (mockCheck, utils)
    types/        # API response types

nginx/            # Reverse-proxy config (serves the app on :80)
docker-compose.yml
```

`rules.py` is the single source of truth for the 16 rule IDs — it feeds the prompt checklist,
the structured-output enum, and the hard filter, so the codes can't drift apart.

## License

MIT
