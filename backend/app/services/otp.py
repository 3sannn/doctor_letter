import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import OtpVerification
from app.services.sms import SmsDeliveryError, send_login_code


def _hash_code(settings: Settings, mobile: str, code: str) -> str:
    payload = f"{mobile}:{code}".encode("utf-8")
    key = settings.secret_key.encode("utf-8")
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def normalize_mobile_e164(mobile_digits: str, country_code: str) -> str:
    digits = mobile_digits
    cc = country_code.lstrip("+")
    if digits.startswith(cc) and len(digits) > 10:
        return f"+{digits}"
    if len(digits) == 10:
        return f"+{cc}{digits}"
    return f"+{digits}"


def _recent_request_count(db: Session, mobile: str, since: datetime) -> int:
    return (
        db.query(OtpVerification)
        .filter(OtpVerification.mobile == mobile, OtpVerification.created_at >= since)
        .count()
    )


def _latest_otp(db: Session, mobile: str) -> OtpVerification | None:
    return (
        db.query(OtpVerification)
        .filter(OtpVerification.mobile == mobile)
        .order_by(OtpVerification.created_at.desc())
        .first()
    )


def request_otp(db: Session, settings: Settings, mobile: str) -> dict:
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    if _recent_request_count(db, mobile, hour_ago) >= settings.otp_max_requests_per_hour:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many code requests. Try again later.",
        )

    latest = _latest_otp(db, mobile)
    if latest and (now - latest.created_at).total_seconds() < settings.otp_resend_cooldown_seconds:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Wait a moment before requesting another code.",
        )

    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = now + timedelta(minutes=settings.otp_ttl_minutes)
    row = OtpVerification(
        mobile=mobile,
        code_hash=_hash_code(settings, mobile, code),
        expires_at=expires_at,
    )
    db.add(row)
    db.commit()

    mobile_e164 = normalize_mobile_e164(mobile, settings.sms_default_country_code)
    try:
        send_login_code(settings, mobile_e164, code)
    except SmsDeliveryError as exc:
        db.delete(row)
        db.commit()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    response = {"message": "Verification code sent.", "expires_in_minutes": settings.otp_ttl_minutes}
    if settings.otp_dev_mode and not settings.is_production:
        response["dev_code"] = code
    return response


def verify_otp(db: Session, settings: Settings, mobile: str, code: str) -> None:
    row = _latest_otp(db, mobile)
    if not row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request a new code first.")

    if datetime.utcnow() > row.expires_at:
        db.delete(row)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code expired. Request a new one.")

    row.attempts += 1
    if row.attempts > settings.otp_max_attempts:
        db.delete(row)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many attempts. Request a new code.")

    expected = _hash_code(settings, mobile, code.strip())
    if not hmac.compare_digest(expected, row.code_hash):
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect code.")

    db.query(OtpVerification).filter(OtpVerification.mobile == mobile).delete()
    db.commit()
