import hashlib

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import AuditEvent


def _client_fingerprint(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:12]


def record_audit(
    db: Session,
    doctor_id: str,
    action: str,
    request: Request,
    letter_id: str = "",
    detail: str = "",
) -> None:
    event = AuditEvent(
        doctor_id=doctor_id,
        action=action,
        letter_id=letter_id,
        detail=detail or _client_fingerprint(request),
    )
    db.add(event)
    db.commit()
