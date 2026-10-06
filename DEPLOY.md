# Deploy on Render (free tier) + GitHub auto-deploy

This app is a single Python service: FastAPI serves the API and the `frontend/` static files. Database is **Neon** (already in your `.env`). **AWS** can stay empty until you finalize PDFs to S3.

## What “lag free” means on free hosting

Render’s **free** web service **sleeps** after ~15 minutes without traffic. The first request after sleep can take **30–90 seconds** (wake app + Neon). There is no fully lag-free free tier.

To **reduce** lag:

1. Ping `GET /api/health` every **10–14 minutes** (see step 6).
2. Use **one** gunicorn worker on free RAM (`WEB_CONCURRENCY=1` in `render.yaml`).
3. Keep Neon in a **region close to you** (e.g. AWS Mumbai if users are in India).

For always-on performance you need a **paid** plan (Render Starter, etc.).

---

## Step 1 — Push code to GitHub

```powershell
cd e:\doctor_letter
git add .
git commit -m "Prepare Render deploy"
git push origin main
```

Never commit `.env`. Set secrets only in Render’s dashboard.

---

## Step 2 — Create a Render account

1. Go to [render.com](https://render.com) and sign up (GitHub login is easiest).
2. **New → Blueprint** (if you use `render.yaml`) **or** **New → Web Service** and connect repo `3sannn/doctor_letter` (your repo).

**Blueprint:** Render reads `render.yaml` at the repo root and creates the web service (and optional cron if your plan allows it).

**Manual web service:**

| Setting | Value |
|--------|--------|
| Root directory | *(leave empty — repo root)* |
| Runtime | Python 3 |
| Build command | `pip install -r backend/requirements.txt` |
| Start command | `cd backend && gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:$PORT` |
| Plan | **Free** |
| `PYTHON_VERSION` | **3.12.7** (required — do not use 3.14) |

---

## Step 3 — Environment variables (Render dashboard)

Copy values from your local `.env` (except do not paste AWS until ready).

| Key | Required now | Notes |
|-----|----------------|-------|
| `DATABASE_URL` | Yes | Neon connection string (use **pooled** URL for production traffic) |
| `SECRET_KEY` | Yes | 32+ random characters |
| `ENVIRONMENT` | Yes | Use `development` until AWS is set; then `production` |
| `OTP_ENABLED` | Yes | `false` (mobile sign-in only) |
| `CORS_ORIGINS` | Yes | `https://YOUR-SERVICE.onrender.com` (exact URL, no trailing slash) |
| `WEB_CONCURRENCY` | Yes | `1` on free plan |
| `PYTHON_VERSION` | Yes | `3.12.7` (if not using Blueprint / `runtime.txt`) |
| `AWS_*` | Later | Leave empty until S3 is configured; finalize will fail until then |

After the first deploy, copy your public URL (e.g. `https://doctor-letter-xxxx.onrender.com`) and set `CORS_ORIGINS` to that HTTPS origin, then **Manual Deploy → Clear build cache & deploy** if you change CORS.

---

## Step 4 — GitHub → auto deploy

1. In Render: **Service → Settings → Build & Deploy**.
2. **Auto-Deploy:** Yes, branch `main` (or your default branch).
3. Each `git push` to that branch triggers a new build and deploy (usually 2–5 minutes).

You do **not** need GitHub Actions for deploy if Render is connected to the repo.

Optional: `.github/workflows/ci.yml` runs tests on push (add `DATABASE_URL` as a GitHub **repository secret** if you want DB tests in CI).

---

## Step 5 — Smoke test

1. Open `https://YOUR-SERVICE.onrender.com`
2. Sign in with mobile → dashboard → templates → editor → **preview** PDF.
3. `https://YOUR-SERVICE.onrender.com/api/health` → `{"status":"ok","database":"connected"}`

---

## Step 6 — Keep-alive (free external cron)

Render’s own cron jobs may require a paid plan. Use a free external pinger:

1. [cron-job.org](https://cron-job.org) (free account).
2. Create job: **URL** = `https://YOUR-SERVICE.onrender.com/api/health`, **every 12 minutes**, method GET.
3. Save.

This keeps the app and Neon warmer; first click after long idle may still be slower than paid hosting.

---

## Step 7 — When AWS is ready

1. Add `AWS_S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` in Render.
2. Set `ENVIRONMENT=production` (enforces strong secrets + AWS in `startup.py`).
3. Redeploy.

---

## Troubleshooting

| Problem | Fix |
|--------|-----|
| Build fails | Pin **Python 3.12.7** (`PYTHON_VERSION` in Render, plus root `runtime.txt`). Default 3.14 breaks `pydantic-core` (Rust build). |
| `pydantic-core` / maturin / read-only filesystem | Same fix: set `PYTHON_VERSION=3.12.7`, clear build cache, redeploy. |
| 502 on first visit | Free tier waking up; wait and retry; add cron health ping |
| CORS / sign-in fails | `CORS_ORIGINS` must match exact browser origin (https + hostname) |
| “AWS required” on start | Set `ENVIRONMENT=development` until AWS vars are set |

---

## Other free hosts (same idea)

| Provider | GitHub deploy | Notes |
|----------|---------------|--------|
| **Render** | Native | Best match for this repo (`render.yaml`) |
| **Railway** | Native | Limited free credits; similar env vars |
| **Fly.io** | GitHub Actions or CLI | Small free allowance; more setup |

Recommendation: **Render free + Neon free + cron-job.org** for your current stack.
