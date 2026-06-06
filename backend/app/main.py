import asyncio
import os
import uuid

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.checker import run_check
from app.extract import build_context
from app.jobs import JobStore
from app.pdf import extract_text
from app.schemas import CheckResult, CheckStatus

app = FastAPI(title="TORDIT API")

# DEMO: เปิดให้ใครก็เรียกได้ ยังไม่ทำ auth (origin ทั้งหมดผ่าน)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_jobs = JobStore()

_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


@app.post("/api/v1/check", status_code=202, response_model=CheckResult)
async def submit_check(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    procurement_type: str = Form(...),
    form: str = Form(...),
) -> CheckResult:
    content_type = file.content_type or ""
    filename = file.filename or ""
    if content_type != "application/pdf" and not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="file must be a PDF")

    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(status_code=422, detail="file too large (max 5 MB)")

    check_id = str(uuid.uuid4())
    job = CheckResult(
        check_id=check_id,
        status=CheckStatus.PROCESSING,
        procurement_type=procurement_type,
        form=form,
    )
    _jobs.put(job)
    background_tasks.add_task(run_check, check_id, content, procurement_type, form, _jobs)
    return job


@app.get("/api/v1/check/{check_id}", response_model=CheckResult)
async def get_check(check_id: str) -> CheckResult:
    job = _jobs.get(check_id)
    if job is None:
        raise HTTPException(status_code=404, detail="check not found")
    return job


# Debug endpoint คืน raw text ของเอกสาร — ปิดเป็น default เพื่อความปลอดภัย
# เปิดเฉพาะตอน dev ด้วย ENABLE_DEBUG_ENDPOINTS=1 (ดู .env.example)
if os.getenv("ENABLE_DEBUG_ENDPOINTS", "").lower() in {"1", "true", "yes"}:

    @app.post("/api/v1/debug/extract")
    async def debug_extract(
        file: UploadFile = File(...),
        procurement_type: str = Form(default="จ้างทั่วไป"),
        form: str = Form(default="เต็ม"),
    ) -> dict:
        content = await file.read()
        text = await asyncio.to_thread(extract_text, content)
        ctx = build_context(text, procurement_type, form)
        return {
            "char_count": len(text),
            "raw_text": text,
            "penalty_rate": ctx.penalty_rate,
            "has_hourly_penalty": ctx.has_hourly_penalty,
            "payment_percentages": ctx.payment_percentages,
            "project_period": ctx.project_period and [str(ctx.project_period[0]), str(ctx.project_period[1])],
            "delivery_dates": [{"label": d.label, "deadline": str(d.deadline)} for d in ctx.delivery_dates],
        }
