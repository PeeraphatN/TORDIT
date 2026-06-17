# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

TORDIT checks Thai government procurement **TOR** (Terms of Reference) PDFs for compliance with
regulations (ว 159, ว 214, ระเบียบกระทรวงการคลัง พ.ศ. 2560). Upload a PDF → get findings
(violations / improvements) each with a rule ID, legal citation, and suggested fix. MVP scope is
deliberately locked to `procurement_type = จ้างทั่วไป` and `form = เต็ม`.

## Commands

Backend — run from `backend/`, uses [uv](https://docs.astral.sh/uv/):
```bash
uv sync --extra api --extra llm --extra dev    # install (extras: api=FastAPI/pdf, llm=langchain, dev=pytest)
cp .env.example .env                           # then set GOOGLE_API_KEY
uv run uvicorn app.main:app --reload           # http://localhost:8000/docs
uv run pytest                                  # all tests
uv run pytest tests/test_pdf.py -k unwrap      # single file / name pattern
ENABLE_DEBUG_ENDPOINTS=1 uv run uvicorn app.main:app --reload   # enables POST /api/v1/debug/extract (dumps raw extracted text)
```

Frontend — run from `frontend/`:
```bash
npm install
npm run dev      # http://localhost:3000
npm run build
npm run lint     # eslint
```

Full stack (nginx serves everything on port 80):
```bash
docker compose up --build    # http://localhost
```

Eval (LLM-as-judge) — run from `backend/`, requires `LLM_MODE=live` + `GOOGLE_API_KEY`:
```bash
python -m eval.run --data-dir "../DUMMY DATA/01"      # score a folder recursively
python -m eval.run path/to.pdf --out results.json     # specific file(s)
```

## Architecture

Async, polling-based — **there is no database**. The flow:

1. `POST /api/v1/check` (`app/main.py`) validates the PDF (≤ 5 MB), stores a `CheckResult` in the
   in-memory `JobStore` (`app/jobs.py`, TTL + capacity-bounded), schedules `run_check` as a FastAPI
   `BackgroundTask`, and returns `202` + `check_id` immediately.
2. `run_check` (`app/checker.py`) is the pipeline:
   `extract_text` (`pdf.py`) → `build_context` (`extract.py`) → `generate_findings` (`llm.py`) →
   `filter_findings` + `apply_references` (`rules.py`).
3. The frontend polls `GET /api/v1/check/{id}` every 2 s until `status` is `completed` or `failed`.

Key modules and the non-obvious decisions baked into them:

- **`pdf.py`** — tries `pypdf` text extraction first; if the PDF has no text layer (scanned/image),
  falls back to **Typhoon OCR** (`typhoon-ocr`, needs `TYPHOON_OCR_API_KEY`). Typhoon is rate-limited
  to **2 req/s, 20 req/min**; OCR concurrency is capped at 2 (env `TYPHOON_OCR_CONCURRENCY`) to stay
  under the RPS limit, and its response is a `{"natural_text": ...}` JSON wrapper that must be
  unwrapped before downstream regex (otherwise escaped `\n` breaks the section extractors).
- **`extract.py`** — regex pre-extractors pull numeric/date facts (penalty rate, payment %, project
  period, delivery dates) into a `CheckContext` that cross-checks the LLM. Sections are located by
  Thai **heading text, not by item numbers**, because TOR numbering is frequently wrong (that is one
  of the things being audited).
- **`llm.py`** — single-pass call via LangChain `init_chat_model` (provider-swappable; default
  `google_genai` / `gemini-3.5-flash`, `anthropic` path also shipped). Uses structured output with a
  **lenient schema** (every field defaulted) so partial model output never crashes the parse.
  `LLM_MODE=mock` returns canned findings with no API key — use it for frontend work. (Code default is
  `mock`; `.env.example` sets `live`.)
- **`rules.py`** — the rule registry is the **single source of truth** for rule IDs. The same set
  feeds (a) the prompt checklist, (b) the structured-output enum that constrains the model, and
  (c) the hard filter that drops findings citing non-existent rules. Add/modify rules here only.
- **`apply_references`** stamps the official legal citation per `rule_id` (the model is instructed
  *not* to write citations itself) and verifies each `evidence` quote actually appears in the TOR —
  dropping the quote if not, while keeping the finding.

Frontend (Next.js): the browser never calls the backend directly. `next.config.ts` rewrites
`/api/*` to `BACKEND_URL` (`http://backend:8000` in compose), so the backend port is not published
to the host. The uploaded PDF is stashed as a data URL in `sessionStorage` for the result page's
side-by-side preview.

## Gotchas

- **The frontend Next.js is a modified build** (`next@16.2.7`, React 19). Per `frontend/AGENTS.md`:
  its APIs/conventions may differ from training data — read `node_modules/next/dist/docs/` before
  writing frontend code.
- **MVP scope is gated in the UI**: only `จ้างทั่วไป` / `เต็ม` are selectable; the other options are
  roadmap placeholders. The prompt and rule set assume this scope.
- **Eval data hygiene**: few-shot examples (from `docs/03_...`) must never overlap with the held-out
  eval set, or scores are inflated (see `architecture.md`). `DUMMY DATA/` holds labeled eval PDFs and
  is gitignored.
- `docs/` folders are numbered by purpose: `01` reference regulations, `02` clean templates,
  `03` wrong/fixed pairs, `04`–`06` example TORs.
