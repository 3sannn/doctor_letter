from fastapi import HTTPException, Request, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import Doctor


class SessionService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.serializer = URLSafeTimedSerializer(settings.secret_key, salt="doctor-letter-session")
        self.max_age_seconds = settings.session_max_age_hours * 3600

    def issue_token(self, doctor_id: str) -> str:
        return self.serializer.dumps({"doctor_id": doctor_id})

    def read_doctor_id(self, token: str) -> str:
        try:
            payload = self.serializer.loads(token, max_age=self.max_age_seconds)
        except SignatureExpired as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired.") from exc
        except BadSignature as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session.") from exc
        doctor_id = payload.get("doctor_id")
        if not doctor_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session.")
        return doctor_id


def get_session_service() -> SessionService:
    return SessionService(get_settings())


def get_or_create_doctor(db: Session, mobile: str) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.mobile == mobile).one_or_none()
    if doctor:
        return doctor
    doctor = Doctor(mobile=mobile)
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def get_current_doctor(
    request: Request,
    db: Session,
    session_service: SessionService,
) -> Doctor:
    token = request.cookies.get(session_service.settings.session_cookie_name)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in with your mobile number.")
    doctor_id = session_service.read_doctor_id(token)
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).one_or_none()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session no longer valid.")
    return doctor


def set_session_cookie(response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_max_age_hours * 3600,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.is_production,
        samesite="lax",
    )
