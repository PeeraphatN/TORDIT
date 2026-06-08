# TORDIT — Frontend

Next.js 15 (App Router, TypeScript, Tailwind) UI for the TORDIT TOR-compliance checker.
See the [root README](../README.md) for the full system overview.

## What it does

- **Upload page** (`src/app/page.tsx`) — drag-and-drop a TOR PDF, pick procurement type / form
  (MVP: `งานจ้างทั่วไป` / `แบบเต็ม`), and submit to `POST /api/v1/check`.
- **Result page** (`src/app/check/[id]/page.tsx`) — polls `GET /api/v1/check/{id}` until the status
  is `completed` or `failed`, then renders findings grouped by TOR section.
- **Components** — `FindingCard` (expandable, severity-coded, rule ID + citation) and `FindingsPanel`.

## Backend connection

The browser calls same-origin `/api/*`; Next.js rewrites those to the backend (`next.config.ts`):

```ts
source: "/api/:path*"  →  `${BACKEND_URL ?? "http://localhost:8000"}/api/:path*`
```

Set `BACKEND_URL` at build/run time (in Docker it's `http://backend:8000`). The backend is never
exposed to the browser directly.

## Develop

```bash
npm install
npm run dev      # http://localhost:3000  (expects the backend on :8000)
```

Other scripts: `npm run build` · `npm run start` · `npm run lint`.

**Demo mode:** opening `/check/<DEMO_ID>` loads fixture findings from `src/lib/mockCheck.ts` instead
of polling the backend — useful for UI work without a running API. The fixture is loaded on demand
and not bundled into the production build.

## Build notes

- `output: "standalone"` — produces a self-contained server bundle for the Docker image.
- Font: [Geist](https://vercel.com/font) via `next/font`.
