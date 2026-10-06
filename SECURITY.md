# Security

## Secrets

- Never commit `.env` or AWS/Neon credentials.
- Use `.env.example` as a template only.
- Rotate `SECRET_KEY` and IAM keys if they are ever exposed.

## Production checklist

- Set `ENVIRONMENT=production`.
- Use a `SECRET_KEY` with at least 32 random characters.
- Serve the app behind HTTPS (required for secure session cookies).
- Set `CORS_ORIGINS` to your real site origin only (not `*`).
- Neon: use SSL (`sslmode=require` in `DATABASE_URL`).
- S3: block public access; rely on presigned URLs only.
- IAM policy: limit to `letters/*` on your bucket.

## Data handling

- Doctor profile, drafts, and letter metadata live in Neon PostgreSQL.
- Final letter PDFs live in S3 only.
- Full letter HTML is not stored after finalize.
- Audit log records actions, not letter bodies.

## Reporting issues

If you find a security problem, avoid opening a public issue with sensitive details. Contact the repository owner privately.
