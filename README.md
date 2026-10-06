# Doctor Letter

Doctors sign in with a mobile number, edit letter templates in a self-hosted Quill editor, and save finalized PDFs to AWS S3. Profile, drafts, and history metadata are stored in Neon PostgreSQL.

## Repository layout

```
doctor_letter/
├── backend/
│   ├── app/                 FastAPI app, routes, services, letter_templates/
│   ├── tests/               API tests (keep for CI before deploy)
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/                Static HTML, CSS, JS, vendor/quill/
├── ops/health_ping.sh       Cron-friendly keep-alive for /api/health
├── render.yaml              Render blueprint (free tier + GitHub auto-deploy)
├── DEPLOY.md                Step-by-step: Render + Neon + keep-alive cron
├── .env.example
├── AGENTS.md
├── SECURITY.md
└── README.md
```

There is no separate `docs/` folder — operational notes live here and in `AGENTS.md`.

## Requirements

- Python 3.11+
- Neon PostgreSQL (`DATABASE_URL`; use **pooled** URL in production)
- AWS S3 bucket and IAM credentials (finalize/download)

## Local setup

1. Copy `.env.example` to `.env`. Set `DATABASE_URL`. Keep `OTP_ENABLED=false` for mobile-only sign-in.
2. Install and run:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\pip install -r requirements.txt
   .\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

3. Open http://127.0.0.1:8000

## Deploy (free tier + GitHub)

Push to **GitHub** → connect **[Render](https://render.com)** to the repo → each push redeploys automatically. Full steps: **[DEPLOY.md](DEPLOY.md)**.

Use `ENVIRONMENT=development` on Render until AWS credentials are set. Add a free [cron-job.org](https://cron-job.org) ping to `/api/health` every 12 minutes to reduce cold-start lag (free hosts still sleep sometimes).

API docs (development only): http://127.0.0.1:8000/docs

## Tests

Keep `backend/tests/` — run before every deploy.

```powershell
cd backend
.\.venv\Scripts\pip install -r requirements-dev.txt
.\.venv\Scripts\pytest -q
```

Tests force `OTP_ENABLED=false` in `conftest.py`. The S3 finalize test is skipped if `AWS_S3_BUCKET` is empty.

## Production checklist

Environment (`.env` or platform secrets):

| Variable | Notes |
|----------|--------|
| `ENVIRONMENT=production` | Disables `/docs`, enforces startup checks |
| `SECRET_KEY` | 32+ random characters |
| `OTP_ENABLED` | Leave `false` unless you enable optional SMS OTP |
| `DATABASE_URL` | Neon **pooler** connection string |
| `CORS_ORIGINS` | Your HTTPS origin only |
| AWS | Bucket + keys; bucket private |

Process model:

```bash
cd backend && gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
```

Tune `WEB_CONCURRENCY`, `DB_POOL_SIZE`, and `DB_MAX_OVERFLOW` so  
`workers × (DB_POOL_SIZE + DB_MAX_OVERFLOW)` stays **below** Neon’s connection limit.

### Keep-alive (free tier / cold start)

Schedule `ops/health_ping.sh` or a platform cron every **10–14 minutes** against `GET /api/health` (sets `HEALTHCHECK_URL` to your public base URL). This reduces Neon/compute sleep; confirm it complies with your host’s terms of service.

Example in `render.yaml`: cron every 12 minutes.

### Static assets

Quill is served from `frontend/vendor/quill/`. CSS, JS, and vendor files get long `Cache-Control` (`STATIC_CACHE_SECONDS`, default 7 days).

### Capacity (~4,000–5,000 concurrent users)

This stack can serve that load only with **horizontal scaling and paid tiers**, not a single free instance:

- Multiple gunicorn/uvicorn workers behind a load balancer (4–8+ workers per instance, several instances).
- Neon **scale** plan with pooler; monitor connection count and query latency.
- S3 and PDF generation are the other bottlenecks — preview/finalize are CPU-heavy; consider async PDF jobs if p95 latency grows.
- Session rate limits are **in-memory per process**; for many workers use a shared store (Redis) if abuse becomes an issue.

Plan load tests against your target region before go-live with real PHI.

## Data flow

| Step | Storage |
|------|---------|
| Sign in / profile | Neon |
| Draft autosave | Neon |
| Preview PDF | Memory only |
| Finalize letter | PDF to S3, metadata to Neon |
| Download | Presigned S3 URL |
| Delete letter | Remove Neon row and S3 object |

## GitHub

Do not push `.env`, `.venv`, or pytest cache. They are in `.gitignore`.
