# Agent context — Doctor Letter

Read this file before changing code. It defines **what the product is**, **how we build it**, and **what not to do**.

---

## Product in one paragraph

Doctors open a **mobile-friendly web app**, sign in with their **mobile number** (no password; optional SMS OTP only if `OTP_ENABLED=true`), pick from **letter templates** including a blank starter, edit in **self-hosted Quill**, **preview** a PDF, then **finalize** — storing a **PDF on AWS S3** and **metadata in Neon PostgreSQL**.

Patient-related content is sensitive. Treat it as health-adjacent data: minimize stored PHI, use secure sessions, and do not weaken auth or storage rules without explicit user approval.

---

## Fixed tech stack (do not replace)

| Layer | Choice |
|-------|--------|
| UI | HTML, CSS, vanilla JavaScript (multi-page, not React/Vue) |
| Editor | Quill 2 (`frontend/vendor/quill/`, `editor.html` only) |
| Optional SMS OTP | Off by default (`OTP_ENABLED=false`; Twilio if enabled) |
| API | Python **FastAPI** |
| ORM | SQLAlchemy 2 |
| Doctor data | **Neon PostgreSQL** (`DATABASE_URL`) |
| Letter PDF files | **AWS S3** only (presigned downloads) |
| PDF generation | xhtml2pdf (server-side HTML → PDF) |
| Sessions | Signed **httpOnly** cookie (`itsdangerous`) |

Do not introduce a second frontend framework, MongoDB, local PDF storage for production, or commit secrets.

---

## Storage rules (non-negotiable)

| Data | Where |
|------|--------|
| Mobile, doctor profile, drafts (HTML), letter index, audit events | **Neon** |
| Final letter PDFs | **S3** (`letters/{doctor_id}/{uuid}.pdf`) |
| Preview PDF | **Memory only** — not S3, not Neon |
| After finalize | **No full letter HTML** on `letters` row — PDF + summary fields only |

---

## Repository layout

```
backend/app/
  main.py              App factory, middleware, static mount
  config.py            pydantic-settings from .env
  models.py            Doctor, Letter, LetterDraft, AuditEvent, OtpVerification
  schemas.py           Pydantic request/response models
  startup.py           Production env validation
  database_migrate.py  Lightweight SQL migrations (Neon)
  routes/              Thin HTTP handlers
  services/            Business logic (pdf, s3, session, audit, templates)
  letter_templates/    Static HTML fragments with {{placeholders}}

frontend/
  *.html               One page per flow (index, dashboard, templates, editor, history, profile, privacy)
  css/main.css         Single stylesheet — prefer editing here for UI
  js/                  Small modules (see below)
  vendor/quill/        Self-hosted Quill assets

ops/health_ping.sh     Cron keep-alive for GET /api/health
SECURITY.md            Secrets and production checklist
README.md                Deploy, scaling, keep-alive
.env.example              Template only — never commit .env
```

---

## Backend conventions

- **Routes** parse input, call **services**, return **schemas**. No fat handlers.
- **Auth**: `get_current_doctor()` from cookie on protected routes.
- **Bundled reads** (performance): prefer existing combined endpoints instead of many round trips:
  - `GET /api/workspace` → profile + drafts
  - `GET /api/editor/{slug}` → template HTML + draft for that slug
- **Templates**: `template_loader.py` + files in `letter_templates/`; placeholders filled with doctor profile + today’s date.
- **S3**: `services/storage.py` — `build_s3_storage()`; finalize/delete must stay consistent (Neon row + S3 object).
- **Production**: `ENVIRONMENT=production` disables `/docs`, enforces AWS + strong `SECRET_KEY` (`startup.py`). Mobile-only sign-in uses rate limits + secure cookies.
- **Tests**: `backend/tests/` — run `pytest` from `backend/`; do not break existing tests when adding features.

---

## Frontend conventions

- **Same page structure**: keep separate HTML files; extract logic to `js/*-page.js` when a page grows.
- **Script order** (defer): caches → `http-client.js` → `api.js` → `session.js` → `ui.js` → page script.
- **Modules**:
  - `http-client.js` — fetch + error parsing
  - `profile-cache.js` / `workspace-cache.js` / `template-cache.js` — short TTL sessionStorage
  - `api.js` — all `/api/*` calls
  - `session.js` — `requireAuth()` (cache first, refresh session in background)
  - `ui.js` — alerts, dates, draft list rendering, `page-busy` state
- **Performance**: avoid extra `Api.me()` on every navigation; use caches and bundled endpoints. Debounce draft saves (~6s), do not spam audit on every draft PUT.
- **Responsive**: mobile-first in `main.css`; 16px inputs on small screens; full-width buttons where needed.

---

## UI / UX rules (user standards)

