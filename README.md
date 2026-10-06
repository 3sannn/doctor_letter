# Doctor Letter

Doctors sign in with a mobile number, edit letter templates in a rich text editor, and save finalized PDFs to AWS S3. Profile, drafts, and history metadata are stored in Neon PostgreSQL.

## Repository layout

```
doctor_letter/
├── backend/
│   ├── app/
│   │   ├── routes/          HTTP API (session, profile, templates, drafts, letters)
│   │   ├── services/        Business logic (PDF, S3, sessions, audit)
│   │   ├── letter_templates/  HTML starting points for each letter type
│   │   ├── models.py        Database tables
│   │   ├── config.py        Environment settings
│   │   └── main.py          Application entry
│   ├── tests/               Automated tests
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/                Static HTML, CSS, JavaScript UI
├── .env.example             Copy to .env (never commit .env)
├── SECURITY.md
└── README.md
```

## Requirements

- Python 3.11+
- Neon PostgreSQL (`DATABASE_URL`)
- AWS S3 bucket and IAM credentials (for final PDF save/download)
- Optional: AWS S3 can be added later; preview and drafts work without it

## Local setup

1. Copy `.env.example` to `.env` and fill in Neon and AWS values.
2. Create a virtual environment in `backend` and install dependencies:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\pip install -r requirements.txt
   ```

3. Run the server:

   ```powershell
   .\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

4. Open http://127.0.0.1:8000

API docs (development only): http://127.0.0.1:8000/docs

## Tests

```powershell
cd backend
.\.venv\Scripts\pip install -r requirements-dev.txt
.\.venv\Scripts\pytest -q
```

Tests use your `.env` Neon connection. The S3 finalize test is skipped if `AWS_S3_BUCKET` is empty.

## Production

Set in `.env`:

- `ENVIRONMENT=production`
- Strong `SECRET_KEY` (32+ characters)
- `CORS_ORIGINS=https://your-domain.com`
- Valid Neon and AWS credentials

Deploy behind HTTPS (nginx, Caddy, or a platform with TLS). OpenAPI docs are disabled in production.

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

Do not push `.env`, `.venv`, local `.db` files, or PDF artifacts. They are listed in `.gitignore`.