- **Humanized**: plain language, calm clinical tone — not marketing hype or “startup hero” copy.
- **Not AI-slop**: no purple gradients, glassmorphism stacks, generic “Welcome to your journey”, no emoji in UI or code comments.
- **Attractive but restrained**: warm paper tones, clear typography, subtle borders/accent — see `main.css` variables.
- **Do not restructure** the app into a SPA or redesign information architecture unless the user explicitly asks.
- **Accessibility**: labels on fields, `aria-live` on alerts, sensible focus states.

---

## Coding rules (user standards)

- **Modular and readable**: small files, clear names, one responsibility per service module.
- **Minimal diffs**: fix the task; do not refactor unrelated code or add speculative features.
- **No clutter**: no debug prints, no commented-out blocks, no unnecessary CLI scripts in repo unless requested.
- **Secrets**: never hardcode keys; never commit `.env`.
- **Git**: commit only when the user asks; do not force-push `main`.

---

## Core user flows (reference)

1. **index.html** — POST `/api/session` (mobile + honeypot) → cookie → dashboard  
2. **profile.html** — PUT `/api/profile` → Neon  
3. **templates.html** — blank letter + grouped templates → **same** `editor.html` (Quill)  
4. **editor.html** — GET `/api/editor/{slug}` → rich text → autosave PUT `/api/drafts`  
5. **Preview** — POST `/api/letters/preview` (base64 PDF, no storage)  
6. **Finalize** — POST `/api/letters/finalize` → S3 + Neon `letters`, delete draft  
7. **history.html** — GET `/api/letters`, download presigned URL, DELETE removes Neon + S3  

---

## API quick reference

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/health` | No | DB ping (use for keep-alive cron) |
| POST | `/api/session` | No | Sign in with mobile (rate limited) |
| GET | `/api/session/me` | Yes | Profile from session |
| POST | `/api/session/logout` | No | Clear cookie |
| GET | `/api/workspace` | Yes | Profile + drafts (dashboard) |
| GET | `/api/editor/{slug}` | Yes | Template + draft (editor) |
| GET/PUT | `/api/profile` | Yes | Read/update doctor fields |
| GET | `/api/templates` | No | List letter templates (each opens in rich text editor) |
| GET | `/api/templates/{slug}` | Yes | Template HTML + profile placeholders |
| PUT | `/api/drafts` | Yes | Upsert draft |
| GET | `/api/drafts/by-template/{slug}` | Yes | Single draft (legacy; editor uses bundled route) |
| POST | `/api/letters/preview` | Yes | PDF base64 |
| POST | `/api/letters/finalize` | Yes | PDF → S3, row → Neon |
| GET | `/api/letters` | Yes | History |
| GET | `/api/letters/{id}/download` | Yes | Presigned S3 URL |
| DELETE | `/api/letters/{id}` | Yes | Delete Neon + S3 |

Static UI is served from `frontend/` at `/` (FastAPI `StaticFiles`, `html=True`).

---

## Data model (Neon)

| Table | Key fields |
|-------|------------|
| `doctors` | `mobile` (unique), profile fields, timestamps |
| `letter_drafts` | `doctor_id`, `template_slug` (**unique pair**), `html_content`, `patient_name` |
| `letters` | `doctor_id`, `template_*`, `patient_name`, `storage_key` (S3 key) |
| `audit_events` | `action`, optional `letter_id`, no letter body |
| `otp_verifications` | Hashed codes, expiry, rate limits (no plaintext OTP at rest) |

---

## Environment variables

See `.env.example`. Required: `DATABASE_URL`, `SECRET_KEY`. Production: AWS, pooled Neon URL, `CORS_ORIGINS`, HTTPS. Keep `OTP_ENABLED=false` unless SMS OTP is intentionally enabled.

---

## Known gaps (do not “fix” silently)

- **Neon latency / cold start** — pooling, bundled APIs, optional `/api/health` cron; not eliminable on free tiers alone.  
- **PDF CPU** — preview/finalize are server-heavy at scale; consider job queue later.  
- **Audit retention** — no auto-purge yet.  
- **Rate limits** — in-memory per process; shared store if you run many workers and need global limits.  

See `README.md` for production capacity (~4k–5k concurrent users needs horizontal scale + paid Neon).

---

## When implementing a new feature

1. Confirm it fits **mobile → template → edit → preview → S3 finalize → history** scope.  
2. Decide **Neon vs S3 vs neither** for any new data.  
3. Prefer **one API call** per screen load where possible.  
4. Update **schemas + routes + services** together; add a **pytest** if behavior is critical.  
5. Match **existing CSS/JS patterns**; update this file only if architecture or rules change.

---

## Local commands

```powershell
cd backend
.\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\pytest -q
```

App URL: http://127.0.0.1:8000
